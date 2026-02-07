import os, io, time
from pathlib import Path
from datetime import datetime, timezone
import requests, numpy as np, pandas as pd
from PIL import Image
import cv2

from TripTally.backend.app.services.trafficcams.yolo import YOLOOnnx

API_URL   = os.getenv("API_URL", "https://api.data.gov.sg/v1/transport/traffic-images")
X_API_KEY = os.getenv("X_API_KEY", "")
MODEL     = os.getenv("MODEL_PATH", "model.onnx")
OUT_DIR   = Path(os.getenv("OUT_DIR", "/opt/triptally/ci"))

CONF      = float(os.getenv("CONF_THRES", "0.25"))
IOU       = float(os.getenv("IOU_THRES", "0.45"))
IMGSZ     = int(os.getenv("IMG_SIZE", "640"))

# CI normalizers
K_COUNT   = int(os.getenv("K_COUNT", "20"))
K_AREA    = float(os.getenv("K_AREA", "0.10"))
K_MOTION  = float(os.getenv("K_MOTION", "8.0"))

# weights
W_DENS    = float(os.getenv("W_DENS", "0.6"))
W_AREA    = float(os.getenv("W_AREA", "0.4"))
W_MREL    = float(os.getenv("W_MREL", "0.3"))
W_CIRAW   = float(os.getenv("W_CIRAW", "0.7"))

# EWMA smoothing
ALPHA     = float(os.getenv("CI_ALPHA", "0.4"))  # new weight; prev is (1-ALPHA)

# Verbosity (ON by default). Set VERBOSE=0 to silence.
VERBOSE   = os.getenv("VERBOSE", "1") == "1"

CLASS_W = {
    "car": 1.0, "motorcycle": 0.5, "bus": 2.0, "truck": 2.0, "van": 1.2,
    2:1.0, 3:1.0, 5:2.0, 7:2.0, 1:0.5  # COCO fallbacks by id
}

def log(msg):
    if VERBOSE:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)

def fetch_cameras():
    t0 = time.perf_counter()
    headers = {"Accept":"application/json"}
    if X_API_KEY: headers["X-Api-Key"] = X_API_KEY
    r = requests.get(API_URL, headers=headers, timeout=60)
    r.raise_for_status()
    item = r.json()["items"][0]
    dt_ms = (time.perf_counter() - t0) * 1000
    log(f"API fetch OK in {dt_ms:.1f} ms")
    return item["timestamp"], item["cameras"]

