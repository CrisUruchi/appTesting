import os
from functools import wraps
from flask import Flask, request, jsonify, render_template, session
from datetime import date, datetime
from werkzeug.security import check_password_hash, generate_password_hash
from validaciones import validar_producto
from models import (
    ProductoNoEncontrado,
    ProductoRepository,
    CompradorNoEncontrado,
    CompradorRepository,
    StockInsuficiente,
    UsuarioRepository,
    VentaRepository,
)
from validaciones import validar_cantidad

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "change-this-secret-key-before-deployment"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get(
    "FLASK_COOKIE_SECURE", "0"
).lower() in {"1", "true", "yes"}
repo = ProductoRepository()
usuarios = UsuarioRepository()
ventas = VentaRepository()
compradores = CompradorRepository()

ROLES = {
    "admin": "Gerente",
    "compras": "Encargado de compras",
    "vendedor": "Vendedor",
}


def requiere_rol(*roles):
    def decorador(funcion):
        @wraps(funcion)
        def protegido(*args, **kwargs):
            usuario = session.get("usuario")
            if usuario is None:
                return jsonify({"error": "Debes iniciar sesión"}), 401
            if roles and usuario["rol"] not in roles:
                return jsonify({"error": "No tienes permisos para esta operación"}), 403
            return funcion(*args, **kwargs)
        return protegido
    return decorador


def datos_publicos(usuario):
    return {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "correo": usuario["correo"],
        "rol": usuario["rol"],
        "perfil": ROLES[usuario["rol"]],
    }


# ============ WEB UI ============

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sesion", methods=["GET"])
def obtener_sesion():
    usuario = session.get("usuario")
    if usuario is None:
        return jsonify({"error": "Debes iniciar sesión"}), 401
    return jsonify(datos_publicos(usuario)), 200


@app.route("/api/sesion", methods=["POST"])
def iniciar_sesion():
    data = request.get_json(silent=True) or {}
    correo = data.get("correo", "")
    contrasena = data.get("contrasena", "")
    if not isinstance(correo, str) or not isinstance(contrasena, str):
        return jsonify({"error": "Correo y contraseña son obligatorios"}), 400

    usuario = usuarios.buscar_por_correo(correo.strip().lower())
    if (usuario is None or not usuario["activo"] or
            not check_password_hash(usuario["password_hash"], contrasena)):
        return jsonify({"error": "Correo o contraseña incorrectos"}), 401

    session.clear()
    session["usuario"] = datos_publicos(usuario)
    return jsonify(datos_publicos(usuario)), 200


@app.route("/api/sesion", methods=["DELETE"])
def cerrar_sesion():
    session.clear()
    return jsonify({"mensaje": "Sesión cerrada"}), 200


@app.route("/api/usuarios", methods=["GET"])
@requiere_rol("admin")
def listar_usuarios():
    return jsonify([datos_publicos(usuario) for usuario in usuarios.listar()]), 200


@app.route("/api/usuarios", methods=["POST"])
@requiere_rol("admin")
def crear_usuario():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre", "")
    correo = data.get("correo", "")
    contrasena = data.get("contrasena", "")
    rol = data.get("rol", "")

    if not all(isinstance(valor, str) for valor in (nombre, correo, contrasena, rol)):
        return jsonify({"error": "Todos los campos deben ser texto"}), 400
    nombre = nombre.strip()
    correo = correo.strip().lower()
    if not nombre or len(nombre) > 120:
        return jsonify({"error": "El nombre es obligatorio y admite hasta 120 caracteres"}), 400
    if "@" not in correo or len(correo) > 254:
        return jsonify({"error": "Ingresa un correo válido"}), 400
    if len(contrasena) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
    if rol not in ROLES:
        return jsonify({"error": "El perfil seleccionado no es válido"}), 400

    if usuarios.buscar_por_correo(correo) is not None:
        return jsonify({"error": "Ya existe un usuario con ese correo"}), 409
    usuario_id = usuarios.crear(
        nombre, correo, generate_password_hash(contrasena), rol
    )
    return jsonify({
        "id": usuario_id,
        "nombre": nombre,
        "correo": correo,
        "rol": rol,
        "perfil": ROLES[rol],
    }), 201


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
    for campo in ("precio", "precio_por_unidad", "cantidad_stock"):
        if p.get(campo) is not None:
            p[campo] = float(p[campo])
    return p


def serializar_venta(venta):
    resultado = dict(venta)
    for campo in ("cantidad", "precio_por_unidad", "total"):
        if resultado.get(campo) is not None:
            resultado[campo] = float(resultado[campo])
    if isinstance(resultado.get("vendido_en"), datetime):
        resultado["vendido_en"] = resultado["vendido_en"].isoformat()
    return resultado


@app.route("/api/productos", methods=["GET"])
@requiere_rol("admin", "compras", "vendedor")
def listar_productos():
    productos = repo.listar()
    return jsonify([serializar(p) for p in productos]), 200


