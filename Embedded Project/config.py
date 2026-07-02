import os

# 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "yolov8n-facebest.pt")
CAPTURE_DIR = os.path.join(BASE_DIR, "Capture")
REFERENCE_IMG_PATH = os.path.join(BASE_DIR, "reference.jpg")

# 사용자 및 보안
AUTHORIZED_USERS = ["HJH", "KTJ", "LJY", "HKM"]
CONFIDENCE_THRESHOLD = 0.50
DETECT_MIN_CONF = 0.40
MIN_FACE_AREA_RATIO = 0.01
AUTH_TIMEOUT = 10.0
DOOR_OPEN_SECONDS = 3.0
FACE_DISTANCE_THRESHOLD = 0.65

# 카메라/성능
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MODEL_IMGSZ = 640
MAX_DET = 10
DETECT_FPS = 15
STREAM_FPS = 12