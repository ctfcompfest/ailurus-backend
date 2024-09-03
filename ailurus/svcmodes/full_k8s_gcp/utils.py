from ailurus.utils.config import get_app_config, get_config

import logging
import os
import requests
import zipfile

log = logging.getLogger(__name__)

def init_challenge_asset(chall_id, chall_slug, asset_checksum=None, asset_type="artifact"):
    if asset_checksum == None: return None

    assetroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", f"{asset_type}s")
    asset_folder = os.path.join(assetroot_folder, f"{chall_slug}-{asset_checksum}")
    asset_zipfile = os.path.join(assetroot_folder, f"{chall_slug}-{asset_checksum}.zip")
    
    os.makedirs(assetroot_folder, exist_ok=True)
    if not os.path.exists(asset_folder):
        log.info(f"tc file not found.")

        link_download = get_app_config("WEBAPP_URL") + "/api/v2/worker/{}/{}/".format(asset_type, chall_id)
        log.debug(f"downloading tc file from {link_download}.")
        
        worker_secret = get_config("WORKER_SECRET")
        response = requests.get(link_download, headers={"X-WORKER-SECRET": worker_secret})
        log.debug(f"response from webapp: {response.status_code}.")
        
        with open(asset_zipfile, 'wb') as tczip:
            tczip.write(response.content)
    
        with zipfile.ZipFile(asset_zipfile, "r") as tczip_file:
            log.debug(f"extracting tc zipfile to {asset_folder}.")
            tczip_file.extractall(asset_folder)
    return asset_folder
