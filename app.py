from flask import Flask, request, Response, jsonify
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from contract import contractABI, contractAddress
from web3 import Web3,HTTPProvider
from flask_cors import CORS
from dotenv import load_dotenv
import ipfshttpclient
import datetime
from os import remove, chmod, getenv

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "upload_dir/"
node_list = {}
active_task_list = []

ipfs_api = '/ip4/127.0.0.1/tcp/5001/http'
client = ipfshttpclient.connect(ipfs_api)
print(f"Connected to IPFS v{client.version()['Version']}")

@app.route('/first-run', methods = ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def upload():

    reqJSON = request.get_json()

    if request.method == 'POST':

        if (reqJSON and 'file_name' in reqJSON):
            res = client.add(f"{UPLOAD_DIR}{reqJSON['file_name']}")
            print(f"Deployed {res['Hash']} to IPFS")
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

@app.route('/next-run/<int:task_id>/', methods = ['GET', 'POST'])
def nextrun(task_id):
    eth_address = Web3.toChecksumAddress("0xBeb71662FF9c08aFeF3866f85A6591D4aeBE6e4E")
    if(request.args.get('modelHash')):
        eth_address = request.args.get('modelHash')

    w3 = Web3(HTTPProvider('https://testnet2.matic.network'))
    Sentinel = w3.eth.contract(address=contractAddress,abi=contractABI)
    acct = w3.eth.account.privateKeyToAccount(getenv("PRIVATEKEY"))
    txn = Sentinel.functions.updateModelForTask(int(task_id), str(request.args.get('modelHash'))).buildTransaction({
        "nonce": w3.eth.getTransactionCount(acct.address),
        "from": acct.address,
        "gas": 65000,
        "gasPrice": 0,
        "value": 0,
        "chainId": 8995,
    })

    signed_txn = w3.eth.account.signTransaction(txn, getenv("PRIVATEKEY"))
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    tx_hash = str(tx_hash.hex())
    print(tx_hash)

    active_task_list.append(int(task_id))

    return tx_hash


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

@app.route('/active-tasks/', methods = ['GET', 'POST'])
def activetasks():
    return jsonify(active_task_list), 200

@app.route('/', methods = ['GET', 'OPTIONS', 'DELETE'])
def hello():

    if request.method == 'GET':
        return "<p style='font-family: monospace;padding: 10px;'>Server is online 🚀</p>"

    elif request.method == 'DELETE':
        return "200", 200
    elif request.method == 'OPTIONS':
        fn = request.get_data().decode("utf-8")
        # chmod(f"{UPLOAD_DIR}{fn}", 0o777)
        # remove(f"{UPLOAD_DIR}{fn}")
        return "Done", 200
    else:
        return "sort-hello", 200


if __name__ == '__main__':
    w3 = Web3(HTTPProvider('https://testnet2.matic.network'))
    if not w3.isConnected():
        print("Web3 Not Connected")
        exit(0)
    app.run()
