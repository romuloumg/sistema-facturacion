# app/services/product_service.py
from ..models.product_model import get_product, update_stock_set, update_stock_delta
from ..models.sale_model import with_transaction

class ProductError(Exception): pass

@with_transaction
def set_stock(conn, cursor, id_producto: int, new_stock: int):
    if new_stock < 0:
        raise ProductError("El stock no puede ser negativo.")
    p = get_product(id_producto)
    if not p:
        raise ProductError("Producto no existe.")
    update_stock_set(cursor, id_producto, new_stock)
    return {"id_producto": id_producto, "stock": new_stock}

@with_transaction
def change_stock(conn, cursor, id_producto: int, delta: int):
    p = get_product(id_producto)
    if not p:
        raise ProductError("Producto no existe.")
    update_stock_delta(cursor, id_producto, delta)
    # leer stock final
    p2 = get_product(id_producto)
    return {"id_producto": id_producto, "stock": p2["stock"]}
