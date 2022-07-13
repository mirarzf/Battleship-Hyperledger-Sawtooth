# Copyright 2017 Intel Corporation
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
This file is used for automated testing of the battleship client.
'''

from sawtooth_processor_test.message_factory import MessageFactory

class BattleshipMessageFactory(object):
    def __init__(self, signer=None):
        self._factory = MessageFactory(
            family_name="battleship",
            family_version="1.0",
            namespace=MessageFactory.sha512("battleship".encode("utf-8"))[0:6],
            signer=signer)

    def _game_to_address(self, game):
        return self._factory.namespace + \
            self._factory.sha512(game.encode())[0:64]

    def get_public_key(self):
        return self._factory.get_public_key()

    def create_tp_register(self):
        return self._factory.create_tp_register()

    def create_tp_response(self, status):
        return self._factory.create_tp_response(status)

    def _create_txn(self, txn_function, game, action, space=None):
        payload = ",".join([
            str(game), str(action), str(space)
        ]).encode()

        addresses = [self._game_to_address(game)]

        return txn_function(payload, addresses, addresses, [])

    def create_tp_process_request(self, action, value=None):
        txn_function = self._factory.create_tp_process_request
        return self._create_txn(txn_function, action, value)

    def create_transaction(self, action, value=None):
        txn_function = self._factory.create_transaction
        return self._create_txn(txn_function, action, value)

    def create_get_request(self):
        addresses = [self._make_address()]
        return self._factory.create_get_request(addresses)

    ## Adapt to board def /!\
    def create_set_request(
        self, game, board_P1="---------------------------------------------------------------------------------------------------", board_P2="---------------------------------------------------------------------------------------------------", state="PLACE", player1="", player2=""
    ):
        address = self._game_to_address(game)

        data = None
        if state is not None:
            data = ",".join([game, board_P1, board_P2, state, player1, player2]).encode()
        else:
            data = None

        return self._factory.create_set_request({address: data})

    ## Adapt to board def /!\
    def create_get_response(
        self, game, board_P1="---------------------------------------------------------------------------------------------------", board_P2="---------------------------------------------------------------------------------------------------", state="PLACE", player1="", player2=""
    ):
        address = self._game_to_address(game)

        data = None
        if board_P1 is not None and board_P2 is not None:
            data = ",".join([game, board_P1, board_P2, state, player1, player2]).encode()
        else:
            data = None

        return self._factory.create_get_response({address: data})

    def create_set_response(self, game):
        addresses = [self._make_address()]
        return self._factory.create_set_response(addresses)

