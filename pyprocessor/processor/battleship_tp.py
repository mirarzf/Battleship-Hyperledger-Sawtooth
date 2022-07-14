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
TO_PLACE = [[1, 1, 1, 1, 1], [1, 1, 1, 1, 1]]

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
                        state="PLACE",
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

            if game.state == 'PLACE':
                raise InvalidTransaction('Invalid Action : Game has not started, ships are still being placed')

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

def _update_board(board, row, col, state):
    # Conversion of the COL ROW format to INT of the space 
    rownames = {
        "A": 0, 
        "B": 1, 
        "C": 2, 
        "D": 3, 
        "E": 4, 
        "F": 5, 
        "G": 6, 
        "H": 7, 
        "I": 8, 
        "J": 9, 
    }
    space = rownames[row]*10 + col
    index = space - 1

    if state == 'PLACE' :
        mark = board[index]
        
    else: 
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

def place(board, row, col, state, boat_ID, direction):
    '''
    col, row : col is an integer between 1 and 10, row is a character between A and J. 
    Direction is either 'vertical' or 'horizontal'. 
    boat_ID is the type of boat. 
    '''
    
    # Conversion of the COL ROW format to INT of the space 
    rownames = {
        "A": 0, 
        "B": 1, 
        "C": 2, 
        "D": 3, 
        "E": 4, 
        "F": 5, 
        "G": 6, 
        "H": 7, 
        "I": 8, 
        "J": 9, 
    }
    space = rownames[row]*10 + col
    index = space - 1

    if state != 'PLACE':
        raise InvalidTransaction('Invalid Action: Game has started, all the ships have been placed')
    mark = boat_ID

    boat_length = BOAT_CASES[id][ID_BOAT.index(board[index])]

    # test if the boat will stay inside the board
    if direction == 'vertical':
        x = 0
        y = 1
        if index + boat_length*10 > 100 :
            raise InvalidTransaction('Invalid Action: Your boat is outside the board on the bottom')
    else :
        x = 1
        y = 0
        if index + boat_length > 9:
            raise InvalidTransaction('Invalid Action: Your boat is outside the board on the right')
    
    # list of what is on the path of the new boat
    index_list = []
    for k in range(boat_length):
        index_list.append(index + k*x + k*y*10)
        mark = boat_ID

    path = []
    for square, current in enumerate(board) :
        for i in index_list :
            if square == i :
                path.append(current)
    
    # check if boats don't overlapp
    for k in ID_BOAT :
        if k in path :
            raise InvalidTransaction('Invalid Action: Your boat is overlapping with another')

    # replace the i-th space with mark and all the cases that are in the specified direction
    return ''.join([
        current if square not in index_list else mark
        for square, current in enumerate(board)
    ])

def _update_game_state(game_state):
    P1_wins = _is_win(0)
    P2_wins = _is_win(1)
    start_game = _boats_placed()

    if start_game:
        return 'P1-NEXT'
    else: 
        return 'PLACE'

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

def _boats_placed():
    res1 = 0
    res2 = 0
    for k in TO_PLACE[0] :
        res1 += k
    for k in TO_PLACE[1] :
        res2 += k
    if res1 > 0 :
        print('Player1 has not finished placing boats')
        return False
    elif res2 > 0 :
        print('Player2 has not finished placing boats')
        return False
    return True

def _is_win(id):
    for k in BOAT_CASES[id]:
        if k != 0:
            return False
    return True

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
