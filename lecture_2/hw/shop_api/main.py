from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import List, Optional, Iterable
from models import Cart, CartItem, Item, ItemPost


app = FastAPI(title="Shop API")


# Хранилища данных
_items = dict[int, Item]()
_carts = dict[int, Cart]()


def id_generator() -> Iterable[int]:
    id = 0
    while True:
        yield id
        id += 1


_items_id_generator = id_generator()
_carts_id_generator = id_generator()


# --- Ресурсы для Item ---

@app.post("/item", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemPost):
    item_id = next(_items_id_generator)
    new_item = Item(id=item_id, name=item.name, price=item.price)
    _items[item_id] = new_item
    return JSONResponse(
        content={"id": item_id, "name": new_item.name, "price": new_item.price},
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"/item/{item_id}"},
    )


@app.get("/item/{id}", status_code=status.HTTP_200_OK)
def get_item(id: int):
    if id not in _items or _items[id]["deleted"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return _items[id]


@app.put("/item/{id}")
def update_item(id: int, item: ItemPost):
    if id not in _items or _items[id]["deleted"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    _items[id]["name"] = item.name
    _items[id]["price"] = item.price
    return _items[id]


@app.patch("/item/{id}")
def patch_item(id: int, item: dict):
    if id not in _items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if _items[id]["deleted"]:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="Item is deleted")

    allowed_fields = {"name", "price"}
    for key, value in item.items():
        if key in allowed_fields:
            _items[id][key] = value
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Field {key} is not allowed")

    return _items[id]


@app.delete("/item/{id}")
def delete_item(id: int):
    if id not in _items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    _items[id]["deleted"] = True
    return {"message": "Item deleted"}


@app.get("/item")
def get_items(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    min_price: Optional[float] = Query(None, ge=0.0),
    max_price: Optional[float] = Query(None, ge=0.0),
    show_deleted: bool = Query(False)
):
    filtered_items = [item for item in _items if not item["deleted"] or show_deleted]

    # Фильтрация по цене
    if min_price is not None:
        filtered_items = [item for item in filtered_items if item["price"] >= min_price]
    if max_price is not None:
        filtered_items = [item for item in filtered_items if item["price"] <= max_price]

    # Применение offset и limit для пагинации
    start = offset
    end = offset + limit
    return filtered_items[start:end]


# --- Ресурсы для Cart ---

@app.post("/cart", status_code=status.HTTP_201_CREATED)
def create_cart():
    cart_id = next(_carts_id_generator)
    _carts[cart_id] = Cart(id=cart_id)

    return JSONResponse(
        content={"id": cart_id},
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"/cart/{cart_id}"},
    )


@app.get("/cart/{id}")
def get_cart(id: int):
    if id not in _carts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    return _carts[id]


@app.post("/cart/{cart_id}/add/{item_id}", status_code=status.HTTP_200_OK)
def add_item_to_cart(cart_id: int, item_id: int):
    if cart_id not in _carts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    if item_id not in _items or _items[item_id]["deleted"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or deleted")

    item = _items[item_id]
    cart = _carts[cart_id]
    for cart_item in cart.items:
        if cart_item.id == item.id:
            cart_item.quantity += 1
            break
    else:
        cart.items.append(CartItem(id=item.id, name=item.name, quantity=1))
    # Увеличиваем сумму корзины на стоимость добавленного товара
    cart.price += item.price
    return cart


@app.get("/cart")
def get_carts(
        offset: int = Query(0, ge=0),
        limit: int = Query(10, gt=0),
        min_price: Optional[float] = Query(None, ge=0.0),
        max_price: Optional[float] = Query(None, ge=0.0),
        min_quantity: Optional[int] = Query(None, ge=0),
        max_quantity: Optional[int] = Query(None, ge=0)
):
    filtered_carts = list(_carts.values())

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
