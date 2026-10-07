import pytest
from werkzeug.security import check_password_hash, generate_password_hash

import app as sistema


class UsuariosFake:
    def __init__(self):
        self.usuarios = {
            rol: {
                "id": identificador,
                "nombre": rol,
                "correo": f"{rol}@test.local",
                "password_hash": generate_password_hash("clave1234"),
                "rol": rol,
                "activo": True,
            }
            for identificador, rol in enumerate(("admin", "compras", "vendedor"), 1)
        }

    def buscar_por_correo(self, correo):
        return next(
            (usuario for usuario in self.usuarios.values() if usuario["correo"] == correo),
            None,
        )

    def listar(self):
        return list(self.usuarios.values())

    def crear(self, nombre, correo, password_hash, rol):
        self.usuarios[correo] = {
            "id": 99,
            "nombre": nombre,
            "correo": correo,
            "password_hash": password_hash,
            "rol": rol,
            "activo": True,
        }
        return 99


class ProductosFake:
    def listar(self):
        return []

    def obtener(self, id_producto):
        return {"id": id_producto}

    def crear(self, **campos):
        return 17

    def actualizar(self, *args, **kwargs):
        return True

    def eliminar(self, id_producto):
        return True


class VentasFake:
    def __init__(self):
        self.stock = 5.0
        self.registros = []

    def registrar(self, producto_id, vendedor_id, cantidad, comprador_id):
        if producto_id != 7:
            raise sistema.ProductoNoEncontrado
        if comprador_id not in sistema.compradores.registros:
            raise sistema.CompradorNoEncontrado
        if cantidad > self.stock:
            raise sistema.StockInsuficiente(self.stock)
        self.stock -= cantidad
        venta = {
            "id": len(self.registros) + 1,
            "producto_id": producto_id,
            "vendedor_id": vendedor_id,
            "comprador_id": comprador_id,
            "comprador_nombre": "Ana",
            "comprador_apellido": "Lopez",
            "producto_nombre": "Manzana",
            "cantidad": cantidad,
            "unidad_medida": "kg",
            "precio_por_unidad": 2.5,
            "total": round(cantidad * 2.5, 2),
        }
        self.registros.append(venta)
        return venta

    def listar(self, vendedor_id=None):
        if vendedor_id is None:
            return self.registros
        return [venta for venta in self.registros if venta["vendedor_id"] == vendedor_id]


class CompradoresFake:
    def __init__(self):
        self.registros = {
            21: {"id": 21, "nombre": "Ana", "apellido": "Lopez", "telefono": "70000000"}
        }

    def buscar(self, termino):
        termino = termino.lower()
        return [
            comprador for comprador in self.registros.values()
            if termino in " ".join(str(valor) for valor in comprador.values()).lower()
        ]

    def crear(self, nombre, apellido, telefono):
        comprador_id = max(self.registros, default=0) + 1
        self.registros[comprador_id] = {
            "id": comprador_id,
            "nombre": nombre,
            "apellido": apellido,
            "telefono": telefono,
        }
        return comprador_id


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setattr(sistema, "usuarios", UsuariosFake())
    monkeypatch.setattr(sistema, "repo", ProductosFake())
    monkeypatch.setattr(sistema, "ventas", VentasFake())
    monkeypatch.setattr(sistema, "compradores", CompradoresFake())
    return sistema.app.test_client()


def autenticar(cliente, rol):
    return cliente.post(
        "/api/sesion",
        json={"correo": f"{rol}@test.local", "contrasena": "clave1234"},
    )


def test_api_rechaza_sesion_anonima(cliente):
    respuesta = cliente.get("/api/productos")
    assert respuesta.status_code == 401


def test_inicio_sesion_devuelve_perfil_y_cierre_invalida_sesion(cliente):
    respuesta = autenticar(cliente, "vendedor")
    assert respuesta.status_code == 200
    assert respuesta.json["perfil"] == "Vendedor"
    assert cliente.delete("/api/sesion").status_code == 200
    assert cliente.get("/api/productos").status_code == 401


