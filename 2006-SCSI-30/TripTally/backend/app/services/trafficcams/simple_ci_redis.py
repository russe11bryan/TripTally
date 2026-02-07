"""
Simple CI with Redis Integration and Forecasting
Runs continuously, updating CI and forecasts every 2 minutes
"""

import os, io, time, math
from pathlib import Path
from datetime import datetime, timezone
import requests, numpy as np, pandas as pd
from PIL import Image
import cv2
import redis
from collections import deque

from yolo import YOLO

# API Configuration
API_URL   = os.getenv("API_URL", "https://api.data.gov.sg/v1/transport/traffic-images")
X_API_KEY = os.getenv("X_API_KEY", "")
MODEL     = os.getenv("MODEL_PATH", "models/yolov8n.pt")
CACHE_DIR = Path(os.getenv("CACHE_DIR", "./cache"))

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB   = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Model Configuration
CONF      = float(os.getenv("CONF_THRES", "0.25"))
IOU       = float(os.getenv("IOU_THRES", "0.45"))
IMGSZ     = int(os.getenv("IMG_SIZE", "640"))

# CI normalizers
K_COUNT   = int(os.getenv("K_COUNT", "20"))
K_AREA    = float(os.getenv("K_AREA", "0.10"))
K_MOTION  = float(os.getenv("K_MOTION", "8.0"))

# Weights
W_DENS    = float(os.getenv("W_DENS", "0.6"))
W_AREA    = float(os.getenv("W_AREA", "0.4"))
W_MREL    = float(os.getenv("W_MREL", "0.3"))
W_CIRAW   = float(os.getenv("W_CIRAW", "0.7"))

# EWMA smoothing
ALPHA     = float(os.getenv("CI_ALPHA", "0.4"))

# Loop interval (seconds)
LOOP_INTERVAL = int(os.getenv("LOOP_INTERVAL", "120"))  # 2 minutes

# Verbosity
VERBOSE   = os.getenv("VERBOSE", "1") == "1"

# Model version
MODEL_VER = "simple_ci_v1"

CLASS_W = {
    "car": 1.0, "motorcycle": 0.5, "bus": 2.0, "truck": 2.0, "van": 1.2,
    2:1.0, 3:1.0, 5:2.0, 7:2.0, 1:0.5
}

# Historical CI storage for forecasting (per camera)
ci_history = {}  # camera_id -> deque of (ts, CI) tuples
MAX_HISTORY = 60  # Keep last 60 observations (~2 hours at 2-min intervals)


def log(msg):
    if VERBOSE:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)


def get_redis_client():
    """Get Redis client"""
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )


def fetch_cameras():
    """Fetch camera data from API"""
    t0 = time.perf_counter()
    headers = {"Accept":"application/json"}
    if X_API_KEY: 
        headers["X-Api-Key"] = X_API_KEY
    r = requests.get(API_URL, headers=headers, timeout=60)
    r.raise_for_status()
    item = r.json()["items"][0]
    dt_ms = (time.perf_counter() - t0) * 1000
    log(f"API fetch OK in {dt_ms:.1f} ms")
    return item["timestamp"], item["cameras"]


def motion_score(cam_id, img_rgb):
    """Calculate motion score using frame differencing"""
    cache_dir = CACHE_DIR / "prev_frames"
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


def clip01(x): 
    return max(0.0, min(1.0, x))


def ci_from_features(veh_wcount, area_ratio, motion):
    """Calculate CI from features"""
    veh_density  = clip01(veh_wcount / K_COUNT)
    area_density = clip01(area_ratio / K_AREA)
    CI_raw = W_DENS*veh_density + W_AREA*area_density
    motion_relief = 1.0 - clip01(motion / K_MOTION)
    CI = clip01(W_CIRAW*CI_raw + W_MREL*motion_relief)
    return CI


def temporal_features(ts):
    """Extract temporal features from timestamp"""
    minute_of_day = ts.hour * 60 + ts.minute
    hour = ts.hour
    day_of_week = ts.weekday()
    is_weekend = day_of_week >= 5
    
    # Cyclical encoding
    t_h = ts.hour + ts.minute / 60.0
    sin_t_h = math.sin(2 * math.pi * t_h / 24.0)
    cos_t_h = math.cos(2 * math.pi * t_h / 24.0)
    
    return minute_of_day, hour, day_of_week, is_weekend, sin_t_h, cos_t_h


