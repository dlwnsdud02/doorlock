import datetime
import state

def add(msg: str):
    """시스템 로그 추가"""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{now}] {msg}"
    print(line)
    if not state.logs or state.logs[-1] != line:
        state.logs.append(line)