@app.route("/api/productos/<int:id_producto>", methods=["GET"])
@requiere_rol("admin", "compras", "vendedor")
def obtener_producto(id_producto):
    producto = repo.obtener(id_producto)
    if producto is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(serializar(producto)), 200


@app.route("/api/productos", methods=["POST"])
@requiere_rol("admin", "compras")
def crear_producto():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    try:
        limpio = validar_producto(
            data.get("nombre"),
            data.get("descripcion"),
            data.get("precio"),
            data.get("fecha_vencimiento"),
            data.get("cantidad_stock", 0),
            data.get("unidad_medida", "unidad"),
            data.get("precio_por_unidad"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    nuevo_id = repo.crear(**limpio)
    return jsonify({"id": nuevo_id, **limpio, "fecha_vencimiento": str(limpio["fecha_vencimiento"])}), 201


@app.route("/api/productos/<int:id_producto>", methods=["PUT"])
@requiere_rol("admin", "compras")
def actualizar_producto(id_producto):
    producto_actual = repo.obtener(id_producto)
    if producto_actual is None:
        return jsonify({"error": "Producto no encontrado"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    try:
        limpio = validar_producto(
            data.get("nombre"),
            data.get("descripcion"),
            data.get("precio"),
            data.get("fecha_vencimiento"),
            data.get("cantidad_stock", producto_actual["cantidad_stock"]),
            data.get("unidad_medida", producto_actual["unidad_medida"]),
            data.get("precio_por_unidad"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    repo.actualizar(id_producto, **limpio)
    return jsonify({"mensaje": "Producto actualizado", "id": id_producto}), 200


@app.route("/api/productos/<int:id_producto>", methods=["DELETE"])
@requiere_rol("admin")
def eliminar_producto(id_producto):
    if repo.obtener(id_producto) is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    if not repo.eliminar(id_producto):
        return jsonify({"error": "No se puede eliminar un producto con ventas registradas"}), 409
    return jsonify({"mensaje": "Producto eliminado", "id": id_producto}), 200


@app.route("/api/ventas", methods=["GET"])
@requiere_rol("admin", "vendedor")
def listar_ventas():
    usuario = session["usuario"]
    vendedor_id = None if usuario["rol"] == "admin" else usuario["id"]
    return jsonify([serializar_venta(venta) for venta in ventas.listar(vendedor_id)]), 200


@app.route("/api/compradores", methods=["GET"])
@requiere_rol("admin", "vendedor")
def buscar_compradores():
    termino = request.args.get("buscar", "").strip()
    if len(termino) < 2:
        return jsonify([]), 200
    return jsonify(compradores.buscar(termino)), 200


@app.route("/api/compradores", methods=["POST"])
@requiere_rol("admin", "vendedor")
def crear_comprador():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    telefono = data.get("telefono")
    if not all(isinstance(valor, str) for valor in (nombre, apellido, telefono)):
        return jsonify({"error": "Nombre, apellido y teléfono son obligatorios"}), 400
    nombre = nombre.strip()
    apellido = apellido.strip()
    telefono = telefono.strip()
    if not nombre or len(nombre) > 100:
        return jsonify({"error": "El nombre es obligatorio y admite hasta 100 caracteres"}), 400
    if not apellido or len(apellido) > 100:
        return jsonify({"error": "El apellido es obligatorio y admite hasta 100 caracteres"}), 400
    if not telefono or len(telefono) > 30:
        return jsonify({"error": "El teléfono es obligatorio y admite hasta 30 caracteres"}), 400

    comprador_id = compradores.crear(nombre, apellido, telefono)
    return jsonify({
        "id": comprador_id,
        "nombre": nombre,
        "apellido": apellido,
        "telefono": telefono,
    }), 201


@app.route("/api/ventas", methods=["POST"])
@requiere_rol("admin", "vendedor")
def registrar_venta():
    data = request.get_json(silent=True) or {}
    producto_id = data.get("producto_id")
    comprador_id = data.get("comprador_id")
    if isinstance(producto_id, bool) or not isinstance(producto_id, int) or producto_id < 1:
        return jsonify({"error": "El producto seleccionado no es válido"}), 400
    if isinstance(comprador_id, bool) or not isinstance(comprador_id, int) or comprador_id < 1:
        return jsonify({"error": "Selecciona un comprador registrado"}), 400
    try:
        cantidad = validar_cantidad(data.get("cantidad"))
        venta = ventas.registrar(
            producto_id, session["usuario"]["id"], cantidad, comprador_id
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except ProductoNoEncontrado:
        return jsonify({"error": "Producto no encontrado"}), 404
    except CompradorNoEncontrado:
        return jsonify({"error": "Comprador no encontrado"}), 404
    except StockInsuficiente as error:
        return jsonify({"error": "Stock insuficiente", "disponible": error.disponible}), 409
    return jsonify(serializar_venta(venta)), 201


if __name__ == "__main__":
    app.run(port=5000, debug=True)