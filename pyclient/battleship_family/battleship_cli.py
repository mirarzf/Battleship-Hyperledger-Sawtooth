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
Command line interface for the battleship transaction family.

Parses command line arguments and passes it to the BattleshipClient class
to process.
''' 

import argparse
import getpass
import logging
import os
import sys
import traceback
import pkg_resources

from colorlog import ColoredFormatter


from battleship_family.battleship_client import BattleshipClient
ID_BOAT = ['Z', 'Y', 'X', 'W', 'V']

DISTRIBUTION_NAME = 'battleship'

DEFAULT_URL = 'http://rest-api:8008'

def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)
    clog.setLevel(logging.DEBUG)
    return clog

def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))

def add_create_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'create',
        help='Creates a new battleship game',
        description='Sends a transaction to start an battleship game with the '
        'identifier <name>. This transaction will fail if the specified '
        'game already exists.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='unique identifier for the new game')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--disable-client-validation',
        action='store_true',
        default=False,
        help='disable client validation')

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for game to commit')


def add_list_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'list',
        help='Displays information for all battleship games',
        description='Displays information for all battleship games in state, showing '
        'the players, the game state, and the board for each game.',
        parents=[parent_parser])

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')


def add_show_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'show',
        help='Displays information about an battleship game',
        description='Displays the battleship game <name>, showing the players, '
        'the game state, and the board',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='identifier for the game')

    parser.add_argument(
        'username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

def correct_space_row (string): 
    row = string 
    rowlist = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    if row not in rowlist: 
        raise argparse.ArgumentTypeError('Row has to be between A and J')
    return row 
    
def correct_space_col (str): 
    col = int(str) 
    if col < 0 or col > 10: 
        raise argparse.ArgumentTypeError('Column has to be between 1 and 10')
    return col 

def add_shoot_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'shoot',
        help='Shoots a space in a battleship game',
        description='Sends a transaction to shoot an enemy square in the '
        'battleship game with the identifier <name>. This transaction will fail if the '
        'specified game does not exist.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='identifier for the game')

    parser.add_argument(
        'row', 
        type=correct_space_row, 
        help='row of the square to shoot (A-J)'
    )

    parser.add_argument(
        'col', 
        type=correct_space_col, 
        help='column of the square to shoot (1-10)'
    )

    parser.add_argument(
        'username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for shoot transaction '
        'to commit')
        
def add_place_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'place',
        help='Places a boat on a space in a battleship game',
        description='Sends a transaction to place a boat on your own board in the'
        'battleship game with the identifier <name>. This transaction will fail if the '
        'specified game does not exist.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='identifier for the game')

    parser.add_argument(
        'row', 
        type=correct_space_row, 
        help='row of the square to place (A-J)'
    )

    parser.add_argument(
        'col', 
        type=correct_space_col, 
        help='column of the square to place (1-10)'
    )

    parser.add_argument(
        'direction', 
        type=str, 
        help='vertical or horizontal: goes to the right or '
        'to the bottom from the stated case'
    )

    parser.add_argument(
        'boat', 
        type=str, 
        help='boat type from V to Z. \n\n'
        'V: 5 cases \n'
        'W: 4 cases \n'
        'X: 3 cases \n'
        'Y: 3 cases \n'
        'Z: 2 cases \n'
    )

    parser.add_argument(
        'username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for place transaction '
        'to commit')


def add_delete_parser(subparsers, parent_parser):
    parser = subparsers.add_parser('delete', parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='name of the game to be deleted')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for delete transaction to commit')

def create_parent_parser(prog_name):
    '''Define the -V/--version command line options.'''
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    '''Define the command line parsing for all the options and subcommands.'''
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to manage your simple wallet',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    subparsers.required = True

    add_create_parser(subparsers, parent_parser)
    add_list_parser(subparsers, parent_parser)
    add_show_parser(subparsers, parent_parser)
    add_shoot_parser(subparsers, parent_parser)
    add_place_parser(subparsers, parent_parser)
    add_delete_parser(subparsers, parent_parser)

    return parser

def _get_url(args):
    return DEFAULT_URL if args.url is None else args.url


def _get_keyfile(args):
    '''Get the private key for a customer.'''
    username = getpass.getuser() if args.username is None else args.username
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, username)


def _get_auth_info(args):
    auth_user = args.auth_user
    auth_password = args.auth_password
    if auth_user is not None and auth_password is None:
        auth_password = getpass.getpass(prompt="Auth Password: ")

    return auth_user, auth_password

def _get_pubkeyfile(customerName):
    '''Get the public key for a customer.'''
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.pub'.format(key_dir, customerName)

def do_list(args):
    url = _get_url(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=None)

    game_list = [
        game.split(',')
        for games in client.list(auth_user=auth_user,
                                 auth_password=auth_password)
        for game in games.decode().split('|')
    ]

    if game_list is not None:
        fmt = "%-15s %-15.15s %-15.15s %s"
        print(fmt % ('GAME', 'PLAYER 1', 'PLAYER 2', 'STATE'))
        for game_data in game_list:

            name, board_P1, board_P2, game_state, player1, player2 = game_data

            print(fmt % (name, player1[:6], player2[:6], game_state))
    else:
        raise BaseException("Could not retrieve game listing.")


def do_show(args):
    '''
    This shows the boards of a game. When it is you turn, it displays your own board with where your enemy 
    has shot and the enemy board (with no boats) whith the shots you made
    '''
    name = args.name

    url = _get_url(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=None)

    data = client.show(name, auth_user=auth_user, auth_password=auth_password)

    if data is not None:

        board_str_P1, board_str_P2, game_state, player1, player2 = {
            name: (board_P1, board_P2, state, player_1, player_2)
            for name, board_P1, board_P2, state, player_1, player_2 in [
                game.split(',')
                for game in data.decode().split('|')
            ]
        }[name]

        board_P1 = list(board_str_P1.replace("-", " "))
        board_P2 = list(board_str_P2.replace("-", " "))

        ## ERROR IN TEST only works when you can only display when it's your turn
        
        currentplayer = args.username 
        if currentplayer == player1: 
            board_enemy = display_enemy(board_P2)
            board_perso = board_P1
            display_both_boards(name, player1, player2, game_state, board_perso, board_enemy)
        elif currentplayer == player2: 
            board_enemy = display_enemy(board_P1)
            board_perso = board_P2
            display_both_boards(name, player1, player2, game_state, board_perso, board_enemy)
        else: 
            raise Exception("Player {} doesn't exist in the game {}".format(currentplayer, name))

    else:
        raise Exception("Game not found: {}".format(name))

def display_both_boards(name, player1, player2, game_state, board_current_player, board_enemy): 
    '''
    Function permitting to print the boards. Utility for show command. 
    '''
    
    print("GAME:     : {}".format(name))
    print("PLAYER 1  : {}".format(player1[:6]))
    print("PLAYER 2  : {}".format(player2[:6]))
    print("STATE     : {}".format(game_state))
    print("Enemy board")
    print("")
    print("   | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 ")
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" A | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[0], board_enemy[1], board_enemy[2], board_enemy[3], board_enemy[4], board_enemy[5], board_enemy[6], board_enemy[7], board_enemy[8], board_enemy[9]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" B | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[10], board_enemy[11], board_enemy[12], board_enemy[13], board_enemy[14], board_enemy[15], board_enemy[16], board_enemy[17], board_enemy[18], board_enemy[19]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" C | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[20], board_enemy[21], board_enemy[22], board_enemy[23], board_enemy[24], board_enemy[25], board_enemy[26], board_enemy[27], board_enemy[28], board_enemy[29]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" D | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[30], board_enemy[31], board_enemy[32], board_enemy[33], board_enemy[34], board_enemy[35], board_enemy[36], board_enemy[37], board_enemy[38], board_enemy[39]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" E | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[40], board_enemy[41], board_enemy[42], board_enemy[43], board_enemy[44], board_enemy[45], board_enemy[46], board_enemy[47], board_enemy[48], board_enemy[49]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" F | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[50], board_enemy[51], board_enemy[52], board_enemy[53], board_enemy[54], board_enemy[55], board_enemy[56], board_enemy[57], board_enemy[58], board_enemy[59]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" G | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[60], board_enemy[61], board_enemy[62], board_enemy[63], board_enemy[64], board_enemy[65], board_enemy[66], board_enemy[67], board_enemy[68], board_enemy[69]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" H | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[70], board_enemy[71], board_enemy[72], board_enemy[73], board_enemy[74], board_enemy[75], board_enemy[76], board_enemy[77], board_enemy[78], board_enemy[79]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" I | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[80], board_enemy[81], board_enemy[82], board_enemy[83], board_enemy[84], board_enemy[85], board_enemy[86], board_enemy[87], board_enemy[88], board_enemy[89]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" J | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[90], board_enemy[91], board_enemy[92], board_enemy[93], board_enemy[94], board_enemy[95], board_enemy[96], board_enemy[97], board_enemy[98], board_enemy[99]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print("")
    print("Your board")
    print("   | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 ")
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" A | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[0], board_current_player[1], board_current_player[2], board_current_player[3], board_current_player[4], board_current_player[5], board_current_player[6], board_current_player[7], board_current_player[8], board_current_player[9]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" B | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[10], board_current_player[11], board_current_player[12], board_current_player[13], board_current_player[14], board_current_player[15], board_current_player[16], board_current_player[17], board_current_player[18], board_current_player[19]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" C | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[20], board_current_player[21], board_current_player[22], board_current_player[23], board_current_player[24], board_current_player[25], board_current_player[26], board_current_player[27], board_current_player[28], board_current_player[29]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" D | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[30], board_current_player[31], board_current_player[32], board_current_player[33], board_current_player[34], board_current_player[35], board_current_player[36], board_current_player[37], board_current_player[38], board_current_player[39]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" E | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[40], board_current_player[41], board_current_player[42], board_current_player[43], board_current_player[44], board_current_player[45], board_current_player[46], board_current_player[47], board_current_player[48], board_current_player[49]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" F | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[50], board_current_player[51], board_current_player[52], board_current_player[53], board_current_player[54], board_current_player[55], board_current_player[56], board_current_player[57], board_current_player[58], board_current_player[59]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" G | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[60], board_current_player[61], board_current_player[62], board_current_player[63], board_current_player[64], board_current_player[65], board_current_player[66], board_current_player[67], board_current_player[68], board_current_player[69]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" H | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[70], board_current_player[71], board_current_player[72], board_current_player[73], board_current_player[74], board_current_player[75], board_current_player[76], board_current_player[77], board_current_player[78], board_current_player[79]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" I | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[80], board_current_player[81], board_current_player[82], board_current_player[83], board_current_player[84], board_current_player[85], board_current_player[86], board_current_player[87], board_current_player[88], board_current_player[89]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print(" J | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_current_player[90], board_current_player[91], board_current_player[92], board_current_player[93], board_current_player[94], board_current_player[95], board_current_player[96], board_current_player[97], board_current_player[98], board_current_player[99]))
    print("---|---|---|---|---|---|---|---|---|---|---")
    print("")

def display_enemy(board):
    ''' 
    This returns a board that shows where the 
    current player has shot on their enemy board. 
    '''
    board_disp = []
    for k in board :
        if k in ID_BOAT :
            board_disp.append(" ")
        else :
            board_disp.append(k)
    return board_disp


def do_create(args):
    '''
    This creates a new game
    '''
    name = args.name

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.create(
            name, wait=args.wait,
            auth_user=auth_user,
            auth_password=auth_password)
    else:
        response = client.create(
            name, auth_user=auth_user,
            auth_password=auth_password)

    print("Response: {}".format(response))


def do_shoot(args):
    '''
    Given the name of the game, the row and the column, this shoots on the enemy board at the given spot
    row is a character A-J
    col is an int 1-10 
    '''
    name = args.name
    column = args.col
    row = args.row 

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
    space = rownames[row]*10+column 

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.shoot(
            name, space, wait=args.wait,
            auth_user=auth_user,
            auth_password=auth_password)
    else:
        response = client.shoot(
            name, space,
            auth_user=auth_user,
            auth_password=auth_password)

    print("Response: {}".format(response))

def do_place(args):
    '''
    Give the name of the game, the column and the row, this places a given boat at the given spot
    '''
    name = args.name
    column = args.col
    row = args.row 
    boat = args.boat

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
    space = rownames[row]*10+column 

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.place(
            name, space, wait=args.wait,
            auth_user=auth_user,
            auth_password=auth_password)
    else:
        response = client.place(
            name, space,
            auth_user=auth_user,
            auth_password=auth_password)

    print("Response: {}".format(response))


def do_delete(args):
    '''
    This deletes the game that has the name you give as argument
    '''
    name = args.name

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.delete(
            name, wait=args.wait,
            auth_user=auth_user,
            auth_password=auth_password)
    else:
        response = client.delete(
            name, auth_user=auth_user,
            auth_password=auth_password)

    print("Response: {}".format(response))


def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    '''Entry point function for the client CLI.'''
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    verbose_level = 0

    setup_loggers(verbose_level=verbose_level)

    # Get the commands from cli args and call corresponding handlers
    if args.command == 'create':
        do_create(args)
    elif args.command == 'list':
        do_list(args)
    elif args.command == 'show':
        do_show(args)
    elif args.command == 'shoot':
        do_shoot(args)
    elif args.command == 'place':
        do_place(args)
    elif args.command == 'delete':
        do_delete(args)
    else:
        raise Exception("Invalid command: {}".format(args.command))


def main_wrapper():
    try:
        main()
    except Exception as err: ## 
        print("Error: {}".format(err), file=sys.stderr) ## 
        sys.exit(1) ## 
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

