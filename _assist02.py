from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import openai
import json
import os
from werkzeug.utils import secure_filename
import logging

# Load OpenAI API Key
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    openai.api_key = config['openai_api_key']

# Initialize Flask and SocketIO
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Assistant ID - replace with your own
assistant_id = 'asst_SFJ785rxK4BFeVaWhDPTs7Yb'

# Directory for storing uploaded files
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('chat2.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Process the file here (e.g., read text, OCR, etc.)
        # For now, just returning the file path
        return jsonify({'file_path': file_path})
    return jsonify({'error': 'File type not allowed'})

@socketio.on('connect')
def handle_connect():
    logging.info('Socket.IO connected')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Socket.IO disconnected')

def handle_message(data):
    message_text = data.get('message')
    file_path = data.get('file_path')

    # Process the message or file
    # For now, let's just echo back the received message
    response = f"Received your message: {message_text}"
    if file_path:
        response += f" and file at {file_path}"

    socketio.emit('response', {'response': response})

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    socketio.run(app, debug=True)
