from ailurus.utils.config import get_app_config, get_config

import logging
import os
import requests
import zipfile

log = logging.getLogger(__name__)

def init_challenge_asset(chall_id, asset_checksum=None, asset_type="artifact"):
    if asset_checksum == None: return None

    assetroot_folder = os.path.join(get_app_config("DATA_DIR"), "..", "worker_data", f"{asset_type}s")
    asset_folder = os.path.join(assetroot_folder, f"{chall_id}-{asset_checksum}")
    asset_zipfile = os.path.join(assetroot_folder, f"{chall_id}-{asset_checksum}.zip")
    
    os.makedirs(assetroot_folder, exist_ok=True)
    if not os.path.exists(asset_folder):
        log.info(f"{asset_type} file not found, will download the file.")

        link_download = get_app_config("WEBAPP_URL") + "/api/v2/worker/{}/{}/".format(asset_type, chall_id)
        log.debug(f"downloading {asset_type} file from {link_download}.")
        
        worker_secret = get_config("WORKER_SECRET")
        response = requests.get(link_download, headers={"X-WORKER-SECRET": worker_secret})
        log.debug(f"response from webapp: {response.status_code}.")
        
        with open(asset_zipfile, 'wb') as asset_type_zip:
            asset_type_zip.write(response.content)
    
        with zipfile.ZipFile(asset_zipfile, "r") as asset_type_zip_file:
            log.debug(f"extracting {asset_type} zipfile to {asset_folder}.")
            asset_type_zip_file.extractall(asset_folder)
    return asset_folder