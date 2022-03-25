import asyncio

from threading import Thread
from time import sleep

from database import ConfigureAsyncpg
from database.sql import process_user_transaction
from well_known_classes.exceptions import NotEnoughMoneyException
from .queues import CommonTransactionsQueue, UserTransactionsQueue


class TransactionsWorker:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.init_event_loop()

    def init_event_loop(self):
        asyncio.set_event_loop(self.loop)

    def run(self, db: ConfigureAsyncpg, common_tq: CommonTransactionsQueue, user_tq: UserTransactionsQueue):
        while True:
            transaction_info = common_tq.pop_transaction()
            if not transaction_info:
                sleep(1)
                continue
            transaction_id, user_id = transaction_info
            try:
                self.handle_transaction(db, transaction_id)
            except NotEnoughMoneyException:
                # log me please
                pass
            finally:
                user_tq.remove_transaction(user_id, transaction_id)

    def handle_transaction(self, db: ConfigureAsyncpg.connection, transaction_id: int) -> None:
        """
        Обрабатывает одну транзакцию за один промежуток времени
        Если у пользователя недостаточно денег для выполнения транзакции,
        то выбрасывается ошибка NotEnoughMoneyException
        """
        self.loop.run_until_complete(process_user_transaction(transaction_id, db))


def start_workers(*args, **kwargs) -> None:
    worker = TransactionsWorker()
    thread = Thread(target=worker.run, args=args, kwargs=kwargs)
    thread.start()
