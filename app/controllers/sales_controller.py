from flask import Blueprint, request, jsonify
from ..services.sale_service import create_sale, SaleError

sales_bp = Blueprint("sales", __name__)

@sales_bp.post("/ventas")
def post_sale():
    data = request.get_json(silent=True) or {}
    id_usuario = data.get("id_usuario")
    items = data.get("items", [])
    try:
        result = create_sale(id_usuario, items)
        return jsonify(result), 200
    except SaleError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"DB: {e}"}), 500
