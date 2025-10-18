from flask import Blueprint, jsonify, request
from ..models.product_model import list_products
from ..services.product_service import set_stock, change_stock, ProductError

products_bp = Blueprint("products", __name__)

@products_bp.get("/productos")
def get_products():
    rows = list_products()
    # Convertir Decimal a float para JSON
    for r in rows:
        if "precio" in r and r["precio"] is not None:
            r["precio"] = float(r["precio"])
    return jsonify(rows)

products_bp = Blueprint("products", __name__)

@products_bp.get("/productos")
def get_products():
    rows = list_products()
    for r in rows:
        if "precio" in r and r["precio"] is not None:
            r["precio"] = float(r["precio"])
    return jsonify(rows)

@products_bp.patch("/productos/<int:id_producto>/stock")
def patch_stock(id_producto: int):
    data = request.get_json(silent=True) or {}
    try:
        if "new_stock" in data:
            result = set_stock(id_producto, int(data["new_stock"]))
        elif "delta" in data:
            result = change_stock(id_producto, int(data["delta"]))
        else:
            return jsonify({"error": "Envía new_stock o delta"}), 400
        return jsonify(result)
    except ProductError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
