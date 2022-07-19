import hashlib

from sawtooth_sdk.processor.exceptions import InternalError


BATTLESHIP_NAMESPACE = hashlib.sha512('battleship'.encode("utf-8")).hexdigest()[0:6]


def _make_battleship_address(name):
    return BATTLESHIP_NAMESPACE + \
        hashlib.sha512(name.encode('utf-8')).hexdigest()[:64]


class Game:
    def __init__(self, name, board_P1, board_P2, state, player1, player2, boat_cases, to_place):
        self.name = name
        self.board_P1 = board_P1
        self.board_P2 = board_P2
        self.state = state
        self.player1 = player1
        self.player2 = player2
        self.boat_cases = boat_cases
        self.to_place = to_place
        

class BattleshipState:

    TIMEOUT = 3

    def __init__(self, context):
        """Constructor.

        Args:
            context (sawtooth_sdk.processor.context.Context): Access to
                validator state from within the transaction processor.
        """

        self._context = context
        self._address_cache = {}

    def delete_game(self, game_name):
        """Delete the Game named game_name from state.

        Args:
            game_name (str): The name.

        Raises:
            KeyError: The Game with game_name does not exist.
        """

        games = self._load_games(game_name=game_name)
        
        del games[game_name]
        if games:
            self._store_game(game_name, games=games)
        else:
            self._delete_game(game_name)

    def set_game(self, game_name, game):
        """Store the game in the validator state.

        Args:
            game_name (str): The name.
            game (Game): The information specifying the current game.
        """

        games = self._load_games(game_name=game_name)

        games[game_name] = game

        self._store_game(game_name, games=games)

    def get_game(self, game_name):
        """Get the game associated with game_name.

        Args:
            game_name (str): The name.

        Returns:
            (Game): All the information specifying a game.
        """
        
        return self._load_games(game_name=game_name).get(game_name)

    def _store_game(self, game_name, games):
        address = _make_battleship_address(game_name)

        state_data = self._serialize(games)

        self._address_cache[address] = state_data

        self._context.set_state(
            {address: state_data},
            timeout=self.TIMEOUT)

    def _delete_game(self, game_name):
        address = _make_battleship_address(game_name)

        self._context.delete_state(
            [address],
            timeout=self.TIMEOUT)

        self._address_cache[address] = None

    def _load_games(self, game_name):
        address = _make_battleship_address(game_name)

        if address in self._address_cache:
            if self._address_cache[address]:
                serialized_games = self._address_cache[address]
                games = self._deserialize(serialized_games)
            else:
                games = {}
        else:
            state_entries = self._context.get_state(
                [address],
                timeout=self.TIMEOUT)
            if state_entries:

                self._address_cache[address] = state_entries[0].data

                games = self._deserialize(data=state_entries[0].data)

            else:
                self._address_cache[address] = None
                games = {}

        return games

    def _deserialize(self, data):
        """Take bytes stored in state and deserialize them into Python
        Game objects.

        Args:
            data (bytes): The UTF-8 encoded string stored in state.

        Returns:
            (dict): game name (str) keys, Game values.
        """

        games = {}
        try:
            for game in data.decode().split("|"):
                name, board_P1, board_P2, state, player1, player2, boat_cases, to_place = game.split(",")

                games[name] = Game(name, board_P1, board_P2, state, player1, player2, boat_cases, to_place)
        except ValueError as e:
            raise InternalError("Failed to deserialize game data") from e

        return games

    def _serialize(self, games):
        """Takes a dict of game objects and serializes them into bytes.

        Args:
            games (dict): game name (str) keys, Game values.

        Returns:
            (bytes): The UTF-8 encoded string stored in state.
        """

        game_strs = []
        for name, g in games.items():
            game_str = ",".join(
                [name, g.board_P1, g.board_P2, g.state, g.player1, g.player2, g.boat_cases, g.to_place])
            game_strs.append(game_str)

        return "|".join(sorted(game_strs)).encode()