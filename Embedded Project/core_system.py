import cv2
import time
import os
import random

import config
import state
import logger
import tools
import auth_service
import ai_engine
import servo_lock as servo

def run():
    # 1. 초기화
    try: servo.lock_door()
    except: pass
    
    if not os.path.exists(config.CAPTURE_DIR):
        os.makedirs(config.CAPTURE_DIR)

    engine = ai_engine.YoloEngine() # AI 엔진 시작
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    logger.add("📷 카메라 및 시스템 준비 완료")

    detect_interval = 1.0 / config.DETECT_FPS
    last_loop_t = tools.monotonic()

    # 2. 메인 루프
    while not state.stop_event.is_set():
        # FPS 제어
        now_t = tools.monotonic()
        dt = now_t - last_loop_t
        if dt < detect_interval: time.sleep(detect_interval - dt)
        last_loop_t = tools.monotonic()

        ret, frame = cap.read()
        if not ret:
            time.sleep(0.2); continue
        
        curr_time = time.time()
        display = frame.copy()

        # [기능 A] 자동 잠금
        if state.door_status == "OPEN" and curr_time > state.door_open_until:
            servo.lock_door()
            tools.run_async(servo.sound_click)
            state.door_status = "LOCKED"
            logger.add("🔒 자동 잠금")

        # [기능 B] 캡처
        if state.capture_event.is_set():
            state.capture_event.clear()
            fname = f"Image{random.randint(0, 9999999):07d}.jpg"
            cv2.imwrite(os.path.join(config.CAPTURE_DIR, fname), frame)
            logger.add(f"📸 저장: {fname}")

        # [기능 C] 인증 처리
        if state.is_auth_active:
            if curr_time - state.auth_start_time > config.AUTH_TIMEOUT:
                _handle_auth_timeout()
            else:
                _process_detection(engine, frame, display)

        # 프레임 업데이트
        with state.frame_cond:
            state.output_frame = display
            state.frame_cond.notify_all()

    cap.release()
    servo.cleanup()

def _handle_auth_timeout():
    logger.add("⏰ 시간 초과")
    state.is_auth_active = False
    tools.run_async(servo.sound_fail)
    servo.alarm_fail()

def _process_detection(engine, frame, display):
    results = engine.detect(frame)
    best_info = None

    for r in results:
        if r.boxes is None: continue
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            name = engine.model.names.get(cls_id, str(cls_id))
            area_r = tools.bbox_area_ratio(x1, y1, x2, y2, config.FRAME_WIDTH, config.FRAME_HEIGHT)

            # 그리기
            color = (0, 255, 0) if name in config.AUTHORIZED_USERS else (0, 0, 255)
            cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
            cv2.putText(display, f"{name} {conf*100:.0f}%", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

            if area_r >= config.MIN_FACE_AREA_RATIO:
                if best_info is None or area_r > best_info[-1]:
                    best_info = (x1, y1, x2, y2, conf, name, area_r)

    if best_info:
        _evaluate_candidate(frame, display, best_info)

def _evaluate_candidate(frame, display, info):
    x1, y1, x2, y2, conf, name, area = info
    
    if name not in config.AUTHORIZED_USERS:
        cv2.putText(display, "UNAUTHORIZED", (x1, y1-30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        return

    face = tools.crop_face(frame, x1, y1, x2, y2)
    
    # 참조 데이터 확인
    has_ref = (state.reference_encoding is not None) or (state.reference_class is not None)
    
    if has_ref:
        ok, reason = auth_service.match_reference(face, name)
        if ok and state.door_status == "LOCKED":
            _unlock(name, f"정밀: {reason}")
        elif not ok:
            cv2.putText(display, f"REJECT: {reason}", (x1, y1-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
    else:
        # 참조 데이터 없음 -> YOLO만 믿음
        if state.door_status == "LOCKED":
            _unlock(name, "YOLO단독")

def _unlock(name, method):
    logger.add(f"🔓 성공({method}): {name}")
    tools.run_async(servo.sound_success)
    servo.unlock_door()
    state.door_status = "OPEN"
    state.door_open_until = time.time() + config.DOOR_OPEN_SECONDS
    state.is_auth_active = False