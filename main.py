import os
from pathlib import Path

from quart import Quart, request, send_file
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './files/'
ALLOWED_EXTENSIONS = {'tar'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return {'url': f"{request.environ['SERVER_NAME']}/download/{file.filename}"}

@app.route('/download/{shard_id}', methods=['GET'])
def download_file(shard_id: int):
    file_path = Path(os.path.join(app.config['UPLOAD_FOLDER'], f"{shard_id}.tar"))
    if not file_path.exists():
        return 'Invalid file ID', 404
    return send_file(str(file_path.absolute()), mimetype="application/x-tar")
    
@app.route('/delete/{shard_id}', methods=['DELETE'])
def delete_file(shard_id: int):
    file_path = Path(os.path.join(app.config['UPLOAD_FOLDER'], f"{shard_id}.tar"))
    if not file_path.exists():
        return 'Invalid file ID', 404

app.run("0.0.0.0", 80)
