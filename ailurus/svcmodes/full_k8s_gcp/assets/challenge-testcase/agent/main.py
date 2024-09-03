from typing import Mapping, Any

import os
import requests
import time

def run_checker(team_id: str, challenge_slug: str, app_file_basedir: str, service_secret: str, current_flag: str) -> Mapping[str, Any]:
    # TODO: Implement the agent checker here
    return {
        "status": "ok",
        "message": "Checker is running",
        "challenge_slug": challenge_slug,
        "team_id": team_id,
        "current_flag": current_flag,
        "last_checked_at": int(time.time())  # Unix timestamp in seconds
    }

def main():
    checker_interval = int(os.getenv("CHECKER_INTERVAL"))
    checker_secret = os.getenv("CHECKER_SECRET")
    app_file_basedir = os.getenv("APP_CONTAINER_FILESYSTEM")

    with open("/configmap/.service_secret") as svc_secret_file:
        service_secret = svc_secret_file.read().strip()

    challenge_slug = os.getenv("REPORT_CHALL_SLUG")
    team_id = os.getenv("REPORT_TEAM_ID")
    report_url = os.getenv("REPORT_API_ENDPOINT")

    while True:
        with open("/configmap/flag/flag.txt") as flag_file:
            current_flag = flag_file.read().strip()
        checker_result = run_checker(team_id, challenge_slug, app_file_basedir, service_secret, current_flag)
        requests.post(
            report_url,
            json={"challenge_slug": challenge_slug, "team_id": team_id, "report": checker_result},
            headers={'X-CHECKER-SECRET': checker_secret},
        )
        
        time.sleep(checker_interval)

if __name__ == "__main__":
    main()