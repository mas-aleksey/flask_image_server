import os
import base64
from binascii import Error as BinasciiError
from datetime import datetime

from flask import Flask, request, send_from_directory, jsonify, abort
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException


ALLOWED_EXTENSIONS = ('jpg', 'jpeg')


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def gen_file_name(file_dir: str, filename: str) -> str:
    i = 1
    new_name = filename
    while os.path.exists(os.path.join(file_dir, new_name)):
        name, extension = os.path.splitext(filename)
        new_name = '%s_%s%s' % (name, str(i), extension)
        i += 1
    return new_name


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config['UPLOAD_FOLDER'] = 'images/'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    def prepare_file_name(file_name):
        if not file_name:
            abort(400, description="Missing required key in data: 'filename'")
        secure_name = secure_filename(file_name)
        final_name = gen_file_name(app.config['UPLOAD_FOLDER'], secure_name)

        if not allowed_file(final_name):
            abort(400, description="File type not allowed")

        return final_name

    def prepare_file_body(data64):
        if not data64:
            abort(400, description="Missing required key in data: 'data'")
        try:
            binary_data = base64.decodebytes(data64.encode())
        except BinasciiError as exc:
            abort(400, description=f"invalid data in base64: {exc}")
        else:
            return binary_data

    def full_path(file_name):
        return os.path.join(app.config['UPLOAD_FOLDER'], file_name)

    def is_image_file(file_name):
        file_path = full_path(file_name)
        if not os.path.isfile(file_path):
            return False
        if not allowed_file(file_name):
            return False
        return True

    def get_file_info(file_name):
        file_path = full_path(file_name)
        size = os.path.getsize(file_path)
        last_mod_time = os.path.getmtime(file_path)
        time = datetime.fromtimestamp(last_mod_time).strftime('%Y-%m-%d %H:%M:%S')

        return {'file_name': file_name, 'size': size, 'last_modification_time': time}

    @app.route("/image", methods=['GET', 'POST', 'DELETE'])
    def upload():
        if request.method == 'POST':
            file = request.form.to_dict()
            if not file:
                abort(400, description="Missing file in data payload")
            file_name = prepare_file_name(file.get('filename'))
            file_data = prepare_file_body(file.get('data'))
            with open(full_path(file_name), 'wb') as new_img:
                new_img.write(file_data)

            return jsonify(get_file_info(file_name))

        if request.method == 'GET':
            files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if is_image_file(f)]
            return jsonify({"files": [get_file_info(file) for file in files]})

        if request.method == 'DELETE':
            filename = request.json.get('file')
            if not filename:
                abort(400, description="Missing required key 'file'")
            try:
                os.remove(full_path(filename))
            except OSError as exc:
                abort(500, description=f"deleting error: {exc}")
            else:
                return jsonify({filename: 'True'})

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        return jsonify({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }), e.code

    @app.route('/images/<string:filename>', methods=['GET'])
    def get_image(filename):
        if not is_image_file(filename):
            abort(500, description='Image file not found')
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']), filename=filename)

    return app
