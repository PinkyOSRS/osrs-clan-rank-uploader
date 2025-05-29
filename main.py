import os
import json
import base64
import logging
from flask import Flask, request, jsonify
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# GitHub config
GITHUB_TOKEN = os.environ.get("GITHUB_PAT")
GITHUB_REPO = "osrs-clan-rank-sync"
GITHUB_OWNER = "PinkyOSRS"

def trigger_process_clan_ranks():
    workflow_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/process-clan-ranks.yml/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "ref": "main"
    }

    r = requests.post(workflow_url, headers=headers, json=payload)
    logger.info(f"Triggered Process Clan Ranks: {r.status_code} {r.text}")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "Uploader is running. Use POST /clanrank"})

@app.route("/clanrank", methods=["POST"])
def upload_clanrank():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    try:
        data = request.get_json()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"clanrank_{timestamp}.json"
        file_path = f"uploads/{filename}"

        encoded_content = base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8")
        commit_message = f"Upload clanrank data {filename}"

        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{file_path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        payload = {
            "message": commit_message,
            "content": encoded_content,
            "branch": "main"
        }

        logger.info(f"Uploading to: {url}")
        r = requests.put(url, headers=headers, json=payload)
        logger.info(f"GitHub response: {r.status_code} - {r.text}")

        if r.status_code in [200, 201]:
            # ✅ Trigger the workflow after successful upload
            trigger_process_clan_ranks()
            return jsonify({"status": "success", "filename": filename})
        else:
            return jsonify({"error": "GitHub API error", "details": r.text}), 500

    except Exception as e:
        logger.exception("An error occurred during upload")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

