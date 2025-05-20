from flask import Flask, render_template, request, send_from_directory, jsonify, url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quixchatsecret'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app, cors_allowed_origins="*")

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

CHAT_LOG = []
BAD_WORDS = ['badword1', 'badword2']
NSFW_KEYWORDS = ['nsfw', '18+', 'explicit']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/history')
def chat_history():
    return jsonify(CHAT_LOG)

@socketio.on('message')
def handle_message(data):
    global CHAT_LOG
    if isinstance(data, dict):
        msg = data.get('msg', '')
        username = data.get('username', 'Anonymous')
    else:
        msg = str(data)
        username = "Anonymous"

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    nsfw_flag = any(word in msg.lower() for word in NSFW_KEYWORDS)
    for word in BAD_WORDS:
        msg = msg.replace(word, '*' * len(word))
    chat_data = {
        'username': username,
        'msg': msg,
        'timestamp': timestamp,
        'nsfw': nsfw_flag
    }
    CHAT_LOG.append(chat_data)
    emit('message', chat_data, broadcast=True)

@socketio.on('typing')
def handle_typing(username):
    emit('typing', username, broadcast=True, include_self=False)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'url': url_for('uploaded_file', filename=filename)})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
