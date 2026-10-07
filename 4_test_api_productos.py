import os
import pytest
import requests as requests_module
from datetime import date, timedelta

##ejecutar con: python -m pytest 4_test_api_productos.py -v

BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}
requests = requests_module.Session()


@pytest.fixture(scope="session", autouse=True)
def iniciar_sesion_api():
    correo = os.environ.get("API_EMAIL")
    contrasena = os.environ.get("API_PASSWORD")
    if not correo or not contrasena:
        pytest.skip("Configura API_EMAIL y API_PASSWORD para ejecutar pruebas de API")
    respuesta = requests.post(
        f"{BASE_URL}/api/sesion",
        json={"correo": correo, "contrasena": contrasena},
        headers=HEADERS,
    )
    assert respuesta.status_code == 200, "Se requiere una cuenta válida, preferentemente admin"


def fecha_futura(dias=365):
    return (date.today() + timedelta(days=dias)).isoformat()


def fecha_pasada():
    return (date.today() - timedelta(days=1)).isoformat()


def producto_valido(**overrides):
    data = {
        "nombre": "Laptop HP",
        "descripcion": "Laptop 15 pulgadas",
        "precio": 1500.50,
        "precio_por_unidad": 1500.50,
        "cantidad_stock": 25,
        "unidad_medida": "unidad",
        "fecha_vencimiento": fecha_futura()
    }
    data.update(overrides)
    if "precio" in overrides and "precio_por_unidad" not in overrides:
        data["precio_por_unidad"] = overrides["precio"]
    return data


# ============================================================
# Fixture: crea un producto y lo elimina al final
# ============================================================
@pytest.fixture
def producto_creado():
    r = requests.post(f"{BASE_URL}/api/productos",
                      json=producto_valido(), headers=HEADERS)
    assert r.status_code == 201
    producto = r.json()
    yield producto
    # Cleanup
    requests.delete(f"{BASE_URL}/api/productos/{producto['id']}", headers=HEADERS)


# ============================================================
# 01 - Listar productos
# ============================================================
def test_listar_productos_devuelve_200():
    r = requests.get(f"{BASE_URL}/api/productos", headers=HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ============================================================
# 02 - Crear producto válido
# ============================================================
def test_crear_producto_valido_devuelve_201():
    payload = producto_valido()
    r = requests.post(f"{BASE_URL}/api/productos", json=payload, headers=HEADERS)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] is not None
    assert body["nombre"] == payload["nombre"]
    assert body["cantidad_stock"] == payload["cantidad_stock"]
    assert body["unidad_medida"] == payload["unidad_medida"]
    assert body["precio_por_unidad"] == payload["precio_por_unidad"]
    # Cleanup
    requests.delete(f"{BASE_URL}/api/productos/{body['id']}", headers=HEADERS)


# ============================================================
# 03 - Obtener producto por id
# ============================================================
def test_obtener_producto_existente(producto_creado):
    r = requests.get(f"{BASE_URL}/api/productos/{producto_creado['id']}",
                     headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["id"] == producto_creado["id"]


# ============================================================
# 04 - Obtener producto inexistente
# ============================================================
def test_obtener_producto_inexistente_devuelve_404():
    r = requests.get(f"{BASE_URL}/api/productos/999999", headers=HEADERS)
    assert r.status_code == 404
    assert "error" in r.json()


# ============================================================
# 05 - Crear con precio negativo
# ============================================================
def test_crear_con_precio_negativo_devuelve_400():
    payload = producto_valido(precio=-100)
    r = requests.post(f"{BASE_URL}/api/productos", json=payload, headers=HEADERS)
    assert r.status_code == 400
    assert "precio" in r.json()["error"].lower()


# ============================================================
# 06 - Crear con precio cero
# ============================================================
def test_crear_con_precio_cero_devuelve_400():
    payload = producto_valido(precio=0)
    r = requests.post(f"{BASE_URL}/api/productos", json=payload, headers=HEADERS)
    assert r.status_code == 400


# ============================================================
# 07 - Crear con precio no numérico
# ============================================================
def test_crear_con_precio_no_numerico_devuelve_400():
    payload = producto_valido(precio="abc")
    r = requests.post(f"{BASE_URL}/api/productos", json=payload, headers=HEADERS)
    assert r.status_code == 400


# ============================================================
# 08 - Crear con nombre vacío
# ============================================================
def test_crear_con_nombre_vacio_devuelve_400():
    payload = producto_valido(nombre="")
    r = requests.post(f"{BASE_URL}/api/productos", json=payload, headers=HEADERS)
    assert r.status_code == 400


# ============================================================
# 09 - Crear con nombre null
# ============================================================
def test_crear_con_nombre_null_devuelve_400():
    payload = producto_valido(nombre=None)
    r = requests.post(f"{BASE_URL}/api/productos", json=payload, headers=HEADERS)
    assert r.status_code == 400


# ============================================================
# 10 - Crear con fecha pasada
# ============================================================
def test_crear_con_fecha_pasada_devuelve_400():
    payload = producto_valido(fecha_vencimiento=fecha_pasada())
    r = requests.post(f"{BASE_URL}/api/productos", json=payload, headers=HEADERS)
    assert r.status_code == 400
    assert "fecha" in r.json()["error"].lower()


# ============================================================
# 11 - Crear con fecha formato inválido
# ============================================================
def test_crear_con_fecha_invalida_devuelve_400():
    payload = producto_valido(fecha_vencimiento="31-12-2026")
    r = requests.post(f"{BASE_URL}/api/productos", json=payload, headers=HEADERS)
    assert r.status_code == 400


# ============================================================
# 12 - Actualizar producto
# ============================================================
def test_actualizar_producto(producto_creado):
    actualizado = producto_valido(nombre="Laptop Actualizada", precio=2000)
    r = requests.put(f"{BASE_URL}/api/productos/{producto_creado['id']}",
                     json=actualizado, headers=HEADERS)
    assert r.status_code == 200
    # Verificar que se guardó
    r2 = requests.get(f"{BASE_URL}/api/productos/{producto_creado['id']}",
                      headers=HEADERS)
    assert r2.json()["nombre"] == "Laptop Actualizada"
    assert r2.json()["precio"] == 2000.0


# ============================================================
# 13 - Actualizar producto inexistente
# ============================================================
def test_actualizar_producto_inexistente_devuelve_404():
    actualizado = producto_valido()
    r = requests.put(f"{BASE_URL}/api/productos/999999",
                     json=actualizado, headers=HEADERS)
    assert r.status_code == 404


# ============================================================
# 14 - Eliminar producto
# ============================================================
def test_eliminar_producto(producto_creado):
    r = requests.delete(f"{BASE_URL}/api/productos/{producto_creado['id']}",
                        headers=HEADERS)
    assert r.status_code == 200
    # Verificar que ya no existe
    r2 = requests.get(f"{BASE_URL}/api/productos/{producto_creado['id']}",
                      headers=HEADERS)
    assert r2.status_code == 404


# ============================================================
# 15 - Eliminar producto inexistente
# ============================================================
def test_eliminar_producto_inexistente_devuelve_404():
    r = requests.delete(f"{BASE_URL}/api/productos/999999", headers=HEADERS)
    assert r.status_code == 404