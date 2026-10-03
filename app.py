from flask import Flask, request, jsonify, render_template
from datetime import date, datetime
from validaciones import validar_producto
from models import ProductoRepository

app = Flask(__name__)
repo = ProductoRepository()


# ============ WEB UI ============

@app.route("/")
def index():
    return render_template("index.html")


# ============ API REST ============

def serializar(producto):
    """Convierte tipos no-JSON a string."""
    if producto is None:
        return None
    p = dict(producto)
    if isinstance(p.get("fecha_vencimiento"), date):
        p["fecha_vencimiento"] = p["fecha_vencimiento"].isoformat()
    if isinstance(p.get("creado_en"), datetime):
        p["creado_en"] = p["creado_en"].isoformat()
    if p.get("precio") is not None:
        p["precio"] = float(p["precio"])
    return p


@app.route("/api/productos", methods=["GET"])
def listar_productos():
    productos = repo.listar()
    return jsonify([serializar(p) for p in productos]), 200


@app.route("/api/productos/<int:id_producto>", methods=["GET"])
def obtener_producto(id_producto):
    producto = repo.obtener(id_producto)
    if producto is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(serializar(producto)), 200


@app.route("/api/productos", methods=["POST"])
def crear_producto():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    try:
        limpio = validar_producto(
            data.get("nombre"),
            data.get("descripcion"),
            data.get("precio"),
            data.get("fecha_vencimiento")
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    nuevo_id = repo.crear(**limpio)
    return jsonify({"id": nuevo_id, **{k: str(v) for k, v in limpio.items()}}), 201


@app.route("/api/productos/<int:id_producto>", methods=["PUT"])
def actualizar_producto(id_producto):
    if repo.obtener(id_producto) is None:
        return jsonify({"error": "Producto no encontrado"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    try:
        limpio = validar_producto(
            data.get("nombre"),
            data.get("descripcion"),
            data.get("precio"),
            data.get("fecha_vencimiento")
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    repo.actualizar(id_producto, **limpio)
    return jsonify({"mensaje": "Producto actualizado", "id": id_producto}), 200


@app.route("/api/productos/<int:id_producto>", methods=["DELETE"])
def eliminar_producto(id_producto):
    if repo.obtener(id_producto) is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    repo.eliminar(id_producto)
    return jsonify({"mensaje": "Producto eliminado", "id": id_producto}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)