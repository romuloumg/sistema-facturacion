from decimal import Decimal
from ..db import get_conn

def create_sale_header(id_usuario, cursor):
    cursor.execute("INSERT INTO ventas (id_usuario, total) VALUES (%s, 0)", (id_usuario,))
    return cursor.lastrowid

def insert_sale_detail(cursor, id_venta, p, cantidad):
    precio = p["precio"]                       # DECIMAL de MySQL
    subtotal = precio * Decimal(cantidad)
    cursor.execute("""
        INSERT INTO venta_detalle
        (id_venta, id_producto, nombre_producto, descripcion, cantidad, precio_unitario, subtotal)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (id_venta, p["id_producto"], p["nombre"], p["descripcion"], cantidad, precio, subtotal))
    return subtotal

def update_sale_total(cursor, id_venta, total):
    cursor.execute("UPDATE ventas SET total=%s WHERE id_venta=%s", (total, id_venta))

def with_transaction(fn):
    """
    Decorador simple para ejecutar lógica de servicio dentro de una transacción.
    Pasa (conn, cursor) al callable y hace commit/rollback.
    """
    def wrapper(*args, **kwargs):
        conn = get_conn()
        try:
            cur = conn.cursor(dictionary=True)
            result = fn(conn, cur, *args, **kwargs)
            conn.commit()
            return result
        except Exception:
            try: conn.rollback()
            except: pass
            raise
        finally:
            try: cur.close(); conn.close()
            except: pass
    return wrapper
