# server.py

from flask import Flask, send_file, jsonify
import websocket
import uuid
import json
import urllib.request
import urllib.parse
import random
import io
from PIL import Image

# 서버 설정
server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())
app = Flask(__name__)

# ComfyUI API
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"http://{server_address}/view?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://{server_address}/history/{prompt_id}") as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images

# Flask 엔드포인트
@app.route('/generate', methods=['GET'])
def generate_image():
    try:
        # 워크플로우 로드
        with open("workflow_api.json", "r", encoding="utf-8") as f:
            workflow_data = f.read()
        workflow = json.loads(workflow_data)

        # 랜덤 시드 설정
        seednum = random.randint(1, 99999999999)
        workflow["3"]["inputs"]["seed"] = seednum

        # 이미지 생성 요청
        ws = websocket.WebSocket()
        ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
        images = get_images(ws, workflow)
        ws.close()

        # 이미지 응답 반환
        for node_id in images:
            if images[node_id]:
                image_data = images[node_id][0]
                return send_file(
                    io.BytesIO(image_data),
                    mimetype="image/png",
                    as_attachment=False,
                    download_name="generated.png"
                )

        return jsonify({"error": "이미지를 생성하지 못했습니다."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
