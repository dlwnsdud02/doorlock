import threading
from collections import deque

# 전역 상태
frame_lock = threading.Lock()
frame_cond = threading.Condition(frame_lock)
output_frame = None
door_status = "LOCKED"
logs = deque(maxlen=50)

# 이벤트
stop_event = threading.Event()
capture_event = threading.Event()

# 인증 관련 상태
is_auth_active = False
auth_start_time = 0.0
door_open_until = 0.0

# 참조 데이터 메모리
reference_encoding = None
reference_class = None