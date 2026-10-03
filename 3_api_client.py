import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}

##python 3_api_client.py 

def separador(titulo):
    print("\n" + "=" * 60)
    print(f"  {titulo}")
    print("=" * 60)


def mostrar(respuesta):
    print(f"Status: {respuesta.status_code}")
    try:
        print(f"Body:   {respuesta.json()}")
    except ValueError:
        print(f"Body:   {respuesta.text}")


# ============================================================
# 01 - Listar todos los productos
# ============================================================
separador("01 - Listar productos")
r = requests.get(f"{BASE_URL}/api/productos", headers=HEADERS)
mostrar(r)


# ============================================================
# 02 - Crear producto válido
# ============================================================
separador("02 - Crear producto válido")
nuevo = {
    "nombre": "Laptop HP",
    "descripcion": "Laptop 15 pulgadas, 16GB RAM",
    "precio": 1500.50,
    "fecha_vencimiento": (date.today() + timedelta(days=365)).isoformat()
}
r = requests.post(f"{BASE_URL}/api/productos", json=nuevo, headers=HEADERS)
mostrar(r)

# Guardamos el id para los siguientes requests
if r.status_code == 201:
    producto_id = r.json().get("id")
    print(f"→ Producto creado con id = {producto_id}")
else:
    producto_id = None


# ============================================================
# 03 - Obtener el producto creado
# ============================================================
if producto_id:
    separador(f"03 - Obtener producto {producto_id}")
    r = requests.get(f"{BASE_URL}/api/productos/{producto_id}", headers=HEADERS)
    mostrar(r)


# ============================================================
# 04 - Crear producto con precio negativo (400)
# ============================================================
separador("04 - Crear producto con precio negativo (esperado 400)")
invalido = {
    "nombre": "Producto Inválido",
    "descripcion": "Precio negativo",
    "precio": -100,
    "fecha_vencimiento": (date.today() + timedelta(days=30)).isoformat()
}
r = requests.post(f"{BASE_URL}/api/productos", json=invalido, headers=HEADERS)
mostrar(r)


# ============================================================
# 05 - Crear producto con fecha pasada (400)
# ============================================================
separador("05 - Crear producto con fecha pasada (esperado 400)")
invalido = {
    "nombre": "Producto Vencido",
    "descripcion": "Fecha en el pasado",
    "precio": 100,
    "fecha_vencimiento": "2020-01-01"
}
r = requests.post(f"{BASE_URL}/api/productos", json=invalido, headers=HEADERS)
mostrar(r)


# ============================================================
# 06 - Crear producto con nombre vacío (400)
# ============================================================
separador("06 - Crear producto con nombre vacío (esperado 400)")
invalido = {
    "nombre": "",
    "descripcion": "Sin nombre",
    "precio": 100,
    "fecha_vencimiento": (date.today() + timedelta(days=30)).isoformat()
}
r = requests.post(f"{BASE_URL}/api/productos", json=invalido, headers=HEADERS)
mostrar(r)


# ============================================================
# 07 - Actualizar producto (PUT)
# ============================================================
if producto_id:
    separador(f"07 - Actualizar producto {producto_id}")
    actualizado = {
        "nombre": "Laptop HP Actualizada",
        "descripcion": "Ahora con 32GB RAM",
        "precio": 1800.00,
        "fecha_vencimiento": (date.today() + timedelta(days=500)).isoformat()
    }
    r = requests.put(f"{BASE_URL}/api/productos/{producto_id}",
                     json=actualizado, headers=HEADERS)
    mostrar(r)


# ============================================================
# 08 - Obtener producto inexistente (404)
# ============================================================
separador("08 - Obtener producto inexistente (esperado 404)")
r = requests.get(f"{BASE_URL}/api/productos/999999", headers=HEADERS)
mostrar(r)


# ============================================================
# 09 - Eliminar producto (DELETE)
# ============================================================
if producto_id:
    separador(f"09 - Eliminar producto {producto_id}")
    r = requests.delete(f"{BASE_URL}/api/productos/{producto_id}", headers=HEADERS)
    mostrar(r)


# ============================================================
# 10 - Listar productos después de eliminar
# ============================================================
separador("10 - Listar productos después de eliminar")
r = requests.get(f"{BASE_URL}/api/productos", headers=HEADERS)
mostrar(r)