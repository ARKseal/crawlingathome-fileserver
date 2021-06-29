import os
from pathlib import Path

from quart import Quart, request, Response
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './files/'
ALLOWED_EXTENSIONS = {'tar'}

app = Quart(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 # 1 gb
app.config['BODY_TIMEOUT'] = 60 * 60 # 1 hour
app.config['CHUNK_SIZE'] = 8192

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['POST'])
async def upload_file():
    files = await request.files
    file = files.get('file')
    file_paths = [ \
            Path( os.path.join(app.config['UPLOAD_FOLDER'], \
                f"{file.filename.split('.')[0]}.{extension}")) \
            for extension in app.config['ALLOWED_EXTENSIONS'] ]

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return 'No selected file', 400

    if not allowed_file(file.filename):
        return 'Invalid file', 422

    if any([path.exists() for path in file_paths]):
        return 'File already exists', 409

    if file:
        filename = secure_filename(file.filename)
        await file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return {'url': f"/download/{filename}"}

@app.route('/download/<shard_id>', methods=['GET'])
async def download_file(shard_id):
    file_paths = [ \
            Path( os.path.join(app.config['UPLOAD_FOLDER'], \
                f"{shard_id}.{extension}")) \
            for extension in app.config['ALLOWED_EXTENSIONS'] ]

    if not any([path.exists() for path in file_paths]):
        return 'Invalid file ID', 404

    path = [path for path in file_paths if path.exists()][0]
    def _generator():
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(app.config['CHUNK_SIZE'])
                if not chunk: break
                yield chunk

    response = Response(_generator(), mimetype="application/x-tar", \
        headers = {
            'Content-Disposition': f'attachment; filename={path.name}',
            'content-length': os.path.getsize(path)
        })
    response.timeout = app.config['BODY_TIMEOUT']
    return response

@app.route('/delete/<shard_id>', methods=['DELETE'])
async def delete_file(shard_id):
    file_paths = [ \
            Path( os.path.join(app.config['UPLOAD_FOLDER'], \
                f"{shard_id}.{extension}")) \
            for extension in app.config['ALLOWED_EXTENSIONS'] ]

    if not any([path.exists() for path in file_paths]):
        return 'Invalid file ID', 404

    path = [path for path in file_paths if path.exists()][0]
    os.remove(path)

    return 'File removed'

if __name__ == '__main__':
    app.run("0.0.0.0", 80, debug=True)
