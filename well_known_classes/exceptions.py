
class TransactionBaseException(Exception):
    def __init__(self, message: str = ''):
        self.message = message


class NotEnoughMoneyException(TransactionBaseException):
    def __init__(self, user_id: int, transaction_id: int, message: str = ''):
        self.message = message or f"Not enough money to process {user_id=} {transaction_id=}"
        self.user_id = user_id
        self.transaction_id = transaction_id


class TransactionNotFoundException(TransactionBaseException):
    def __init__(self, transaction_id: int, message: str = ''):
        self.message = message or f"Transaction '{transaction_id}' is not found"
        self.transaction_id = transaction_id


class InvalidTransactionException(TransactionBaseException):
    def __init__(self, transaction_id: int, message: str = ''):
        self.message = message or f"Invalid transaction '{transaction_id}'"
        self.transaction_id = transaction_id
