from flask import Flask, request, Response
from werkzeug.utils import secure_filename
from flask_cors import CORS

import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "upload_dir/"
@app.route('/upload', methods = ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def api():

    if request.method == 'POST':
        if (request.form['file']):
            # pin file
            return "sort"
        else:
            print(request.files)
            f = request.files['file']
            now = str(datetime.datetime.now())
            fn = str(f.filename).split(".")[0]
            fext = str(f.filename).split(".")[1]
            finalfn = secure_filename(f"{fn}{now}.{fext}")
            f.save(f"{UPLOAD_DIR}{finalfn}")

            return finalfn

    return "lol"

@app.route('/')
def hello():

    if request.method == 'GET':
        data = "123"
        resp = Response(data, status=200, mimetype='text/plain')
        return resp
    elif request.method == 'POST':
        print(request.get_data())
        print(request.get_json())
        return "200"


if __name__ == '__main__':
    app.run()
