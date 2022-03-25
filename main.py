from fastapi import FastAPI, Depends, HTTPException

from database import ConfigureAsyncpg, get_dsn
from database.sql import get_transaction_info_sql, get_user_all_transactions_sql, is_user_exits
from database.utils import create_user_transaction
from pq.queues import CommonTransactionsQueue, UserTransactionsQueue
from pq.workers import start_workers
from well_known_classes import TransactionStatus, TransactionType
from well_known_classes.request_models import BalanceTopUpRequest, PurchaseRequest
from well_known_classes.response_models import PurchaseResponse, TransactionInfo, TransactionInfoResponse, \
    UserTransactionsInfoResponse, BalanceTopUpResponse
from well_known_classes.exceptions import TransactionNotFoundException


app = FastAPI()
db = ConfigureAsyncpg(app, get_dsn())


@db.on_init
async def initialization(conn):
    await conn.execute('SELECT 1')


common_tq = CommonTransactionsQueue()
user_tq = UserTransactionsQueue()
start_workers(db=db, common_tq=common_tq, user_tq=user_tq)


@app.put("/api/v1/shop/purchase/", response_model=PurchaseResponse)
async def make_purchase(item: PurchaseRequest, _db: Depends = Depends(db.connection)):
    user_exits = await is_user_exits(item.user_id, _db)
    if not user_exits:
        raise HTTPException(status_code=404, detail=f"User with user_id='{item.user_id}' is not found")
    if item.amount <= 0:
        raise HTTPException(status_code=400, detail=f"Incorrect 'amount' field value. "
                                                    f"'amount' value can't be negative number or zero")
    status = TransactionStatus.PENDING
    transaction_type = TransactionType.PURCHASE
    transaction_id = await create_user_transaction(_db, item.user_id, item.amount,
                                                   status, transaction_type, common_tq, user_tq)
    return PurchaseResponse(user_id=item.user_id, transaction_id=transaction_id, status=status)


@app.put("/api/v1/balance/top_up/", response_model=BalanceTopUpResponse)
async def top_up_balance(item: BalanceTopUpRequest, _db: Depends = Depends(db.connection)):
    user_exits = await is_user_exits(item.user_id, _db)
    if not user_exits:
        raise HTTPException(status_code=404, detail=f"User with user_id='{item.user_id}' is not found")
    if item.amount <= 0:
        raise HTTPException(status_code=400, detail=f"Incorrect 'amount' field value. "
                                                    f"'amount' value can't be negative number or zero")
    status = TransactionStatus.PENDING
    transaction_type = TransactionType.TOP_UP
    transaction_id = await create_user_transaction(_db, item.user_id, item.amount,
                                                   status, transaction_type, common_tq, user_tq)
    return BalanceTopUpResponse(user_id=item.user_id, transaction_id=transaction_id, status=status)


@app.get("/api/v1/transactions/{transaction_id}/", response_model=TransactionInfoResponse)
async def get_transaction_info(transaction_id: str, _db: Depends = Depends(db.connection)):
    try:
        transaction_id = int(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Incorrect 'transaction_id' value. Expected 'int'")
    user_id = common_tq.get_transaction_user(transaction_id)
    if user_id:     # Значит транзакция ещё не обработана
        return TransactionInfoResponse(user_id=user_id, transaction_id=transaction_id, status=TransactionStatus.PENDING)
    else:
        try:
            user_id, status = await get_transaction_info_sql(transaction_id, _db)
            return TransactionInfoResponse(user_id=user_id, transaction_id=transaction_id, status=status)
        except TypeError:
            raise HTTPException(status_code=500, detail="Unknown server error. "
                                                        "Error: Unknown transaction status is received")
        except TransactionNotFoundException:
            raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' is not found")


@app.get("/api/v1/transactions/user/{user_id}/", response_model=UserTransactionsInfoResponse)
async def get_user_transactions_info(user_id: str, _db: Depends = Depends(db.connection)):
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Incorrect 'user_id' value. Expected 'int'")
    if not await is_user_exits(user_id, _db):
        raise HTTPException(status_code=404, detail=f"User with user_id='{user_id}' is not found")
    user_transactions = await get_user_all_transactions_sql(user_id, _db)
    transactions = []
    for transaction_id, status in user_transactions:
        transactions.append(TransactionInfo(transaction_id=transaction_id, status=status))
    return UserTransactionsInfoResponse(user_id=user_id, transactions=transactions)
