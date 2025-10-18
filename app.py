import os
from decimal import Decimal
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

# ---------------------------
# App & CORS
# ---------------------------
app = Flask(__name__)

# --- CORS universal (preflight + headers en todas las respuestas) ---
ALLOWED_ORIGINS = {"http://127.0.0.1:5500", "http://localhost:5500"}

@app.before_request
def _cors_preflight():
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        resp = app.make_response(("", 204))
        if origin in ALLOWED_ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id, X-Role"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PATCH,DELETE,OPTIONS"
        return resp  # ← corta aquí el preflight

@app.after_request
def _cors_headers(resp):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id, X-Role"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PATCH,DELETE,OPTIONS"
    return resp


CORS(
    app,
    resources={r"/api/*": {"origins": ["http://127.0.0.1:5500", "http://localhost:5500"]}},
    supports_credentials=False,
    allow_headers=["Content-Type", "X-User-Id", "X-Role"],
    expose_headers=["Content-Type"],
)

# ---------------------------
# DB
# ---------------------------
DB_CFG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "Sistema_Facturacion"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

def get_conn():
    return mysql.connector.connect(**DB_CFG)

def dec(v):
    return float(v) if isinstance(v, Decimal) else v

# ---------------------------
# Auth / Roles
# ---------------------------
VALID_ROLES = {"admin", "vendedor", "supervisor", "bodeguero"}

def get_request_user():
    """
    Para pruebas:
      - Enviar X-User-Id para leer usuario real desde DB
      - O enviar X-Role: admin|vendedor|supervisor|bodeguero
    """
    uid = request.headers.get("X-User-Id")
    role_hdr = (request.headers.get("X-Role") or "").strip().lower()

    if uid:
        try:
            conn = get_conn()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id_usuario, usuario, rol FROM usuarios WHERE id_usuario=%s",
                (uid,),
            )
            u = cur.fetchone()
            if u and (u["rol"] or "").lower() in VALID_ROLES:
                u["rol"] = u["rol"].lower()
                return u
            return None
        finally:
            try:
                cur.close(); conn.close()
            except:
                pass

    if role_hdr and role_hdr in VALID_ROLES:
        return {"id_usuario": None, "usuario": "(header)", "rol": role_hdr}

    return None

def role_required(*roles):
    roles = {r.lower() for r in roles}
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            u = get_request_user()
            if not u:
                return jsonify({"error": "No autenticado"}), 401
            # admin siempre puede
            if u["rol"] != "admin" and u["rol"] not in roles:
                return jsonify({"error": "No autorizado", "rol": u["rol"]}), 403
            request.user = u
            return fn(*args, **kwargs)
        return wrapper
    return deco

# ---------------------------
# Endpoints
# ---------------------------
@app.route("/")
def alive():
    return "Backend Flask funcionando ✅"

