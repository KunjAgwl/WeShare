import socket
import threading
import os
import logging
from flask import Flask, request, send_from_directory

logger = logging.getLogger(__name__)

class LocalFileServer:
    def __init__(self, upload_dir="uploads", port=5001):
        self.app = Flask(__name__)
        self.upload_dir = upload_dir
        self.port = port
        self.server_thread = None

        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/upload", methods=["POST"])
        def upload_file():
            if "file" not in request.files:
                return "No file part", 400
            file = request.files["file"]
            if file.filename == "":
                return "No selected file", 400
            
            save_path = os.path.join(self.upload_dir, file.filename)
            file.save(save_path)
            logger.info(f"File saved: {save_path}")
            return f"File {file.filename} uploaded successfully", 200

        @self.app.route("/download/<filename>", methods=["GET"])
        def download_file(filename):
            return send_from_directory(self.upload_dir, filename)

    def start(self):
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"File server started on port {self.port}")

    def _run_server(self):
        # Using simple flask run for now; in a real app would use a production server like waitress
        self.app.run(host="0.0.0.0", port=self.port, debug=False, use_reloader=False)

    def get_ip(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
