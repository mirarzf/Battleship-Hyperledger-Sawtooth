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

from re import M
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
ID_BOAT = ['L', 'M', 'N', 'Q', 'P'] # Name IDs of ID_BOAT, can be found in CLI as well 
BOAT_CASES = [[5, 4, 3, 3, 2],[5, 4, 3, 3, 2]] # Initial number of cases for boat cases 

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
            if battleship_payload.player1 == None or battleship_payload.player2 == None: 
                raise InvalidTransaction(
                    'Invalid action: create requires two players')

            if battleship_state.get_game(battleship_payload.name) is not None:
                raise InvalidTransaction(
                    'Invalid action: Game already exists: {}'.format(
                        battleship_payload.name))

            game = Game(name=battleship_payload.name,
                        board_P1="-" * 100,
                        board_P2="-" * 100,
                        state="PLACE",
                        player1=battleship_payload.player1,
                        player2=battleship_payload.player2,
                        boat_cases=_game_boat_data_to_str([[5, 4, 3, 3, 2],[5, 4, 3, 3, 2]]),
                        to_place=_game_boat_data_to_str([[1, 1, 1, 1, 1], [1, 1, 1, 1, 1]]))

            battleship_state.set_game(battleship_payload.name, game)
            _display("Player {} created a game.".format(signer[:6]))
        
        elif battleship_payload.action == 'show': 
            game = battleship_state.get_game(battleship_payload.name)

            if game is None:
                raise InvalidTransaction(
                    'Invalid action: show requires an existing game')

            if game.player1 == '' or game.player2 == '':
                raise InvalidTransaction(
                    'Invalid action: show requires two existing players')
        
        elif battleship_payload.action == 'place': 
            game = battleship_state.get_game(battleship_payload.name)
            if game is None:
                raise InvalidTransaction(
                    'Invalid action: place requires an existing game')

            if game.state != 'PLACE': 
                raise InvalidTransaction('Invalid Action : Game has already started, ships can no longer be placed')

            if game.state == "PLACE":
                currentplayer = battleship_payload.currentplayer
                if game.player1 == currentplayer: 
                    boardtoupdate = game.board_P1 
                    id = 0
                elif game.player2 == currentplayer: 
                    boardtoupdate = game.board_P2 
                    id = 1
                else: 
                    raise InvalidTransaction(
                        "Invalid action: the player '{}' doesn't exist in this game."
                        "'{}' and '{}' do though.".format(currentplayer, game.player1, game.player2))

                upd_board, to_place_list = _place(boardtoupdate, 
                                                _game_boat_data_to_list(game.to_place),
                                                battleship_payload.space,
                                                battleship_payload.boat, 
                                                battleship_payload.direction, 
                                                id)

                upd_game_state = _update_game_state(game.state, to_place_list, _game_boat_data_to_list(game.boat_cases))

                if game.player1 == currentplayer: 
                    game.board_P1 = upd_board
                else: # game.player2 == currentplayer 
                    game.board_P2 = upd_board
                game.to_place = _game_boat_data_to_str(to_place_list)
                game.state = upd_game_state

            battleship_state.set_game(battleship_payload.name, game)

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

            currentplayer = battleship_payload.currentplayer
            if (game.player1 and game.state == 'P1-NEXT'
                and game.player1 != currentplayer) or \
                    (game.player2 and game.state == 'P2-NEXT'
                     and game.player2 != currentplayer):
                raise InvalidTransaction(
                    "Not this player's turn: {}".format(currentplayer[:6]))
            
            if game.state == "P1-NEXT":

                if game.board_P2[battleship_payload.space - 1] == 'X' or game.board_P2[battleship_payload.space - 1] == 'O':
                    raise InvalidTransaction(
                        'Invalid Action: space {} already attacked'.format(
                            battleship_payload))

                upd_board, boat_cases_list = _update_board(game.board_P2, 
                                        _game_boat_data_to_list(game.boat_cases),
                                        battleship_payload.space,
                                        game.state)

                upd_game_state = _update_game_state(game.state, _game_boat_data_to_list(game.to_place), boat_cases_list)
                
                game.board_P2 = upd_board
                game.boat_cases = _game_boat_data_to_str(boat_cases_list)
                game.state = upd_game_state
                _display("Player {} attacks space: {}\n\n".format(currentplayer[:6], battleship_payload.space)) 


            elif game.state == "P2-NEXT":

                if game.board_P1[battleship_payload.space - 1] == 'X' or game.board_P1[battleship_payload.space - 1] == 'O':
                    raise InvalidTransaction(
                        'Invalid Action: space {} already attacked'.format(
                            battleship_payload))
                
                upd_board, boat_cases_list = _update_board(game.board_P1, 
                                        _game_boat_data_to_list(game.boat_cases),
                                        battleship_payload.space,
                                        game.state)

                upd_game_state = _update_game_state(game.state, _game_boat_data_to_list(game.to_place), boat_cases_list)
                
                game.board_P1 = upd_board
                game.boat_cases = _game_boat_data_to_str(boat_cases_list)
                game.state = upd_game_state
                _display("Player {} attacks space: {}\n\n".format(currentplayer[:6], battleship_payload.space)) 

            battleship_state.set_game(battleship_payload.name, game)
            
        else:
            raise InvalidTransaction('Unhandled action: {}'.format(
                battleship_payload.action))

