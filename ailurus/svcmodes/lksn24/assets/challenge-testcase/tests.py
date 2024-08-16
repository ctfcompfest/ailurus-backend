import datetime
import random
import time

def run_testcase():
    start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rand_val = random.randint(5, 15)
    time.sleep(rand_val)
    end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return (
        True,
        {
            "start_time": start_time,
            "end_time": end_time,
            "duration": rand_val,
            "message": "please refer to documentation"
        }
    )