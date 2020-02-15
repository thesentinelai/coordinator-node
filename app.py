""" Coordinating Server """

from os import getenv, path, makedirs
from random import choice
import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from web3 import Web3, HTTPProvider
from flask_cors import CORS
from dotenv import load_dotenv
import ipfshttpclient
import requests
from contract import contract_ABI, contract_address

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "upload_dir/"
node_list = {}

port = int(getenv('PORT', str(5000)))

# ipfs_api = '/ip4/127.0.0.1/tcp/5001/http'
ipfs_api = '/dns/ipfs.infura.io/tcp/5001/https'
client = ipfshttpclient.connect(ipfs_api)
print(f"Connected to IPFS v{client.version()['Version']}")

def send_to_train(task_id=1):

  """ Training Handler"""

  if len(node_list) < 1:
    print("No Node Connected")
    return 0, 200
  else:
    selection = choice(list(node_list.items())) # key, value
    ip = selection[0]
    print(f"Assigning TASKID:{task_id} to {ip}")
    resp = requests.post(f"{ip}/start-training/{task_id}")
    if resp.status_code == 200:
      print("ASSIGNMENT SUCCESS")
      return jsonify({'ip': ip}), 200
    else:
      print("ASSIGNMENT FAILED !!!")
      return "failed", 400

@app.route('/first-run', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def upload():

  """ Upload handler """

  if request.method == 'POST':
    if isinstance(request.files['file'], FileStorage):
      f = request.files['file']
      now = str(datetime.datetime.now())
      fn = str(f.filename).split(".")[0]
      fext = str(f.filename).split(".")[1]
      if fext == "h5":
        finalfn = secure_filename(f"{fn}{now}.{fext}")
        f.save(f"{UPLOAD_DIR}{finalfn}")
        print("Adding File to IPFS")
        res = client.add(f"{UPLOAD_DIR}{finalfn}")
        print(finalfn)
        print(f"Deployed {res['Hash']} to IPFS")
        return str(res['Hash'])
      else:
        print("invald file")
        return "Please Upload a Valid Tensorflow Model(.h5) File", 400

    print("Unsatisfied conditions")
    return "No Can Do", 400

@app.route('/sendtrain/<int:task_id>', methods=['GET', 'POST', 'OPTIONS'])
def sendtrain(task_id):
  return send_to_train(task_id)

@app.route('/next-run/<int:task_id>', methods=['GET', 'POST', 'OPTIONS'])
def nextrun(task_id):

  """ Starts the next round for the model """

  model_hashes = sentinel_contract.functions.getTaskHashes(task_id).call()
  model_hashes = [x for x in list(model_hashes) if x.strip()]
#   print(model_hashes)
  task_data = sentinel_contract.functions.SentinelTasks(task_id).call() # taskID, currentRound, totalRounds, cost

  if len(model_hashes) >= task_data[2]:
    print(f"TASKID:{task_id} ROUND:{task_data[1]} is completed.")
    return "Task Completed", 200
  else:
    req_data = request.get_json()
    model_hash = req_data['modelHash']
    eth_address = req_data['ethAddress']
    acct = w3.eth.account.privateKeyToAccount(getenv("PRIVATEKEY"))
    txn_data = {
        "nonce": w3.eth.getTransactionCount(acct.address),
        "from": acct.address,
        "gas": 3000000,
        "gasPrice": 1,
        "value": 0,
        "chainId": 16110,
    }
    txn_values = [int(task_id), str(model_hash), str(eth_address)]
    print(f"Txn Data : {txn_values}")
    txn = sentinel_contract.functions.updateModelForTask(
        int(task_id),
        str(model_hash),
        Web3.toChecksumAddress(eth_address)
    ).buildTransaction(txn_data)

    signed_txn = w3.eth.account.signTransaction(txn, getenv("PRIVATEKEY"))
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    tx_hash = str(tx_hash.hex())
    print(f"TXNHASH: {tx_hash}")
    send_to_train(int(task_id))
    return tx_hash

@app.route('/nodes', methods=['GET', 'POST', 'DELETE'])
def nodes():

  """ Handles the incoming node connections """

  req_data = request.get_json()
  if req_data and 'eth_address' in req_data:
    eth_address = req_data['eth_address']
  else:
    eth_address = None

  if req_data and 'ip' in req_data:
    ip = req_data['ip']
  else:
    ip = None

  if not eth_address:
    return jsonify(node_list), 200

    # if ip: ip = unquote(ip)
  if eth_address:
    if request.method == 'GET' and ip in node_list:
      return jsonify({
          ip: ip,
          eth_address: node_list[ip]
      }), 200

    if request.method == 'GET':
      return jsonify("Not in List"), 400

    if request.method == 'POST':
      if eth_address and ip:
        node_list[ip] = eth_address
        return jsonify("Success"), 200
      else:
        return jsonify("Invalid Values"), 400

    if request.method == 'DELETE':
      node_list.pop(ip)
      return jsonify("Success"), 200
  else:
    return jsonify("Invalid Ethereum Address"), 400

@app.route('/', methods=['GET', 'OPTIONS', 'DELETE'])
def hello():

  """ Base Route """

  if request.method == 'GET':
    return """<p style='font-family: monospace;padding: 10px;'>
      Coordinator Node is online 🚀
      </p>"""
  if request.method == 'DELETE':
    return "200", 200
  if request.method == 'OPTIONS':
    # fn = request.get_data().decode("utf-8")
    return "Done", 200
  else:
    return "sort-hello", 200

# Start Initialization

w3 = Web3(HTTPProvider('https://betav2.matic.network'))
if not w3.isConnected():
  print("Web3 Not Connected")
  sys.exit(0)
else:
  print(f'Connected to Web3 v{w3.api}')

if not path.exists('upload_dir'): makedirs('upload_dir')

sentinel_contract = w3.eth.contract(address=contract_address, abi=contract_ABI)

# End Initialization

if __name__ != "__main__":

  gunicorn_logger = logging.getLogger('gunicorn.error')
  app.logger.handlers = gunicorn_logger.handlers
  app.logger.setLevel(gunicorn_logger.level)


if __name__ == '__main__':

  app.run(
      host="0.0.0.0",
      port=port,
      debug=False,
      use_reloader=False,
      threaded=True)
      #ssl_context=('/etc/letsencrypt/live/sentinel-coor.anudit.dev/fullchain.pem',
      #             '/etc/letsencrypt/live/sentinel-coor.anudit.dev/privkey.pem'))
