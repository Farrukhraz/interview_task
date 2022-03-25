from enum import Enum


class TransactionStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


class TransactionType(Enum):
    TOP_UP = "top_up"
    PURCHASE = "purchase"