@pytest.mark.parametrize(
    ("rol", "crear_status", "eliminar_status", "usuarios_status"),
    [
        ("vendedor", 403, 403, 403),
        ("compras", 201, 403, 403),
        ("admin", 201, 200, 200),
    ],
)
def test_permisos_se_aplican_en_el_servidor(
    cliente, rol, crear_status, eliminar_status, usuarios_status
):
    assert autenticar(cliente, rol).status_code == 200
    producto = {
        "nombre": "Producto de prueba",
        "descripcion": "",
        "precio": 5,
        "fecha_vencimiento": "2099-12-31",
    }
    assert cliente.post("/api/productos", json=producto).status_code == crear_status
    assert cliente.delete("/api/productos/1").status_code == eliminar_status
    assert cliente.get("/api/usuarios").status_code == usuarios_status


def test_contrasena_incorrecta_no_inicia_sesion(cliente):
    respuesta = cliente.post(
        "/api/sesion",
        json={"correo": "admin@test.local", "contrasena": "incorrecta"},
    )
    assert respuesta.status_code == 401


def test_admin_crea_usuario_con_contrasena_hasheada(cliente):
    assert autenticar(cliente, "admin").status_code == 200
    respuesta = cliente.post(
        "/api/usuarios",
        json={
            "nombre": "Nueva vendedora",
            "correo": "nueva@test.local",
            "contrasena": "clave-segura-123",
            "rol": "vendedor",
        },
    )
    assert respuesta.status_code == 201
    usuario = sistema.usuarios.buscar_por_correo("nueva@test.local")
    assert usuario["password_hash"] != "clave-segura-123"
    assert check_password_hash(usuario["password_hash"], "clave-segura-123")
    assert cliente.post(
        "/api/sesion",
        json={"correo": "nueva@test.local", "contrasena": "clave-segura-123"},
    ).status_code == 200


def test_vendedor_registra_venta_y_ve_solo_su_historial(cliente):
    assert autenticar(cliente, "vendedor").status_code == 200
    respuesta = cliente.post(
        "/api/ventas", json={"producto_id": 7, "comprador_id": 21, "cantidad": 1.25}
    )
    assert respuesta.status_code == 201
    assert respuesta.json["total"] == 3.12
    assert respuesta.json["comprador_id"] == 21
    assert sistema.ventas.stock == 3.75
    assert len(cliente.get("/api/ventas").json) == 1


def test_venta_rechaza_cantidad_superior_al_stock_sin_mutar_inventario(cliente):
    assert autenticar(cliente, "vendedor").status_code == 200
    respuesta = cliente.post(
        "/api/ventas", json={"producto_id": 7, "comprador_id": 21, "cantidad": 6}
    )
    assert respuesta.status_code == 409
    assert respuesta.json["disponible"] == 5
    assert sistema.ventas.stock == 5


def test_compras_no_puede_registrar_ventas(cliente):
    assert autenticar(cliente, "compras").status_code == 200
    assert cliente.post(
        "/api/ventas", json={"producto_id": 7, "comprador_id": 21, "cantidad": 1}
    ).status_code == 403


def test_api_permite_registrar_y_buscar_compradores(cliente):
    assert autenticar(cliente, "vendedor").status_code == 200
    respuesta = cliente.post(
        "/api/compradores",
        json={"nombre": "Luis", "apellido": "Perez", "telefono": "71234567"},
    )
    assert respuesta.status_code == 201
    comprador_id = respuesta.json["id"]
    busqueda = cliente.get("/api/compradores?buscar=Luis")
    assert busqueda.status_code == 200
    assert busqueda.json[0]["id"] == comprador_id


def test_busqueda_de_compradores_requiere_usuario_autenticado(cliente):
    assert cliente.get("/api/compradores?buscar=Ana").status_code == 401


def test_venta_requiere_comprador_registrado(cliente):
    assert autenticar(cliente, "vendedor").status_code == 200
    assert cliente.post(
        "/api/ventas", json={"producto_id": 7, "cantidad": 1}
    ).status_code == 400
    assert cliente.post(
        "/api/ventas",
        json={"producto_id": 7, "comprador_id": 999, "cantidad": 1},
    ).status_code == 404