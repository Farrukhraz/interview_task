from database import ConfigureAsyncpg
from database.sql import create_transaction_in_db
from pq.queues import CommonTransactionsQueue, UserTransactionsQueue
from well_known_classes import TransactionStatus


async def create_user_transaction(db: ConfigureAsyncpg.connection, user_id: int, amount: float,
                                  status: TransactionStatus, transaction_type,
                                  common_tq: CommonTransactionsQueue, user_tq: UserTransactionsQueue) -> int:
    transaction_id = await create_transaction_in_db(db, user_id, amount, status, transaction_type)
    user_tq.add_transaction(user_id, transaction_id)
    common_tq.add_transaction(transaction_id, user_id)
    return transaction_id