def _update_board(board, boat_cases, space, state):
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

            if boat_cases[id][ID_BOAT.index(board[index])] == 1:
                print('SUNK')
            else :
                print('HIT')

            # Update boat cases left status for hit or sunk boat
            boat_cases[id][ID_BOAT.index(board[index])] -= 1

        else: 
            mark = board[index]

    # replace the index-th space with mark, leave everything else the same
    updated_board = ''.join([
        current if square != index else mark
        for square, current in enumerate(board)
    ])

    return updated_board, boat_cases

def _place(board, to_place, space, boat_ID, direction, playerid):
    '''
    board is the board of the player where the boat will be placed. 
    space corresponds to the space of the boat: int between 1 and 100. 
    Direction is either 'vertical' or 'horizontal'. 
    boat_ID is the type of boat. 
    playerid = 0 if player1 is placing their boat. 
    playerid = 1 if player2 is placing their boat. 
    '''

    if to_place[playerid][ID_BOAT.index(boat_ID)] == 0:
        raise InvalidTransaction('Invalid Action: This boat has already been placed. {}'.format(to_place[playerid]))

    index = space - 1
    mark = boat_ID
    boat_length = BOAT_CASES[playerid][ID_BOAT.index(boat_ID)]

    # test if the boat will stay inside the board
    if direction == 'vertical':
        x = 0
        y = 1
        if index + (boat_length-1)*10 > 100 :
            raise InvalidTransaction('Invalid Action: Your boat is outside the board on the bottom')
    else :
        x = 1
        y = 0
        if (index%10) + (boat_length-1) > 9:
            raise InvalidTransaction('Invalid Action: Your boat is outside the board on the right')
    
    # list of what is on the path of the new boat
    index_list = []
    for k in range(boat_length):
        index_list.append(index + k*x + k*y*10)

    # check if boats don't overlapp
    path = []
    for square, current in enumerate(board) :
        for i in index_list :
            if square == i :
                path.append(current)
    
    for k in ID_BOAT :
        if k in path :
            raise InvalidTransaction('Invalid Action: Your boat is overlapping with another')

    to_place[playerid][ID_BOAT.index(boat_ID)] -= 1

    # replace the i-th space with mark and all the cases that are in the specified direction
    updated_board = ''.join([
        current if square not in index_list else mark
        for square, current in enumerate(board)
    ])

    return updated_board, to_place 

def _update_game_state(game_state, to_place, boat_cases):
    P1_wins = _is_win(0, boat_cases)
    P2_wins = _is_win(1, boat_cases)
    start_game = _boats_placed(to_place)

    if start_game and game_state == 'PLACE':
        return 'P1-NEXT'

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
    
    if game_state in ('P1-WINS', 'P2-WINS', 'PLACE'):
        return game_state

    raise InternalError('Unhandled state: {}'.format(game_state))

def _boats_placed(to_place):
    res1 = 0
    res2 = 0
    for k in to_place[0] :
        res1 += k
    for k in to_place[1] :
        res2 += k
    if res1 > 0 :
        print('Player1 has not finished placing boats')
        return False
    elif res2 > 0 :
        print('Player2 has not finished placing boats')
        return False
    return True

def _is_win(id, boat_cases):
    '''
    INPUT: - id is the player id. 0 is for player 1 and 1 is for player 2. 
           - boat_cases is the game list of boat cases. 
    OUTPUT: if the player 1 wins. 
    '''
    for k in boat_cases[1-id]:
        if k != 0:
            return False
    return True

def _game_boat_data_to_str(boat_table): 
    out = ""
    for i in range(2): 
        for j in range(5): 
            out += str(boat_table[i][j])
    return out 

def _game_boat_data_to_list(boat_str): 
    out = []
    for i in range(2): 
        playeri = []
        for j in range(5): 
            playeri.append(int(boat_str[i*5+j]))
        out.append(playeri)
    return out 

def _display_enemy(board):
    ''' 
    This returns a board that shows where the 
    current player has shot on their enemy board. 
    '''
    board_disp = ""
    for k in board :
        if k in ID_BOAT :
            board_disp += "-"
        else :
            board_disp += k
    return board_disp

def _game_data_to_str(board, game_state, player1, player2, name):
    board = list(board.replace("-", " "))
    print(len(board))
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
