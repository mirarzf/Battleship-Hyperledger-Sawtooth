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
Transaction family class for battleship.
'''

import traceback
import sys
import hashlib
import logging

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor

from processor.battleship_payload import BattleshipPayload
from processor.battleship_state import Game, BattleshipState

LOGGER = logging.getLogger(__name__)
ID_BOAT = ['A', 'B', 'C', 'D', 'E']
BOAT_CASES = [[5, 4, 3, 3, 2],[5, 4, 3, 3, 2]]

FAMILY_NAME = "battleship"

def _hash(data):
    '''Compute the SHA-512 hash and return the result as hex characters.'''
    return hashlib.sha512(data).hexdigest()

# Prefix for battleship is the first six hex digits of SHA-512(TF name).
bs_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]

class BattleshipTransactionHandler(TransactionHandler):
    '''                                                       
    Transaction Processor class for the battleship transaction family.       
                                                              
    This with the validator using the accept/get/set functions.
    It implements functions to deposit, withdraw, and transfer money.
    '''

    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):
        '''This implements the apply function for this transaction handler.
                                                              
           This function does most of the work for this class by processing
           a single transaction for the battleship transaction family.   
        '''                                                   
        
        # Get the payload and extract battleship-specific information.
        header = transaction.header

        # Get the public key sent from the client.
        signer = header.signer_public_key
        
        battleship_payload = BattleshipPayload.from_bytes(transaction.payload)
        
        battleship_state = BattleshipState(context)

        # Perform the command 
        if battleship_payload.action == 'delete':
            game = battleship_state.get_game(battleship_payload.name)

            if game is None:
                raise InvalidTransaction(
                    'Invalid action: game does not exist')

            battleship_state.delete_game(battleship_payload.name)

        elif battleship_payload.action == 'create':

            if battleship_state.get_game(battleship_payload.name) is not None:
                raise InvalidTransaction(
                    'Invalid action: Game already exists: {}'.format(
                        battleship_payload.name))

            ## ADAPT board shape //!\\
            game = Game(name=battleship_payload.name,
                        board_P1="-" * 100,
                        board_P2="-" * 100,
                        state="P1-NEXT",
                        player1="",
                        player2="")

            battleship_state.set_game(battleship_payload.name, game)
            _display("Player {} created a game.".format(signer[:6]))
        
        elif battleship_payload.action == 'show': 
            game = battleship_state.get_game(battleship_payload.name)

            if game.player1 == '' or game.player2 == '':
                raise InvalidTransaction(
                    'Invalid action: show requires two existing players')

        elif battleship_payload.action == 'shoot':
            game = battleship_state.get_game(battleship_payload.name)

            if game is None:
                raise InvalidTransaction(
                    'Invalid action: shoot requires an existing game')

            ## ADAPT to battleship game state
            if game.state in ('P1-WIN', 'P2-WIN'):
                raise InvalidTransaction('Invalid Action: Game has ended')

            if (game.player1 and game.state == 'P1-NEXT'
                and game.player1 != signer) or \
                    (game.player2 and game.state == 'P2-NEXT'
                     and game.player2 != signer):
                raise InvalidTransaction(
                    "Not this player's turn: {}".format(signer[:6]))
            
            if game.state == "P1-NEXT":

                if game.board_P2[battleship_payload.space - 1] == 'X' or game.board_P2[battleship_payload.space - 1] == 'O':
                    raise InvalidTransaction(
                        'Invalid Action: space {} already attacked'.format(
                            battleship_payload))
                else :
                    print("HIT/SUNK/MISS")   #TBD add X to the board

                if game.player1 == '':
                    game.player1 = signer

                elif game.player2 == '':
                    game.player2 = signer

def _update_board(board, space, state):
    index = space - 1
    if board[index] == '-':
        print('MISS')
        mark = 'X'
    elif board[index] in ID_BOAT:
        mark = 'O'
        if state == 'P1-NEXT' :
            id = 1
        else :
            id = 0
        if BOAT_CASES[id][ID_BOAT.index(board[index])] == 1:
            print('SUNK')
        else :
            print('HIT')

        # Update boat cases left status for hit or sunk boat
        BOAT_CASES[id][ID_BOAT.index(board[index])] -= 1

    # replace the index-th space with mark, leave everything else the same
    return ''.join([
        current if square != index else mark
        for square, current in enumerate(board)
    ])

def _update_game_state(game_state):
    P1_wins = _is_win(0)
    P2_wins = _is_win(1)

    if P1_wins and P2_wins:
        raise InternalError('Two winners (there can be only one)')

    if P1_wins:
        return 'P1-WIN'

    if P2_wins:
        return 'P2-WIN'

    if game_state == 'P1-NEXT':
        return 'P2-NEXT'

    if game_state == 'P2-NEXT':
        return 'P1-NEXT'

    if game_state in ('P1-WINS', 'P2-WINS'):
        return game_state

    raise InternalError('Unhandled state: {}'.format(game_state))

def _is_win(id):
    for k in BOAT_CASES[id]:
        if k != 0:
            return False
    return True

## MODIFY BOARD LAYOUT /!\
def _game_data_to_str(board, game_state, player1, player2, name):
    board = list(board.replace("-", " "))
    out = ""
    out += "GAME: {}\n".format(name)
    out += "PLAYER 1: {}\n".format(player1[:6])
    out += "PLAYER 2: {}\n".format(player2[:6])
    out += "STATE: {}\n".format(game_state)
    out += "\n"
    out += "   | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 "
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " A | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[0], board[1], board[2], board[3], board[4], board[5], board[6], board[7], board[8], board[9])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " B | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[10], board[11], board[12], board[13], board[14], board[15], board[16], board[17], board[18], board[19])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " C | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[20], board[21], board[22], board[23], board[24], board[25], board[26], board[27], board[28], board[29])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " D | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[30], board[31], board[32], board[33], board[34], board[35], board[36], board[37], board[38], board[39])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " E | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[40], board[41], board[42], board[43], board[44], board[45], board[46], board[47], board[48], board[49])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " F | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[50], board[51], board[52], board[53], board[54], board[55], board[56], board[57], board[58], board[59])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " G | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[60], board[61], board[62], board[63], board[64], board[65], board[66], board[67], board[68], board[69])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " H | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[70], board[71], board[72], board[73], board[74], board[75], board[76], board[77], board[78], board[79])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " I | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[80], board[81], board[82], board[83], board[84], board[85], board[86], board[87], board[88], board[89])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    out += " J | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[90], board[91], board[92], board[93], board[94], board[95], board[96], board[97], board[98], board[99])
    out += "---|---|---|---|---|---|---|---|---|---|---"
    return out

def _display(msg):
    n = msg.count("\n")

    if n > 0:
        msg = msg.split("\n")
        length = max(len(line) for line in msg)
    else:
        length = len(msg)
        msg = [msg]

    # pylint: disable=logging-not-lazy
    LOGGER.debug("+" + (length + 2) * "-" + "+")
    for line in msg:
        LOGGER.debug("+ " + line.center(length) + " +")
    LOGGER.debug("+" + (length + 2) * "-" + "+")

def setup_loggers():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

def main():
    '''Entry-point function for the battleship transaction processor.'''
    setup_loggers()
    try:
        # Register the transaction handler and start it.
        processor = TransactionProcessor(url='tcp://validator:4004')

        handler = BattleshipTransactionHandler(bs_namespace)

        processor.add_handler(handler)

        processor.start()

    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
