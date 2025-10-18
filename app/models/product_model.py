from ..db import get_conn

def list_products():
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT id_producto, nombre, descripcion, precio, stock
                       FROM productos ORDER BY nombre""")
        rows = cur.fetchall()
        return rows
    finally:
        try: cur.close(); conn.close()
        except: pass

def get_product_for_update(id_producto):
    """
    Selecciona el producto con FOR UPDATE (para validar stock dentro de una venta).
    Devuelve dict o None.
    """
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT id_producto, nombre, descripcion, precio, stock
                       FROM productos WHERE id_producto=%s FOR UPDATE""", (id_producto,))
        return cur.fetchone()
    finally:
        try: cur.close(); conn.close()
        except: pass

def discount_stock(id_producto, cantidad, cursor):
    """
    Descuenta stock usando el cursor ACTUAL de la transacción (no abre conexión propia).
    """
    cursor.execute("UPDATE productos SET stock = stock - %s WHERE id_producto = %s",
                   (cantidad, id_producto))


from ..db import get_conn

def get_product(id_producto):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT id_producto, nombre, descripcion, precio, stock
                       FROM productos WHERE id_producto=%s""", (id_producto,))
        return cur.fetchone()
    finally:
        try: cur.close(); conn.close()
        except: pass

def update_stock_set(cursor, id_producto: int, new_stock: int):
    cursor.execute("UPDATE productos SET stock=%s WHERE id_producto=%s",
                   (new_stock, id_producto))

def update_stock_delta(cursor, id_producto: int, delta: int):
    # evita negativos
    cursor.execute("""
        UPDATE productos
        SET stock = GREATEST(0, stock + %s)
        WHERE id_producto=%s
    """, (delta, id_producto))
