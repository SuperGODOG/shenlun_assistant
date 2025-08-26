# app.py

from flask import Flask, request, jsonify
from services import get_llm_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint that returns a welcome message.
    """
    return jsonify({
        'message': '欢迎使用申论评分系统API',
        'endpoints': {
            '/api/chat': 'POST - 发送提示词获取LLM回复'
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint to interact with the LLM.
    Expects a JSON payload with a "prompt" key and optional "format" key.
    """
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Invalid input, "prompt" key is required.'}), 400

    prompt = data['prompt']
    format_type = data.get('format', 'text')  # 默认使用text格式
    
    response = get_llm_response(prompt, format_type)

    if isinstance(response, dict) and 'error' in response:
        return jsonify(response), 500

    return jsonify({
        'response': response,
        'format': format_type,
        'content_type': 'text/markdown' if format_type == 'markdown' else 'text/plain'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)