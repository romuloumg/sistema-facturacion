# app/services/sale_service.py
from typing import List, Dict
from decimal import Decimal
from ..models.product_model import get_product_for_update, discount_stock
from ..models.sale_model import create_sale_header, insert_sale_detail, update_sale_total, with_transaction

class SaleError(Exception):
    pass

@with_transaction
def create_sale(conn, cursor, id_usuario: int, items: List[Dict]):
    if not id_usuario or not items or not isinstance(items, list):
        raise SaleError("Faltan datos: id_usuario e items[]")

    id_venta = create_sale_header(id_usuario, cursor)
    total = Decimal("0.00")
    lineas_validas = 0

    for it in items:
        try:
            prod_id = int(it.get("id_producto", 0))
            cant = int(it.get("cantidad", 0))
        except Exception:
            continue
        if prod_id <= 0 or cant <= 0:
            continue

        p = get_product_for_update(prod_id)
        if not p:
            raise SaleError(f"Producto {prod_id} no existe")
        if p["stock"] < cant:
            raise SaleError(f"Stock insuficiente para {p['nombre']} (disponible {p['stock']})")

        subtotal = insert_sale_detail(cursor, id_venta, p, cant)
        discount_stock(prod_id, cant, cursor)
        total += subtotal
        lineas_validas += 1

    if lineas_validas == 0:
        raise SaleError("No se enviaron cantidades válidas")

    update_sale_total(cursor, id_venta, total)
    return {"id_venta": id_venta, "total": float(total)}
