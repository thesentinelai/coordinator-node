from flask import Flask, request, Response, jsonify
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_cors import CORS
import ipfshttpclient
import datetime
from os import remove, chmod

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "upload_dir/"
node_list = {}

ipfs_api = '/ip4/127.0.0.1/tcp/5001/http'
client = ipfshttpclient.connect(ipfs_api)
print(f"Connected to IPFS v{client.version()['Version']}")

@app.route('/first-run', methods = ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def upload():

    reqJSON = request.get_json()

    if request.method == 'POST':

        if (reqJSON and 'file_name' in reqJSON):
            res = client.add(f"{UPLOAD_DIR}{reqJSON['file_name']}")
            # client.pin_ls(type='all')
            return res['Hash'], 200

        elif(type(request.files['file']) == FileStorage):
            f = request.files['file']
            now = str(datetime.datetime.now())
            fn = str(f.filename).split(".")[0]
            fext = str(f.filename).split(".")[1]
            if( fext == "h5"):
                finalfn = secure_filename(f"{fn}{now}.{fext}")
                f.save(f"{UPLOAD_DIR}{finalfn}")
                return finalfn
            else:
                return "Please Upload a Valid Tensorflow Model(.h5) File", 400

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

@app.route('/', methods = ['GET', 'OPTIONS', 'DELETE'])
def hello():

    if request.method == 'GET':
        return "<p style='font-family: monospace;padding: 10px;'>Server is online 🚀</p>"

    elif request.method == 'DELETE':
        print(request.get_data())
        print(request.get_json())
        return "200", 200
    elif request.method == 'OPTIONS':
        fn = request.get_data().decode("utf-8")
        # chmod(f"{UPLOAD_DIR}{fn}", 0o777)
        # remove(f"{UPLOAD_DIR}{fn}")
        return "Done", 200
    else:
        return "sort-hello", 200


if __name__ == '__main__':

    app.run()
