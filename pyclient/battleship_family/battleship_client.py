# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
'''
This SimpleWalletClient class interfaces with Sawtooth through the REST API.
'''

import hashlib
import base64
from base64 import b64encode
import time 
import random
import requests
import yaml

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch

# The Transaction Family Name
FAMILY_NAME = 'battleship'

def _hash(data):
    return hashlib.sha512(data).hexdigest()


class BattleshipClient(object):
    '''Client battleship class.

    This supports create game, delete game, list existing games, shoot, place, show functions.
    '''

    def __init__(self, base_url, keyfile=None):
        '''Initialize the client class.

           This is mainly getting the key pair and computing the address.
        '''

        self._baseUrl = base_url

        if keyfile is None:
            self._signer = None
            return

        try:
            with open(keyfile) as fd:
                privateKeyStr = fd.read().strip()
        except OSError as err:
            raise Exception('Failed to read private key {}: {}'.format(
                keyfile, str(err)))

        try:
            privateKey = Secp256k1PrivateKey.from_hex(privateKeyStr)
        except ParseError as err:
            raise Exception('Failed to load private key: {}'.format(str(err)))

        self._signer = CryptoFactory(create_context('secp256k1')) \
            .new_signer(privateKey)

        self._publicKey = self._signer.get_public_key().as_hex()

        self._address = _hash(FAMILY_NAME.encode('utf-8'))[0:6] + \
            _hash(self._publicKey.encode('utf-8'))[0:64]


    # For each valid cli command in _cli.py file,
    # add methods to:
    # 1. Do any additional handling, if required
    # 2. Create a transaction and a batch
    # 2. Send to rest-api

    def create(self, name, player1, player2, wait=None, auth_user=None, auth_password=None):
        return self._send_battleship_txn(
            name,
            "create",
            player1 = player1, 
            player2  = player2, 
            wait=wait,
            auth_user=auth_user,
            auth_password=auth_password)

    def delete(self, name, wait=None, auth_user=None, auth_password=None):
        return self._send_battleship_txn(
            name,
            "delete",
            wait=wait,
            auth_user=auth_user,
            auth_password=auth_password)

    def shoot(self, name, space, wait=None, auth_user=None, auth_password=None):
        return self._send_battleship_txn(
            name,
            "shoot",
            space,
            wait=wait,
            auth_user=auth_user,
            auth_password=auth_password)

    def place(self, name, space, boat, direction, wait=None, auth_user=None, auth_password=None):
        return self._send_battleship_txn(
            name,
            "place",
            space,
            boat, 
            direction, 
            wait=wait,
            auth_user=auth_user,
            auth_password=auth_password)

    def list(self, auth_user=None, auth_password=None):
        battleship_prefix = self._get_prefix()

        result = self._send_request(
            "state?address={}".format(battleship_prefix),
            auth_user=auth_user,
            auth_password=auth_password)

        try:
            encoded_entries = yaml.safe_load(result)["data"]

            return [
                base64.b64decode(entry["data"]) for entry in encoded_entries
            ]

        except BaseException:
            return None

    def show(self, name, auth_user=None, auth_password=None):
        address = self._get_address(name)

        result = self._send_request(
            "state/{}".format(address),
            name=name,
            auth_user=auth_user,
            auth_password=auth_password)
        try:
            return base64.b64decode(yaml.safe_load(result)["data"])

        except BaseException:
            return None

    def _send_to_restapi(self,
                         suffix,
                         data=None,
                         contentType=None):
        '''Send a REST command to the Validator via the REST API.'''

        if self._baseUrl.startswith("http://"):
            url = "{}/{}".format(self._baseUrl, suffix)
        else:
            url = "http://{}/{}".format(self._baseUrl, suffix)

        headers = {}

        if contentType is not None:
            headers['Content-Type'] = contentType

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if not result.ok:
                raise Exception("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise Exception(
                'Failed to connect to {}: {}'.format(url, str(err)))

        except BaseException as err:
            raise Exception(err)

        return result.text

    def _wrap_and_send(self,
                       action,
                       *values):
        '''Create a transaction, then wrap it in a batch.     
                                                              
           Even single transactions must be wrapped into a batch.
        ''' 

        # Generate a csv utf-8 encoded string as payload
        rawPayload = action

        for val in values:
            rawPayload = ",".join([rawPayload, str(val)])

        payload = rawPayload.encode()

        # Construct the address where we'll store our state
        address = self._address
        inputAddressList = [address]
        outputAddressList = [address]

        if "transfer" == action:
            toAddress = _hash(FAMILY_NAME.encode('utf-8'))[0:6] + \
            _hash(values[1].encode('utf-8'))[0:64]
            inputAddressList.append(toAddress)
            outputAddressList.append(toAddress)

        # Create a TransactionHeader
        header = TransactionHeader(
            signer_public_key=self._publicKey,
            family_name=FAMILY_NAME,
            family_version="1.0",
            inputs=inputAddressList,
            outputs=outputAddressList,
            dependencies=[],
            payload_sha512=_hash(payload),
            batcher_public_key=self._publicKey,
            nonce=random.random().hex().encode()
        ).SerializeToString()

        # Create a Transaction from the header and payload above
        transaction = Transaction(
            header=header,
            payload=payload,
            header_signature=self._signer.sign(header)
        )

        transactionList = [transaction]

        # Create a BatchHeader from transactionList above
        header = BatchHeader(
            signer_public_key=self._publicKey,
            transaction_ids=[txn.header_signature for txn in transactionList]
        ).SerializeToString()

        #Create Batch using the BatchHeader and transactionList above
        batch = Batch(
            header=header,
            transactions=transactionList,
            header_signature=self._signer.sign(header))

        #Create a Batch List from Batch above
        batch_list = BatchList(batches=[batch])

        # Send batch_list to rest-api
        return self._send_to_restapi(
            "batches",
            batch_list.SerializeToString(),
            'application/octet-stream')

    def _get_status(self, batch_id, wait, auth_user=None, auth_password=None):
        try:
            result = self._send_request(
                'batch_statuses?id={}&wait={}'.format(batch_id, wait),
                auth_user=auth_user,
                auth_password=auth_password)
            return yaml.safe_load(result)['data'][0]['status']
        except BaseException as err:
            raise Exception(err) from err

    def _get_prefix(self):
        return _hash('battleship'.encode('utf-8'))[0:6]

    def _get_address(self, name):
        battleship_prefix = self._get_prefix()
        game_address = _hash(name.encode('utf-8'))[0:64]
        return battleship_prefix + game_address

    def _send_request(self,
                      suffix,
                      data=None,
                      content_type=None,
                      name=None,
                      auth_user=None,
                      auth_password=None):
        '''Send a REST command to the Validator via the REST API.'''

        if self._baseUrl.startswith("http://"):
            url = "{}/{}".format(self._baseUrl, suffix)
        else:
            url = "http://{}/{}".format(self._baseUrl, suffix)

        headers = {}

        if auth_user is not None:
            auth_string = "{}:{}".format(auth_user, auth_password)
            b64_string = b64encode(auth_string.encode()).decode()
            auth_header = 'Basic {}'.format(b64_string)
            headers['Authorization'] = auth_header

        if content_type is not None:
            headers['Content-Type'] = content_type

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if result.status_code == 404:
                raise Exception("No such game: {}".format(name))

            if not result.ok:
                raise Exception("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise Exception(
                'Failed to connect to {}: {}'.format(url, str(err))) from err

        except BaseException as err:
            raise Exception(err) 

        return result.text

    def _send_battleship_txn(self,
                     name,
                     action,
                     space="",
                     boat="", 
                     direction="", 
                     player1="", 
                     player2="", 
                     currentplayer="", 
                     wait=None,
                     auth_user=None,
                     auth_password=None):
        # Serialization is just a delimited utf-8 encoded string
        payload = ",".join([name, action, str(space), str(boat), str(direction), str(player1), str(player2), str(currentplayer)]).encode()

        # Construct the address where we'll store our state 
        address = self._get_address(name)

        # Create a TransactionHeader 
        header = TransactionHeader(
            signer_public_key=self._publicKey,
            family_name="battleship",
            family_version="1.0",
            inputs=[address],
            outputs=[address],
            dependencies=[],
            payload_sha512=_hash(payload),
            batcher_public_key=self._publicKey,
            nonce=hex(random.randint(0, 2**64))
        ).SerializeToString()

        # Create a Transaction from the header and payload above 
        transaction = Transaction(
            header=header,
            payload=payload,
            header_signature=self._signer.sign(header)
        )

        transactionList = [transaction]

        # Create a BatchHeader from transactionList above
        header = BatchHeader(
            signer_public_key=self._publicKey, 
            transaction_ids=[txn.header_signature for txn in transactionList]
        ).SerializeToString()
 
        # Create Batch using the BatchHeader and transactionList above 
        batch = Batch(
            header=header,
            transactions=transactionList,
            header_signature=self._signer.sign(header))

        # Create a Batch List from Batch above 
        batch_list = BatchList(batches=[batch])
        batch_id = batch_list.batches[0].header_signature

        if wait and wait > 0:
            wait_time = 0
            start_time = time.time()
            response = self._send_request(
                "batches", batch_list.SerializeToString(),
                'application/octet-stream',
                auth_user=auth_user,
                auth_password=auth_password)
            while wait_time < wait:
                status = self._get_status(
                    batch_id,
                    wait - int(wait_time),
                    auth_user=auth_user,
                    auth_password=auth_password)
                wait_time = time.time() - start_time

                if status != 'PENDING':
                    return response

            return response

        return self._send_request(
            "batches", batch_list.SerializeToString(),
            'application/octet-stream',
            auth_user=auth_user,
            auth_password=auth_password)