# Productos: lectura (vendedor, supervisor, bodeguero, admin)
@app.route("/api/productos", methods=["GET", "OPTIONS"])
@role_required("vendedor", "supervisor", "bodeguero", "admin")
def api_productos():
    if request.method == "OPTIONS":
        return ("", 204)
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id_producto, nombre, descripcion, precio, stock
            FROM productos
            ORDER BY nombre
        """)
        rows = cur.fetchall()
        for r in rows:
            r["precio"] = dec(r["precio"])
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# Crear venta (vendedor/admin)
@app.route("/api/ventas", methods=["POST", "OPTIONS"])
@role_required("vendedor", "admin")
def api_ventas():
    if request.method == "OPTIONS":
        return ("", 204)

    data = request.get_json(silent=True) or {}
    id_usuario = data.get("id_usuario")
    items = data.get("items", [])

    if not id_usuario or not isinstance(items, list) or len(items) == 0:
        return jsonify({"error": "Faltan datos: id_usuario e items[]"}), 400

    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        cur.execute("INSERT INTO ventas (id_usuario, total) VALUES (%s, 0)", (id_usuario,))
        id_venta = cur.lastrowid
        total = Decimal("0.00")

        for it in items:
            prod_id = int(it.get("id_producto", 0))
            cant = int(it.get("cantidad", 0))
            if prod_id <= 0 or cant <= 0:
                continue

            cur.execute("""
                SELECT id_producto, nombre, descripcion, precio, stock
                FROM productos
                WHERE id_producto=%s
                FOR UPDATE
            """, (prod_id,))
            p = cur.fetchone()
            if not p:
                conn.rollback()
                return jsonify({"error": f"Producto {prod_id} no existe"}), 400
            if p["stock"] < cant:
                conn.rollback()
                return jsonify({"error": f"Stock insuficiente para {p['nombre']} (disp {p['stock']})"}), 400

            precio = p["precio"]
            subtotal = precio * Decimal(cant)
            total += subtotal

            cur.execute("""
                INSERT INTO venta_detalle
                (id_venta, id_producto, nombre_producto, descripcion, cantidad, precio_unitario, subtotal)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (id_venta, p["id_producto"], p["nombre"], p["descripcion"], cant, precio, subtotal))

            cur.execute("UPDATE productos SET stock = stock - %s WHERE id_producto=%s", (cant, prod_id))

        if total == 0:
            conn.rollback()
            return jsonify({"error": "No se enviaron cantidades válidas"}), 400

        cur.execute("UPDATE ventas SET total=%s WHERE id_venta=%s", (total, id_venta))
        conn.commit()

        return jsonify({"id_venta": id_venta, "total": float(total)})
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"error": f"DB: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# Actualizar stock (bodeguero/admin)
@app.route("/api/productos/<int:prod_id>/stock", methods=["PATCH", "OPTIONS"])
@role_required("bodeguero", "admin")
def api_set_stock(prod_id):
    if request.method == "OPTIONS":
        return ("", 204)

    data = request.get_json(silent=True) or {}
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        if "add" in data:
            delta = int(data["add"])
            if delta < 0:
                return jsonify({"error": "add debe ser >= 0"}), 400
            cur.execute("UPDATE productos SET stock = stock + %s WHERE id_producto=%s", (delta, prod_id))
        elif "new_stock" in data:
            new_stock = int(data["new_stock"])
            if new_stock < 0:
                return jsonify({"error": "new_stock debe ser >= 0"}), 400
            cur.execute("UPDATE productos SET stock = %s WHERE id_producto=%s", (new_stock, prod_id))
        else:
            return jsonify({"error": "Envía 'add' o 'new_stock'"}), 400

        conn.commit()
        cur.execute("SELECT id_producto, stock FROM productos WHERE id_producto=%s", (prod_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": f"Producto {prod_id} no existe"}), 404
        return jsonify({"id_producto": row["id_producto"], "stock": int(row["stock"])})
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# CRUD productos (bodeguero/admin)
@app.route("/api/productos", methods=["POST"])
@role_required("bodeguero", "admin")
def create_producto():
    data = request.get_json(silent=True) or {}
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO productos (nombre, descripcion, precio, stock)
            VALUES (%s,%s,%s,%s)
        """, (data.get("nombre"), data.get("descripcion"), data.get("precio"), data.get("stock", 0)))
        conn.commit()
        return jsonify({"id_producto": cur.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

@app.route("/api/productos/<int:prod_id>", methods=["PUT"])
@role_required("bodeguero", "admin")
def update_producto(prod_id):
    data = request.get_json(silent=True) or {}
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE productos
               SET nombre=%s, descripcion=%s, precio=%s, stock=%s
             WHERE id_producto=%s
        """, (data.get("nombre"), data.get("descripcion"), data.get("precio"), data.get("stock"), prod_id))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

@app.route("/api/productos/<int:prod_id>", methods=["DELETE"])
@role_required("bodeguero", "admin")
def delete_producto(prod_id):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM productos WHERE id_producto=%s", (prod_id,))
        conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# Reportes (vendedor ve solo los suyos)
def parse_dt(s, default=None):
    try:
        return datetime.fromisoformat(s) if s else default
    except:
        return default

@app.route("/api/reportes/ventas", methods=["GET"])
@role_required("vendedor", "supervisor", "admin")
def reportes_ventas():
    preset = (request.args.get("preset") or "").lower()
    now = datetime.now()

    if preset == "hoy":
        f = now.replace(hour=0, minute=0, second=0, microsecond=0); t = f + timedelta(days=1)
    elif preset == "semana":
        f = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday()); t = f + timedelta(days=7)
    elif preset == "mes":
        f = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        t = f.replace(year=f.year+1, month=1) if f.month == 12 else f.replace(month=f.month+1)
    elif preset in ("año", "anio"):
        f = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0); t = f.replace(year=f.year+1)
    else:
        f = parse_dt(request.args.get("from"), now.replace(hour=0, minute=0, second=0, microsecond=0))
        t = parse_dt(request.args.get("to"), f + timedelta(days=1))

    u = request.user
    vendedor_param = request.args.get("vendedor")
    only_self = (u["rol"] == "vendedor")

    vendor_clause = ""
    params = [f, t]
    if only_self:
        vendor_clause = " AND v.id_usuario = %s"; params.append(u["id_usuario"])
    elif vendedor_param:
        vendor_clause = " AND v.id_usuario = %s"; params.append(int(vendedor_param))

    try:
        conn = get_conn(); cur = conn.cursor(dictionary=True)

        cur.execute(f"""
          SELECT v.id_venta, v.fecha, v.id_usuario, u.nombre AS vendedor,
                 ROUND(SUM(d.subtotal),2) AS total
          FROM ventas v
          JOIN usuarios u ON u.id_usuario = v.id_usuario
          LEFT JOIN venta_detalle d ON d.id_venta = v.id_venta
          WHERE v.fecha >= %s AND v.fecha < %s {vendor_clause}
          GROUP BY v.id_venta, v.fecha, v.id_usuario, u.nombre
          ORDER BY v.fecha DESC
        """, params)
        ventas = cur.fetchall()

        cur.execute(f"""
          SELECT p.id_producto, p.nombre,
                 SUM(d.cantidad) AS unidades,
                 ROUND(SUM(d.subtotal),2) AS total
          FROM venta_detalle d
          JOIN productos p ON p.id_producto = d.id_producto
          JOIN ventas v ON v.id_venta = d.id_venta
          WHERE v.fecha >= %s AND v.fecha < %s {vendor_clause}
          GROUP BY p.id_producto, p.nombre
          ORDER BY total DESC
        """, params)
        productos = cur.fetchall()

        tot = round(sum(v["total"] or 0 for v in ventas), 2)
        tickets = len(ventas)

        return jsonify({
            "rango": {"from": f.isoformat(), "to": t.isoformat()},
            "scope": "self" if only_self else ("filtered" if vendedor_param else "all"),
            "totales": {"ventas": tot, "tickets": tickets},
            "ventas": ventas,
            "productos": productos
        })
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# Debug: quién soy
@app.route("/api/_whoami", methods=["GET"])
def whoami():
    u = get_request_user()
    return jsonify({
        "user": u,
        "role_from_header": request.headers.get("X-Role"),
        "user_from_header": request.headers.get("X-User-Id"),
    })

# Público temporal (sin auth) para depurar UI
@app.route("/api/productos_public", methods=["GET"])
def api_productos_public():
    try:
        conn = get_conn(); cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id_producto, nombre, descripcion, precio, stock
            FROM productos
            ORDER BY nombre
        """)
        rows = cur.fetchall()
        for r in rows:
            r["precio"] = dec(r["precio"])
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
