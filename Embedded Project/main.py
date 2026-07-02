import threading
import time
import cv2
from flask import Flask, Response, jsonify, render_template, request

import config
import state
import logger
import tools
import core_system
import servo_lock as servo

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

def generate_frames():
    interval = 1.0 / config.STREAM_FPS
    while not state.stop_event.is_set():
        start = tools.monotonic()
        with state.frame_cond:
            if state.output_frame is None: state.frame_cond.wait(timeout=1.0)
            frame = state.output_frame
        if frame is None: continue
        
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ok:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + bytearray(encoded) + b"\r\n")
        
        elapsed = tools.monotonic() - start
        if elapsed < interval: time.sleep(interval - elapsed)

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/get_status")
def get_status():
    return jsonify({
        "status": state.door_status,
        "logs": list(state.logs),
        "auth_active": state.is_auth_active 
    })

@app.route('/request_auth')
def request_auth():
    if state.door_status == "OPEN":
        return jsonify({'result': 'already_open'})
    if state.is_auth_active:
         return jsonify({'result': 'busy'})

    state.is_auth_active = True
    state.auth_start_time = time.time()
    logger.add("🔍 인증 시작 (10초)")
    tools.run_async(servo.processing)
    return jsonify({'result': 'started'})

@app.route('/trigger_capture')
def trigger_capture():
    state.capture_event.set()
    return jsonify({'result':'ok'})

@app.route('/force_unlock')
def force_unlock():
    reason = request.args.get('reason', '비상 개방')
    if state.door_status == 'LOCKED':
        logger.add(f"🔓 강제 개방: {reason}")
        tools.run_async(servo.sound_success)
        servo.unlock_door()
        state.door_status = 'OPEN'
        return jsonify({'result':'unlocked'})
    else:
        return jsonify({'result':'already_open'})

if __name__ == "__main__":
    # 코어 시스템(감지 스레드) 시작
    t = threading.Thread(target=core_system.run, daemon=True)
    t.start()
    
    logger.add(">>> 웹 서버 실행")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    finally:
        state.stop_event.set()
        logger.add("🛑 시스템 종료")