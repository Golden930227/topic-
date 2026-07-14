from pathlib import Path
import socket
import subprocess
import sys
import time

from flask import Flask, jsonify
from flask_cors import CORS


BASE_DIR = Path(__file__).resolve().parent
STREAMLIT_FILE = BASE_DIR / "streamlist.py"

STREAMLIT_HOST = "127.0.0.1"
STREAMLIT_PORT = 8501
STREAMLIT_URL = "http://localhost:8501/?mode=readonly"

app = Flask(__name__)

# 允許 React localhost:5173 呼叫 API
CORS(app, origins=["http://localhost:5173"])

streamlit_process = None


def streamlit_is_running():
    try:
        with socket.create_connection(
            (STREAMLIT_HOST, STREAMLIT_PORT),
            timeout=1,
        ):
            return True
    except OSError:
        return False


@app.post("/api/open-cnn-monitor")
def open_cnn_monitor():
    global streamlit_process

    if not STREAMLIT_FILE.exists():
        return jsonify({
            "success": False,
            "message": f"找不到檔案：{STREAMLIT_FILE}",
        }), 404

    if not streamlit_is_running():
        streamlit_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(STREAMLIT_FILE),
                "--server.address",
                STREAMLIT_HOST,
                "--server.port",
                str(STREAMLIT_PORT),
                "--server.headless",
                "true",
            ],
            cwd=str(BASE_DIR),
        )

        for _ in range(30):
            if streamlit_is_running():
                break

            if streamlit_process.poll() is not None:
                return jsonify({
                    "success": False,
                    "message": "Streamlit 啟動失敗",
                }), 500

            time.sleep(0.5)

    if not streamlit_is_running():
        return jsonify({
            "success": False,
            "message": "等待 Streamlit 啟動逾時",
        }), 500

    return jsonify({
        "success": True,
        "url": STREAMLIT_URL,
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False,
    )