def simple_forecast(camera_id, current_ci, ts):
    """
    Simple persistence-based forecasting with exponential decay
    Uses historical data to predict future CI values
    """
    # Get historical data for this camera
    if camera_id not in ci_history:
        ci_history[camera_id] = deque(maxlen=MAX_HISTORY)
    
    history = ci_history[camera_id]
    
    # Add current observation
    history.append((ts, current_ci))
    
    # Forecast horizons: 2, 4, 6, ..., 120 minutes
    horizons = list(range(2, 121, 2))
    forecasts = []
    
    if len(history) < 2:
        # Not enough history, use persistence (current value)
        forecasts = [current_ci] * len(horizons)
    else:
        # Simple exponential decay model
        # Assumes CI tends to revert to mean over time
        recent_cis = [ci for _, ci in list(history)[-30:]]  # Last 30 observations
        mean_ci = np.mean(recent_cis)
        
        # Calculate trend (if any)
        recent_10 = [ci for _, ci in list(history)[-10:]]
        trend = 0.0
        if len(recent_10) >= 2:
            trend = (recent_10[-1] - recent_10[0]) / len(recent_10)
        
        for h in horizons:
            # Decay factor: stronger decay for longer horizons
            decay = math.exp(-h / 60.0)  # 60-minute half-life
            
            # Forecast = current + trend * horizon + decay to mean
            forecast_ci = current_ci + trend * h + (1 - decay) * (mean_ci - current_ci)
            forecast_ci = clip01(forecast_ci)
            forecasts.append(forecast_ci)
    
    return horizons, forecasts


def save_to_redis(r, camera_id, ts, lat, lon, img_w, img_h, veh_count, 
                  veh_wcount, area_ratio, motion, CI, temporal_feats):
    """Save current state to Redis ci:now:<camera_id>"""
    minute_of_day, hour, day_of_week, is_weekend, sin_t_h, cos_t_h = temporal_feats
    
    key = f"ci:now:{camera_id}"
    data = {
        "ts": ts.isoformat(),
        "camera_id": camera_id,
        "img_w": str(img_w),
        "img_h": str(img_h),
        "veh_count": str(int(veh_count)),
        "veh_wcount": str(veh_wcount),
        "area_ratio": str(area_ratio),
        "motion": str(motion),
        "CI": str(CI),
        "minute_of_day": str(minute_of_day),
        "hour": str(hour),
        "day_of_week": str(day_of_week),
        "is_weekend": str(is_weekend),
        "sin_t_h": str(sin_t_h),
        "cos_t_h": str(cos_t_h),
        "model_ver": MODEL_VER
    }
    
    # Save with 10-minute TTL
    r.hset(key, mapping=data)
    r.expire(key, 600)


def save_forecast_to_redis(r, camera_id, ts, horizons, forecasts):
    """Save forecast to Redis ci:fcst:<camera_id>"""
    key = f"ci:fcst:{camera_id}"
    data = {
        "ts": ts.isoformat(),
        "camera_id": camera_id,
        "model_ver": MODEL_VER
    }
    
    # Add horizon predictions
    for h, f in zip(horizons, forecasts):
        data[f"h:{h}"] = str(f)
    
    # Save with 10-minute TTL
    r.hset(key, mapping=data)
    r.expire(key, 600)


def save_camera_metadata(r, cameras):
    """Save camera metadata to Redis cameras:meta"""
    for cam in cameras:
        cam_id = str(cam.get("camera_id"))
        lat = cam.get("location", {}).get("latitude")
        lon = cam.get("location", {}).get("longitude")
        
        if lat and lon:
            data = {
                "camera_id": cam_id,
                "latitude": str(lat),
                "longitude": str(lon)
            }
            r.hset("cameras:meta", cam_id, str(data))


