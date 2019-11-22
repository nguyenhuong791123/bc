#!/usr/local/bin/python python
# -*- coding: UTF-8 -*-
from uuid import uuid4
from flask import Flask, jsonify, request
from flask_cors import CORS
from block import Blockchain

# ノードを作る
# Flaskについて詳しくはこちらを読んでほしい http://flask.pocoo.org/docs/0.12/quickstart/#a-minimal-application
app = Flask(__name__)
CORS(app, supports_credentials=True)
# このノードのグローバルにユニークなアドレスを作る
node_identifire = str(uuid4()).replace('-', '')
# ブロックチェーンクラスをインスタンス化する
blockchain = Blockchain()

# メソッドはGETで/mineエンドポイントを作る
@app.route('/mine', methods=['GET'])
def mine():
    # 次のプルーフを見つけるためプルーフ・オブ・ワークアルゴリズムを使用する
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # プルーフを見つけたことに対する報酬を得る
    # 送信者は、採掘者が新しいコインを採掘したことを表すために"0"とする
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifire,
        amount=1,
    )

    # チェーンに新しいブロックを加えることで、新しいブロックを採掘する
    block = blockchain.new_block(proof)

    response = {
        'message': '新しいブロックを採掘しました',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


# メソッドはPOSTで/transactions/newエンドポイントを作る。メソッドはPOSTなのでデータを送信する
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # POSTされたデータに必要なデータがあるかを確認
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # 新しいトランザクションを作る
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'トランザクションはブロック {index} に追加されました'}
    return jsonify(response), 201


# メソッドはGETで、フルのブロックチェーンをリターンする/chainエンドポイントを作る
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/last', methods=['GET'])
def last_chain():
    response = {
        'chain': blockchain.last_block,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes', methods=['GET'])
def nodes():
    response = {
        'nodes': blockchain.all_nodes,
        'length': len(blockchain.all_nodes),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: 有効ではないノードのリストです", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': '新しいノードが追加されました',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'チェーンが置き換えられました',
            'chain': blockchain.chain
        }
    else:
        response = {
            'message': 'チェーンが確認されました',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


# port5000でサーバーを起動する
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