def motion_score(cam_id, img_rgb):
    """Cheap inter-frame motion: keep a small cached prev frame per camera, diff at 320px width."""
    cache_dir = OUT_DIR / "cache" / "prev_frames"
    cache_dir.mkdir(parents=True, exist_ok=True)
    prev_p = cache_dir / f"{cam_id}.jpg"

    h, w = img_rgb.shape[:2]
    scale = 320.0 / max(1, w)
    small = cv2.resize(img_rgb, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)

    m = 0.0
    if prev_p.exists():
        prev = cv2.imdecode(np.fromfile(str(prev_p), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if prev is not None and prev.shape == gray.shape:
            diff = cv2.absdiff(gray, prev)
            m = float(np.median(diff)) / 255.0 * 10.0

    _, enc = cv2.imencode(".jpg", gray, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    enc.tofile(str(prev_p))
    return m

def clip01(x): return max(0.0, min(1.0, x))

def ci_from_features(veh_wcount, area_ratio, motion):
    veh_density  = clip01(veh_wcount / K_COUNT)
    area_density = clip01(area_ratio / K_AREA)
    CI_raw = W_DENS*veh_density + W_AREA*area_density
    motion_relief = 1.0 - clip01(motion / K_MOTION)
    CI = clip01(W_CIRAW*CI_raw + W_MREL*motion_relief)
    return CI, {"veh_density":veh_density, "area_density":area_density,
                "motion_relief":motion_relief, "CI_raw":CI_raw}



def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parquet_dir = OUT_DIR / "parquet"
    parquet_dir.mkdir(parents=True, exist_ok=True)

    log(f"Init: MODEL={MODEL} IMG_SIZE={IMGSZ} CONF={CONF} IOU={IOU}")
    sess = YOLOOnnx(MODEL, img_size=IMGSZ, conf=CONF, iou=IOU)

    # in-memory smoothing (reset each process run)
    ci_smooth = {}

    ts_iso, cams = fetch_cameras()
    ts = datetime.fromisoformat(ts_iso.replace("Z","+00:00")).astimezone(timezone.utc)
    log(f"Timestamp={ts_iso} cameras={len(cams)}")

    rows = []
    t_batch0 = time.perf_counter()
    img_ok = 0
    total_boxes = 0

    for c in cams:
        cam_id = str(c.get("camera_id"))
        lat = c.get("location",{}).get("latitude")
        lon = c.get("location",{}).get("longitude")
        md = c.get("image_metadata", {})
        w, h = int(md.get("width",0) or 0), int(md.get("height",0) or 0)

        try:
            t_dl0 = time.perf_counter()
            rb = requests.get(c["image"], timeout=60)
            rb.raise_for_status()
            im = Image.open(io.BytesIO(rb.content)).convert("RGB")
            rgb = np.array(im)
            t_dl = (time.perf_counter() - t_dl0) * 1000

            # detect
            bgr = rgb[:, :, ::-1]
            t_inf0 = time.perf_counter()
            boxes, scores, cids, (r,dw,dh) = sess.infer(bgr)
            boxes = sess.to_native(boxes.copy(), w, h, r, dw, dh)
            t_inf = (time.perf_counter() - t_inf0) * 1000

            veh_count, veh_wcount, area_sum = 0, 0.0, 0.0
            for (x1,y1,x2,y2), sc, cid in zip(boxes, scores, cids):
                veh_count += 1
                weight = CLASS_W.get(int(cid), CLASS_W.get(str(cid), 1.0))
                veh_wcount += float(weight)
                area_sum  += max(0.0, (x2-x1)) * max(0.0, (y2-y1))

            img_area = float(max(1, w*h))
            area_ratio = area_sum / img_area

            mot = motion_score(cam_id, rgb)

            CI, extras = ci_from_features(veh_wcount, area_ratio, mot)
            prev = ci_smooth.get(cam_id, CI)
            CI_s = (1.0-ALPHA)*prev + ALPHA*CI
            ci_smooth[cam_id] = CI_s

            rows.append({
                "ts": ts, "camera_id": cam_id, "lat": lat, "lon": lon,
                "img_w": w, "img_h": h,
                "veh_count": veh_count, "veh_wcount": veh_wcount,
                "area_ratio": area_ratio, "motion": mot,
                "CI": CI, "CI_smooth": CI_s
            })
            img_ok += 1
            total_boxes += veh_count
            log(f"cam={cam_id} {w}x{h} dl={t_dl:.1f}ms infer={t_inf:.1f}ms "
                f"boxes={veh_count} veh_w={veh_wcount:.1f} area={area_ratio:.3f} "
                f"motion={mot:.2f} CI={CI:.3f} CI_s={CI_s:.3f}")

        except Exception as e:
            rows.append({
                "ts": ts, "camera_id": cam_id, "lat": lat, "lon": lon,
                "img_w": w, "img_h": h,
                "veh_count": np.nan, "veh_wcount": np.nan,
                "area_ratio": np.nan, "motion": np.nan,
                "CI": np.nan, "CI_smooth": np.nan,
                "error": str(e)
            })
            log(f"cam={cam_id} ERROR: {e}")

    if not rows:
        log("[empty] no rows")
        return

    df = pd.DataFrame(rows)
    day = ts.strftime("%Y-%m-%d")
    outp = parquet_dir / f"dt={day}" / f"ci_{ts.strftime('%H%M%S')}.parquet"
    outp.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(outp, index=False)
    t_batch = (time.perf_counter() - t_batch0) * 1000

    log(f"WRITE {len(df)} rows → {outp}")
    log(f"SUMMARY: ok_imgs={img_ok}/{len(cams)} total_boxes={total_boxes} "
        f"mean_boxes/img={ (total_boxes/max(1,img_ok)) :.2f} total_time={t_batch:.0f}ms")

if __name__ == "__main__":
    main()
