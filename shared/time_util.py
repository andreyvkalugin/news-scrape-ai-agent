from datetime import datetime, timezone

def get_now() -> int:
    now_utc = datetime.now(timezone.utc)
    timestamp_utc = int(now_utc.timestamp())
    return timestamp_utc