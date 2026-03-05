import requests
import os
import logging

logger = logging.getLogger(__name__)

class LocalClient:
    def __init__(self):
        pass

    def send_file(self, ip, port, file_path):
        url = f"http://{ip}:{port}/upload"
        try:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                files = {"file": (filename, f)}
                response = requests.post(url, files=files)
                
            if response.status_code == 200:
                logger.info(f"File sent successfully to {ip}:{port}")
                return True
            else:
                logger.error(f"Failed to send file: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            return False

    def download_file(self, ip, port, filename, save_dir):
        url = f"http://{ip}:{port}/download/{filename}"
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                save_path = os.path.join(save_dir, filename)
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"File downloaded successfully to {save_path}")
                return True
            else:
                logger.error(f"Failed to download file: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False
