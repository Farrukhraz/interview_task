from collections import OrderedDict
from typing import Dict, Tuple, Union


class UserTransactionsQueue:
    def __init__(self):
        self.user_transactions: Dict[int, Dict[int, str]] = dict()

    def add_transaction(self, user_id: int, transaction_id: int) -> None:
        if not self.user_transactions.get(user_id):
            self.user_transactions[user_id] = dict()
        self.user_transactions[user_id][transaction_id] = ''

    def remove_transaction(self, user_id: int, transaction_id: int) -> None:
        try:
            transactions = self.user_transactions[user_id]
        except KeyError:
            raise KeyError(f"Requested {user_id=} does not exists!")
        if transaction_id in transactions:
            del transactions[transaction_id]

    def __repr__(self):
        return str(self.user_transactions)


class CommonTransactionsQueue:
    def __init__(self):
        self.transactions: OrderedDict[int, int] = OrderedDict()

    # FIFO
    def pop_transaction(self) -> Union[Tuple[int, int], None]:
        """ На выходе получаем либо (transaction_id, user_id), либо None """
        if not self.transactions:
            return
        return self.transactions.popitem(last=False)

    def add_transaction(self, transaction_id: int, user_id: int) -> None:
        self.transactions[transaction_id] = user_id

    def get_transaction_user(self, transaction_id: int) -> Union[int, None]:
        """ Получить user_id конкретной транзакции, если она есть в очереди. Иначе None """
        return self.transactions.get(transaction_id)

    def __repr__(self):
        return str(self.transactions)
