__author__ = 'salas'


class NotLoginException(Exception):
    pass


class UserPayload:

    def __init__(self, account, password):
        self.account = account
        self.password = password

    def to_dict(self):
        return {
            'bor_id': self.account,
            'bor_verification': self.password,
            'func': 'login',
            'ssl_flag': 'Y',
        }