from typing import Mapping, Any

import os
import requests
import datetime
import time

def run_checker(team_id: str, challenge_slug: str, app_file_basedir: str, service_secret: str, current_flag: str) -> Mapping[str, Any]:
    with open(os.path.join(app_file_basedir, "/var/www/html/index.php")) as f:
        file_content = f.read()
        header_start = "// BEGIN-NOCHANGE\n"
        header_end = "// END-NOCHANGE"
        nochange_content = file_content[file_content.find(header_start)+len(header_start):file_content.find(header_end)]
    
    compare_code = """if (md5($_GET["password"]) === "a035574b2aa4ae89e5676dc555675311") {
    echo $_GET["cmd"];
}"""    
    if compare_code != nochange_content:
        return {
            "status": "failed",
            "is_code_valid": False,
            "last_checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    
    return {
        "status": "ok",
        "is_code_valid": True,
        "last_checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
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
        try:
            requests.post(
                report_url,
                json={"challenge_slug": challenge_slug, "team_id": team_id, "report": checker_result},
                headers={'X-CHECKER-SECRET': checker_secret},
                timeout=1
            )
        except Exception as e:
            print(e)
        
        time.sleep(checker_interval)

if __name__ == "__main__":
    main()