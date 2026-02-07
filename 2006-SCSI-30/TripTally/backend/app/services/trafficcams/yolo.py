# app/yolo_onnx.py
import os, time
import numpy as np
from ultralytics import YOLO as UltralyticsYOLO
import cv2

# Classes we keep (COCO-style IDs used by Ultralytics)
# 0=person, 1=bicycle, 2=car, 3=motorcycle, 5=bus, 7=truck
VEHICLE_CLASS_IDS = {1, 2, 3, 5, 7}  # (bicycle optional; remove 1 if you don't want it)

DEBUG_YOLO = os.getenv("DEBUG_YOLO", "0") == "1"

def pick_img_size(w, h):
    """Adaptive image size (multiple of 32). You can ignore and stick to fixed 640 if you prefer."""
    s = max(w, h)
    if s >= 1280: return 768
    if s >= 720:  return 640
    if s >= 480:  return 512
    return 416

class YOLO:
    def __init__(self, path, img_size=640, conf=0.25, iou=0.45, class_ids=VEHICLE_CLASS_IDS):
        self.img_size = int(img_size)
        self.conf = float(conf)
        self.iou = float(iou)
        self.class_ids = set(class_ids)
        
        # Load the YOLO model
        self.model = UltralyticsYOLO(path)

    def infer(self, bgr, override_size=None):
        """
        Input:  BGR uint8 image (H, W, 3)
        Output: boxes (N,4 in resized space), scores (N,), class_ids (N,), (r, dw, dh)
        """
        t0 = time.perf_counter()
        target = int(override_size) if override_size else self.img_size
        
        # YOLO handles preprocessing internally, so we just need to pass the image
        orig_h, orig_w = bgr.shape[:2]
        
        t_pre = (time.perf_counter() - t0) * 1000
        t1 = time.perf_counter()
        
        # Run inference with ultralytics YOLO
        results = self.model.predict(
            bgr, 
            imgsz=target,
            conf=self.conf,
            iou=self.iou,
            classes=list(self.class_ids),
            verbose=False
        )[0]
        
        t_inf = (time.perf_counter() - t1) * 1000
        
        # Extract results
        boxes = results.boxes.xyxy.cpu().numpy() if len(results.boxes) > 0 else np.array([]).reshape(0, 4)
        scores = results.boxes.conf.cpu().numpy() if len(results.boxes) > 0 else np.array([])
        class_ids = results.boxes.cls.cpu().numpy().astype(int) if len(results.boxes) > 0 else np.array([])
        
        # Calculate scaling factors for compatibility with existing code
        # YOLO's results are already in original image coordinates
        r = 1.0  # No scaling needed as YOLO returns coords in original space
        dw, dh = 0.0, 0.0  # No padding offset
        
        if DEBUG_YOLO:
            print(f"[yolo] size={target} pre={t_pre:.1f}ms inf={t_inf:.1f}ms "
                  f"kept={len(boxes)} conf≥{self.conf}")
        
        return boxes, scores, class_ids, ((r, r), dw, dh)

    @staticmethod
    def to_native(boxes, orig_w, orig_h, r_tuple, dw, dh):
        """
        Map letterboxed coords back to original image pixel coords.
        boxes: (N,4) in letterboxed space (x1,y1,x2,y2)
        r_tuple: ((r_w, r_h), dw, dh) -> we pass as ((r_w, r_h), dw, dh)
        
        Note: With standard YOLO, boxes are already in native coordinates,
        but we keep this method for compatibility.
        """
        (r_w, r_h) = r_tuple[0] if isinstance(r_tuple[0], tuple) else r_tuple
        # When we letterbox to square, r_w == r_h typically.
        r = r_w
        # Undo padding, then scale back
        boxes[:, [0, 2]] -= dw
        boxes[:, [1, 3]] -= dh
        boxes[:, :4] /= r
        # Clip to image bounds
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, orig_w - 1)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, orig_h - 1)
        return boxes
