from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict
from .models import Cart, CartItem, Item, ItemPost, UpdateItem


app = FastAPI(title="Shop API")


# Хранилища данных
_items: Dict[int, Item] = {}
_carts: Dict[int, Cart] = {}
_item_id = 0
_cart_id = 0


# --- Ресурсы для Item ---

@app.post("/item", status_code=status.HTTP_201_CREATED)
def create_item(item: ItemPost):
    global _item_id
    _item_id += 1
    new_item = Item(id=_item_id, name=item.name, price=item.price)
    _items[_item_id] = new_item
    return JSONResponse(
        content={"id": _item_id, "name": new_item.name, "price": new_item.price},
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"/item/{_item_id}"},
    )


@app.get("/item/{id}", status_code=status.HTTP_200_OK)
def get_item(id: int):
    if id not in _items.keys() or _items[id].deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    item = _items[id]
    return {"id": item.id, "name": item.name, "price": item.price}


@app.put("/item/{id}")
def update_item(id: int, item: ItemPost):
    if id not in _items.keys() or _items[id].deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    _items[id].name = item.name
    _items[id].price = item.price
    return {"id": _items[id].id, "name": _items[id].name, "price": _items[id].price}


@app.patch("/item/{id}")
def patch_item(id: int, new_item: UpdateItem):
    if id not in _items.keys():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    item = _items[id]
    if item.deleted:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="Item is deleted")

    if new_item.name is not None:
        item.name = new_item.name
    if new_item.price is not None:
        item.price = new_item.price

    return {"id": item.id, "name": item.name, "price": item.price}


@app.delete("/item/{id}")
def delete_item(id: int):
    if id not in _items.keys():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    _items[id].deleted= True
    return {"message": "Item deleted"}


@app.get("/item")
def get_items(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    min_price: Optional[float] = Query(None, ge=0.0),
    max_price: Optional[float] = Query(None, ge=0.0),
    show_deleted: bool = Query(False)
):
    filtered_items = [
        item for item in _items.values()
        if (min_price is None or item.price >= min_price) and
           (max_price is None or item.price <= max_price) and
           (show_deleted or not item.deleted)
    ]

    # Применение offset и limit для пагинации
    start = offset
    end = offset + limit
    return filtered_items[start:end]


# --- Ресурсы для Cart ---

@app.post("/cart", status_code=status.HTTP_201_CREATED)
def create_cart():
    global _cart_id
    _cart_id += 1
    _carts[_cart_id] = Cart(id=_cart_id)

    return JSONResponse(
        content={"id": _cart_id},
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"/cart/{_cart_id}"},
    )


@app.get("/cart/{id}")
def get_cart(id: int):
    if id not in _carts.keys():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    return _carts[id]


@app.post("/cart/{cart_id}/add/{item_id}", status_code=status.HTTP_200_OK)
def add_item_to_cart(cart_id: int, item_id: int):
    if cart_id not in _carts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    if item_id not in _items.keys() or _items[item_id].deleted:
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
    filtered_carts = [
        cart for cart in _carts.values()
        if (min_price is None or cart.price >= min_price) and
           (max_price is None or cart.price <= max_price) and
           (min_quantity is None or sum(item.quantity for item in cart.items) >= min_quantity) and
           (max_quantity is None or sum(item.quantity for item in cart.items) <= max_quantity)
    ]

    # Применение offset и limit для пагинации
    start = offset
    end = offset + limit
    return filtered_carts[start:end]