def process_cameras(sess, r):
    """Process all cameras: detect, compute CI, forecast, write to Redis"""
    ts_iso, cams = fetch_cameras()
    ts = datetime.fromisoformat(ts_iso.replace("Z","+00:00")).astimezone(timezone.utc)
    log(f"Timestamp={ts_iso} cameras={len(cams)}")
    
    # Save camera metadata
    save_camera_metadata(r, cams)
    
    img_ok = 0
    total_boxes = 0
    t_batch0 = time.perf_counter()
    
    for c in cams:
        cam_id = str(c.get("camera_id"))
        lat = c.get("location",{}).get("latitude")
        lon = c.get("location",{}).get("longitude")
        md = c.get("image_metadata", {})
        w, h = int(md.get("width",0) or 0), int(md.get("height",0) or 0)

        try:
            # Download image
            t_dl0 = time.perf_counter()
            rb = requests.get(c["image"], timeout=60)
            rb.raise_for_status()
            im = Image.open(io.BytesIO(rb.content)).convert("RGB")
            rgb = np.array(im)
            t_dl = (time.perf_counter() - t_dl0) * 1000

            # Detect vehicles
            bgr = rgb[:, :, ::-1]
            t_inf0 = time.perf_counter()
            boxes, scores, cids, (r_ratio, dw, dh) = sess.infer(bgr)
            boxes = sess.to_native(boxes.copy(), w, h, r_ratio, dw, dh)
            t_inf = (time.perf_counter() - t_inf0) * 1000

            # Calculate metrics
            veh_count, veh_wcount, area_sum = 0, 0.0, 0.0
            for (x1,y1,x2,y2), sc, cid in zip(boxes, scores, cids):
                veh_count += 1
                weight = CLASS_W.get(int(cid), CLASS_W.get(str(cid), 1.0))
                veh_wcount += float(weight)
                area_sum  += max(0.0, (x2-x1)) * max(0.0, (y2-y1))

            img_area = float(max(1, w*h))
            area_ratio = area_sum / img_area
            mot = motion_score(cam_id, rgb)
            
            # Calculate CI
            CI = ci_from_features(veh_wcount, area_ratio, mot)
            
            # Temporal features
            temp_feats = temporal_features(ts)
            
            # Save current state to Redis
            save_to_redis(r, cam_id, ts, lat, lon, w, h, veh_count, 
                         veh_wcount, area_ratio, mot, CI, temp_feats)
            
            # Generate and save forecast
            horizons, forecasts = simple_forecast(cam_id, CI, ts)
            save_forecast_to_redis(r, cam_id, ts, horizons, forecasts)
            
            img_ok += 1
            total_boxes += veh_count
            
            log(f"cam={cam_id} {w}x{h} dl={t_dl:.1f}ms infer={t_inf:.1f}ms "
                f"boxes={veh_count} veh_w={veh_wcount:.1f} area={area_ratio:.3f} "
                f"motion={mot:.2f} CI={CI:.3f}")

        except Exception as e:
            log(f"cam={cam_id} ERROR: {e}")
    
    t_batch = (time.perf_counter() - t_batch0) * 1000
    log(f"SUMMARY: ok_imgs={img_ok}/{len(cams)} total_boxes={total_boxes} "
        f"mean_boxes/img={total_boxes/max(1,img_ok):.2f} total_time={t_batch:.0f}ms")


def main():
    """Main loop: process cameras every LOOP_INTERVAL seconds"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    log(f"Init: MODEL={MODEL} IMG_SIZE={IMGSZ} CONF={CONF} IOU={IOU}")
    log(f"Redis: {REDIS_HOST}:{REDIS_PORT} DB={REDIS_DB}")
    log(f"Loop interval: {LOOP_INTERVAL}s")
    
    # Initialize YOLO
    sess = YOLO(MODEL, img_size=IMGSZ, conf=CONF, iou=IOU)
    
    # Initialize Redis
    r = get_redis_client()
    
    # Test Redis connection
    try:
        r.ping()
        log("Redis connection OK")
    except Exception as e:
        log(f"Redis connection FAILED: {e}")
        return
    
    # Main loop
    iteration = 0
    while True:
        iteration += 1
        log(f"=== Iteration {iteration} ===")
        
        try:
            process_cameras(sess, r)
        except Exception as e:
            log(f"ERROR in iteration {iteration}: {e}")
        
        log(f"Sleeping {LOOP_INTERVAL}s until next iteration...")
        time.sleep(LOOP_INTERVAL)


if __name__ == "__main__":
    main()
