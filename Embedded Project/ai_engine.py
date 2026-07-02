import sys
from ultralytics import YOLO
import config
import logger

class YoloEngine:
    def __init__(self):
        self.model = self._load_model()

    def _load_model(self):
        logger.add(f"엔진 초기화: {config.YOLO_MODEL_PATH}")
        try:
            model = YOLO(config.YOLO_MODEL_PATH)
            logger.add("✅ YOLO 모델 로드 완료")
            return model
        except Exception as e:
            logger.add(f"❌ 모델 로드 실패: {e}")
            sys.exit(1)

    def detect(self, frame):
        """프레임에서 객체 감지"""
        return self.model.predict(
            frame, 
            conf=config.DETECT_MIN_CONF, 
            verbose=False, 
            imgsz=config.MODEL_IMGSZ, 
            max_det=config.MAX_DET
        )