import time
import threading

def monotonic():
    return time.monotonic()

def bbox_area_ratio(x1, y1, x2, y2, frame_w, frame_h):
    """박스 면적 비율 계산"""
    bw = max(0, x2 - x1)
    bh = max(0, y2 - y1)
    return (bw * bh) / max(1, frame_w * frame_h)

def crop_face(frame, x1, y1, x2, y2, pad=0.15):
    """얼굴 이미지 크롭"""
    h, w = frame.shape[:2]
    bw = x2 - x1
    bh = y2 - y1
    px, py = int(bw * pad), int(bh * pad)
    nx1, ny1 = max(0, x1 - px), max(0, y1 - py)
    nx2, ny2 = min(w, x2 + px), min(h, y2 + py)
    return frame[ny1:ny2, nx1:nx2]

def run_async(func):
    """함수를 비동기(스레드)로 실행"""
    threading.Thread(target=func, daemon=True).start()