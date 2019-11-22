#!/usr/local/bin/python python
# -*- coding: UTF-8 -*-
import os
import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address):
        """
        ノードリストに新しいノードを加える
        :param address: <str> ノードのアドレス 例: 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        # self.nodes.add(parsed_url.netloc)
        self.nodes.add(address)

    def valid_chain(self, chain):
        """
        ブロックチェーンが正しいかを確認する

        :param chain: <list> ブロックチェーン
        :return: <bool> True であれば正しく、 False であればそうではない
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n--------------\n")

            # ブロックのハッシュが正しいかを確認
            if block['previous_hash'] != self.hash(last_block):
                return False

            # プルーフ・オブ・ワークが正しいかを確認
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        これがコンセンサスアルゴリズムだ。ネットワーク上の最も長いチェーンで自らのチェーンを
        置き換えることでコンフリクトを解消する。
        :return: <bool> 自らのチェーンが置き換えられると True 、そうでなれけば False
        """

        neighbours = self.nodes
        new_chain = None

        # 自らのチェーンより長いチェーンを探す必要がある
        max_length = len(self.chain)

        # 他のすべてのノードのチェーンを確認
        for node in neighbours:
            # response = requests.get(f'https://{node}/chain')
            cafile = os.path.join('/var/www/tls/', 'crt.pem')
            # response = requests.get(f'{node}/chain', verify=cafile)
            response = requests.get(f'{node}/chain', verify=False)

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # そのチェーンがより長いか、有効かを確認
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # もし自らのチェーンより長く、かつ有効なチェーンを見つけた場合それで置き換える
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash=None):
        """
        ブロックチェーンに新しいブロックを作る
        :param proof: <int> プルーフ・オブ・ワークアルゴリズムから得られるプルーフ
        :param previous_hash: (オプション) <str> 前のブロックのハッシュ
        :return: <dict> 新しいブロック
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # 現在のトランザクションリストをリセット
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        次に採掘されるブロックに加える新しいトランザクションを作る
        :param sender: <str> 送信者のアドレス
        :param recipient: <str> 受信者のアドレス
        :param amount: <int> 量
        :return: <int> このトランザクションを含むブロックのアドレス
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # チェーンの最後のブロックをリターンする
        return self.chain[-1]

    @property
    def all_nodes(self):
        print(len(self.nodes))
        if len(self.nodes) <= 0:
            return []
        return [i for i in self.nodes]

    @staticmethod
    def hash(block):
        """
        ブロックの SHA-256 ハッシュを作る
        :param block: <dict> ブロック
        :return: <str>
        """

        # 必ずディクショナリ（辞書型のオブジェクト）がソートされている必要がある。そうでないと、一貫性のないハッシュとなってしまう
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        シンプルなプルーフ・オブ・ワークのアルゴリズム:
         - hash(pp') の最初の4つが0となるような p' を探す
         - p は前のプルーフ、 p' は新しいプルーフ
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        プルーフが正しいかを確認する: hash(last_proof, proof)の最初の4つが0となっているか？
        :param last_proof: <int> 前のプルーフ
        :param proof: <int> 現在のプルーフ
        :return: <bool> 正しければ true 、そうでなれけば false
        """

        guess = f'{last_proof}{proof}'.encode()
        # print(last_proof)
        # print(proof)
        # print(guess)
        guess_hash = hashlib.sha256(guess).hexdigest()
        # print(guess_hash)

        return guess_hash[:4] == "0000"
