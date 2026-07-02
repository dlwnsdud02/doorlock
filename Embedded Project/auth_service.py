import cv2
import config
import state

# face_recognition 로딩 시도
try:
    import face_recognition
    FACE_LIB_AVAILABLE = True
except ImportError:
    FACE_LIB_AVAILABLE = False

def match_reference(face_bgr, class_name_now=None):
    """참조 데이터와 현재 얼굴 비교"""
    # 1. 참조 데이터 없음
    if state.reference_class is None and state.reference_encoding is None:
        return False, "참조 없음"

    # 2. 정밀 비교 (Embedding)
    if FACE_LIB_AVAILABLE and state.reference_encoding is not None:
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        encs = face_recognition.face_encodings(rgb)
        if not encs:
            return False, "특징 추출 실패"
        
        dist = face_recognition.face_distance([state.reference_encoding], encs[0])[0]
        ok = dist <= config.FACE_DISTANCE_THRESHOLD
        return ok, f"dist={dist:.3f}"
    
    # 3. 단순 비교 (Class Name)
    else:
        if state.reference_class is None:
            return False, "참조 클래스 없음"
        ok = (class_name_now == state.reference_class)
        return ok, f"class={class_name_now}"