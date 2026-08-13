#!/usr/bin/env python3
"""Face detection shim: works on OpenCV 4 (Haar) and OpenCV 5 (YuNet DNN).

detect(img) -> list of (x, y, w, h) boxes, largest first. Empty list if no
face or if cv2 is unavailable (callers treat that as "skip / fallback").

YuNet needs a small onnx model (~230KB); it is auto-downloaded once into
pipeline/models/.
"""
import os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
YUNET_PATH = os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx")
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/"
             "face_detection_yunet/face_detection_yunet_2023mar.onnx")

_detector = None
_mode = None


def _ensure_yunet():
    if not os.path.exists(YUNET_PATH):
        os.makedirs(os.path.dirname(YUNET_PATH), exist_ok=True)
        print("downloading YuNet face model (one-time, ~230KB)")
        urllib.request.urlretrieve(YUNET_URL, YUNET_PATH)
    return YUNET_PATH


def available():
    try:
        import cv2  # noqa: F401
        return True
    except ImportError:
        return False


def detect(img):
    """img: BGR numpy array. Returns [(x, y, w, h), ...] largest-area first."""
    global _detector, _mode
    try:
        import cv2
    except ImportError:
        return []

    h, w = img.shape[:2]
    if _mode is None:
        if hasattr(cv2, "FaceDetectorYN"):
            _detector = cv2.FaceDetectorYN.create(_ensure_yunet(), "", (w, h),
                                                  0.7, 0.3, 5000)
            _mode = "yunet"
        elif hasattr(cv2, "CascadeClassifier"):
            _detector = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            _mode = "haar"
        else:
            _mode = "none"
    if _mode == "none":
        return []

    def _run(im):
        ih, iw = im.shape[:2]
        if _mode == "yunet":
            _detector.setInputSize((iw, ih))
            _, faces = _detector.detect(im)
            return [tuple(int(v) for v in f[:4])
                    for f in (faces if faces is not None else [])]
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        return [tuple(int(v) for v in f)
                for f in _detector.detectMultiScale(gray, 1.1, 5,
                                                    minSize=(iw // 10, iw // 10))]

    boxes = _run(img)
    # Very large faces (tight framing / zoom-to-fill) exceed the detectors'
    # relative size limits. Retry on downscaled copies and map boxes back.
    for scale in (0.5, 0.3):
        if boxes:
            break
        small = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))))
        boxes = [tuple(int(v / scale) for v in b) for b in _run(small)]
    return sorted(boxes, key=lambda b: -(b[2] * b[3]))
