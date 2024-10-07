from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Shop API")


# Модели данных
class ItemCreate(BaseModel):
    name: str
    price: float


class ItemResponse(ItemCreate):
    id: int
    deleted: bool


class CartResponse(BaseModel):
    id: int
    items: List[dict]
    price: float


# Хранилища данных (заменяем БД на память)
items = {}
carts = {}
next_item_id = 1
next_cart_id = 1


# --- Ресурсы для Item ---

@app.post("/item", response_model=int, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate):
    global next_item_id
    new_item = {
        "id": next_item_id,
        "name": item.name,
        "price": item.price,
        "deleted": False
    }
    items[next_item_id] = new_item
    next_item_id += 1
    return new_item["id"]


@app.get("/item/{id}", response_model=ItemResponse)
def get_item(id: int):
    if id not in items or items[id]["deleted"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return items[id]


@app.put("/item/{id}", response_model=ItemResponse)
def update_item(id: int, item: ItemCreate):
    if id not in items or items[id]["deleted"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    items[id]["name"] = item.name
    items[id]["price"] = item.price
    return items[id]


@app.patch("/item/{id}", response_model=ItemResponse)
def patch_item(id: int, item: dict):
    if id not in items or items[id]["deleted"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    allowed_fields = {"name", "price"}
    for key, value in item.items():
        if key in allowed_fields:
            items[id][key] = value
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Field {key} is not allowed")

    return items[id]


@app.delete("/item/{id}")
def delete_item(id: int):
    if id not in items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    items[id]["deleted"] = True
    return {"message": "Item deleted"}


# --- Ресурсы для Cart ---

@app.post("/cart", response_model=int, status_code=status.HTTP_201_CREATED)
def create_cart():
    global next_cart_id
    new_cart = {
        "id": next_cart_id,
        "items": [],
        "price": 0.0
    }
    carts[next_cart_id] = new_cart
    next_cart_id += 1
    return new_cart["id"]


@app.get("/cart/{id}", response_model=CartResponse)
def get_cart(id: int):
    if id not in carts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    return carts[id]


@app.post("/cart/{cart_id}/add/{item_id}", status_code=status.HTTP_200_OK)
def add_item_to_cart(cart_id: int, item_id: int):
    if cart_id not in carts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    if item_id not in items or items[item_id]["deleted"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or deleted")

    cart = carts[cart_id]
    item_in_cart = next((i for i in cart["items"] if i["id"] == item_id), None)

    if item_in_cart:
        item_in_cart["quantity"] += 1
    else:
        new_cart_item = {
            "id": item_id,
            "name": items[item_id]["name"],
            "quantity": 1,
            "available": not items[item_id]["deleted"]
        }
        cart["items"].append(new_cart_item)

    # Увеличиваем сумму корзины на стоимость добавленного товара
    cart["price"] += items[item_id]["price"]
    return {"message": "Item added to cart"}


@app.get("/cart", response_model=List[CartResponse])
def get_carts(
        offset: int = Query(0, ge=0),
        limit: int = Query(10, gt=0),
        min_price: Optional[float] = Query(None, ge=0.0),
        max_price: Optional[float] = Query(None, ge=0.0),
        min_quantity: Optional[int] = Query(None, ge=0),
        max_quantity: Optional[int] = Query(None, ge=0)
):
    filtered_carts = list(carts.values())

    # Фильтрация по цене
    if min_price is not None:
        filtered_carts = [cart for cart in filtered_carts if cart["price"] >= min_price]
    if max_price is not None:
        filtered_carts = [cart for cart in filtered_carts if cart["price"] <= max_price]

    # Фильтрация по количеству товаров в корзине
    if min_quantity is not None:
        filtered_carts = [cart for cart in filtered_carts if
                          sum(item["quantity"] for item in cart["items"]) >= min_quantity]
    if max_quantity is not None:
        filtered_carts = [cart for cart in filtered_carts if
                          sum(item["quantity"] for item in cart["items"]) <= max_quantity]

    # Применение offset и limit для пагинации
    start = offset
    end = offset + limit
    return filtered_carts[start:end]
