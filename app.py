from flask import Flask, request, Response, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "upload_dir/"
node_list = {}

@app.route('/first-run', methods = ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def upload():
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

@app.route('/nodes/', defaults={'eth_address': None,'ip': None}, methods = ['GET', 'POST', 'DELETE'])
@app.route('/nodes/<eth_address>/', defaults={'ip': None}, methods = ['GET', 'POST', 'DELETE'])
@app.route('/nodes/<eth_address>/<ip>/', methods = ['GET', 'POST', 'DELETE'])
def nodes(eth_address, ip):

    if not eth_address:
        return jsonify(node_list), 200

    if eth_address:
        doesExist = eth_address in node_list
        if request.method == 'GET' and doesExist:
            return jsonify({
                eth_address: node_list[eth_address]
            }), 200
        elif request.method == 'GET' :
            return jsonify("Not in List"), 400

        if request.method == 'POST':
            if ip:
                node_list[eth_address] = ip
                return jsonify("Success"), 200
            else:
                return jsonify("Invalid IP"), 400

        if request.method == 'DELETE':
            node_list.pop(eth_address)
            return jsonify("Success"), 200

    else:
        return jsonify("Invalid Ethereum Address"), 400

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
