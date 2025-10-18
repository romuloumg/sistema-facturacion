from flask import Flask
from flask_cors import CORS
from .config import Config
from .controllers.products_controller import products_bp
from .controllers.sales_controller import sales_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(sales_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
