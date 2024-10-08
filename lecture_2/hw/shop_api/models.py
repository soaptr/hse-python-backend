from pydantic import BaseModel, confloat, conint
from typing import List, Optional


class Item(BaseModel):
    id: int
    name: str
    price: confloat(gt=0)
    deleted: bool = False


class CartItem(BaseModel):
    id: int
    name: str
    quantity: conint(gt=0)
    available: bool = True


class Cart(BaseModel):
    id: int
    items: List[CartItem] = []
    price: float = 0.0


class ItemPost(BaseModel):
    name: str
    price: confloat(gt=0)


class UpdateItem(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    model_config = {
        'extra': 'forbid'
    }
