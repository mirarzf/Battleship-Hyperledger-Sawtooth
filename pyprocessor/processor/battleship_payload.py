from sawtooth_sdk.processor.exceptions import InvalidTransaction


class BattleshipPayload:

    def __init__(self, payload):
        try:
            # The payload is csv utf-8 encoded string
            name, action, space, boat, direction, player1, player2 = payload.decode().split(",")
        except ValueError as e:
            raise InvalidTransaction("Invalid payload serialization") from e

        if not name:
            raise InvalidTransaction('Name is required')

        if '|' in name:
            raise InvalidTransaction('Name cannot contain "|"')

        if not action:
            raise InvalidTransaction('Action is required')

        if action not in ('list', 'create', 'show', 'place', 'shoot', 'delete'):
            raise InvalidTransaction('Invalid action: {}'.format(action))

        if action == 'shoot' or action == 'place':
            space = int(space)
            try:
                ## modified: case name for position as an index 
                if int(space) not in range(1, 100):
                    raise InvalidTransaction(
                        "Space must be an integer from 1 to 100")
            except ValueError:
                raise InvalidTransaction(
                    'Space must be an integer from 1 to 100') from ValueError

        self._name = name
        self._action = action
        self._space = space
        self._boat = boat
        self._direction = direction
        self._player1 = player1 
        self._player2 = player2 

    @staticmethod
    def from_bytes(payload):
        return BattleshipPayload(payload=payload)

    @property
    def name(self):
        return self._name

    @property
    def action(self):
        return self._action

    @property
    def space(self):
        return self._space

    @property
    def boat(self):
        return self._boat

    @property
    def direction(self):
        return self._direction

    @property
    def player1(self):
        return self._player1

    @property
    def player2(self):
        return self._player2