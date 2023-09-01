from datetime import timedelta

CHECKER_INTERVAL = timedelta(seconds=60)
CHECKER_TIMEOUT = timedelta(seconds=CHECKER_INTERVAL.total_seconds() // 3)