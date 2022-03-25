from typing import List, Tuple

from database import ConfigureAsyncpg
from well_known_classes.enums import TransactionStatus, TransactionType
from well_known_classes.exceptions import NotEnoughMoneyException, \
    TransactionNotFoundException, InvalidTransactionException
from database import fetch_row_simple, execute_simple


async def is_user_exits(user_id: int, db: ConfigureAsyncpg.connection) -> bool:
    """ Проверить что юзер есть в бд """
    cmd = f"SELECT * FROM Users WHERE user_id='{user_id}';"
    result = await db.fetch(cmd)
    return bool(result)


async def get_transaction_info_sql(
        transaction_id: int, db: ConfigureAsyncpg.connection) -> Tuple[int, TransactionStatus]:
    """
    Получить из бд информацию по конкретной транзакции пользователя
    Возвращает: Tuple[transaction_id, TransactionStatus]
    Если транзакция не найдена, то выбрасывается ошибка TransactionNotFoundException
    Если не валидное значение статуса выбрасывается ошибка TypeError
    """
    cmd = f"SELECT user_id, status FROM Transactions WHERE transaction_id={transaction_id};"
    result = await db.fetch(cmd)
    if not result:
        raise TransactionNotFoundException(transaction_id)
    user_id = result[0].get('user_id')
    status = TransactionStatus(result[0].get('status'))
    return user_id, status


async def get_user_all_transactions_sql(
        user_id: int, db: ConfigureAsyncpg.connection) -> List[Tuple[int, TransactionStatus]]:
    """
    Получить списком из бд список информацию по транзакциям для конкретного пользователя
    Возвращает: List[Tuple[transaction_id, TransactionStatus]]
    """
    cmd = f"SELECT transaction_id, status FROM Transactions WHERE user_id='{user_id}'"
    results = await db.fetch(cmd)
    transactions = []
    for result in results:
        transaction_id = result.get('transaction_id')
        status = TransactionStatus(result.get('status'))
        transactions.append((transaction_id, status))
    return transactions


async def create_transaction_in_db(db: ConfigureAsyncpg.connection, user_id: int, amount: float,
                                   status: TransactionStatus, transaction_type: TransactionStatus) -> int:
    """ Создать запись о транзакции в БД и вернуть её id"""
    cmd = f"INSERT INTO Transactions (user_id, amount, status, type) " \
          f"VALUES ({user_id}, {amount}, '{status.value}', '{transaction_type.value}') " \
          f"RETURNING transaction_id;"
    result = await db.fetch(cmd)
    return result[0].get('transaction_id')


async def process_user_transaction(transaction_id: int, db: ConfigureAsyncpg) -> None:
    """ Выполнить ранее запрошенный платёж пользователя """
    transaction_cmd = f"SELECT user_id, amount, type FROM Transactions WHERE transaction_id={transaction_id}"
    transaction_cmd_result = await fetch_row_simple(transaction_cmd)
    user_id = transaction_cmd_result.get('user_id')
    amount = transaction_cmd_result.get('amount')
    transaction_type = transaction_cmd_result.get('type')
    balance_cmd = f"SELECT balance FROM Balance WHERE user_id={user_id}"
    balance_cmd_result = await fetch_row_simple(balance_cmd)
    balance = balance_cmd_result.get('balance')
    if transaction_type == TransactionType.TOP_UP.value:
        await __process_top_up_balance(balance, amount, transaction_id, user_id)
    elif transaction_type == TransactionType.PURCHASE.value:
        await __process_purchase(balance, amount, transaction_id, user_id)
    else:
        raise InvalidTransactionException(transaction_id, f"Unknown transaction type '{transaction_type}'")


async def __process_top_up_balance(balance: float, amount: float, transaction_id: int, user_id: int) -> None:
    top_upped_balance = balance + amount
    top_up_balance_cmd = f"UPDATE Balance SET balance={top_upped_balance} WHERE balance_id={user_id}"
    await execute_simple(top_up_balance_cmd)
    update_transaction_status_cmd = f"UPDATE Transactions SET status='{TransactionStatus.SUCCESS.value}' " \
                                    f"WHERE transaction_id={transaction_id}"
    await execute_simple(update_transaction_status_cmd)


async def __process_purchase(balance: float, amount: float, transaction_id: int, user_id: int) -> None:
    sum_after_debit = balance - amount
    if sum_after_debit >= 0:
        debit_money_cmd = f"UPDATE Balance SET balance={sum_after_debit} WHERE balance_id={user_id}"
        await execute_simple(debit_money_cmd)
        update_transaction_status_cmd = f"UPDATE Transactions SET status='{TransactionStatus.SUCCESS.value}' " \
                                        f"WHERE transaction_id={transaction_id}"
        await execute_simple(update_transaction_status_cmd)
    else:
        update_transaction_status_cmd = f"UPDATE Transactions SET status='{TransactionStatus.FAILURE.value}' " \
                                        f"WHERE transaction_id={transaction_id}"
        await execute_simple(update_transaction_status_cmd)
        raise NotEnoughMoneyException(user_id, transaction_id)
