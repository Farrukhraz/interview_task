from pydantic import BaseModel
from typing import List, Optional

from .enums import TransactionStatus


class TransactionInfo(BaseModel):
    transaction_id: int
    status: TransactionStatus


class PurchaseResponse(BaseModel):
    user_id: int
    transaction_id: int
    status: TransactionStatus


class BalanceTopUpResponse(BaseModel):
    user_id: int
    transaction_id: int
    status: TransactionStatus


class TransactionInfoResponse(BaseModel):
    user_id: int
    transaction_id: int
    status: TransactionStatus
    message: Optional[str]


class UserTransactionsInfoResponse(BaseModel):
    user_id: int
    transactions: List[TransactionInfo]
    message: Optional[str]
