from pydantic import BaseModel, validator


class PurchaseRequest(BaseModel):
    user_id: int
    amount: float

    @validator('amount')
    def check_amount(cls, value):
        return round(value, 2)


class BalanceTopUpRequest(BaseModel):
    user_id: int
    amount: float

    @validator('amount')
    def check_amount(cls, value):
        return round(value, 2)
