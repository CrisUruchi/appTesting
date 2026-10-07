"""Prueba UI: python -m pytest 7_pruebaUISelenium.py -v"""

import json
import os
import uuid
from pathlib import Path

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture
def navegador(credenciales):
    opciones = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=opciones)
    yield driver
    #driver.quit()


@pytest.fixture
def credenciales():
    archivo = Path(__file__).with_name("usuarios_prueba.json")
    if not archivo.exists():
        pytest.fail(
            "No existe usuarios_prueba.json"
        )

    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        pytest.fail(f"No se pudo leer {archivo.name}: {error}")

    usuarios = datos.get("usuarios") if isinstance(datos, dict) else None
    if not isinstance(usuarios, list):
        pytest.fail(f"{archivo.name} debe contener una lista llamada 'usuarios'.")

    usuario = next((
        usuario for usuario in usuarios
        if isinstance(usuario, dict)
        and usuario.get("rol") in {"admin", "compras"}
        and usuario.get("correo")
        and usuario.get("contrasena")
    ), None)
    if usuario is None:
        pytest.skip(
            f"Agrega a {archivo.name} una cuenta con correo, contraseña "
            "y rol 'admin' o 'compras'."
        )

    return usuario["correo"], usuario["contrasena"]


def test_login_y_registro_de_producto(navegador, credenciales):
    correo, contrasena = credenciales
    base_url = "http://localhost:5000"
    espera = WebDriverWait(navegador, 15)
    navegador.get(base_url)
    time.sleep(5)

    espera.until(EC.visibility_of_element_located((By.ID, "correo-login"))).send_keys(correo)
    navegador.find_element(By.ID, "contrasena-login").send_keys(contrasena)
    time.sleep(3)
    navegador.find_element(By.CSS_SELECTOR, "#form-login button[type='submit']").click()
    espera.until(EC.visibility_of_element_located((By.ID, "vista-app")))
    assert navegador.find_element(By.ID, "usuario-nombre").text
    espera.until(EC.visibility_of_element_located((By.ID, "form-producto")))

    nombre_producto = f"Producto Selenium {uuid.uuid4().hex[:10]}"
    fecha_vencimiento = "2026-11-20"

    navegador.find_element(By.ID, "nombre").send_keys(nombre_producto)
    navegador.find_element(By.ID, "descripcion").send_keys("Alta desde prueba automatizada")
    navegador.find_element(By.ID, "precio").send_keys("12.50")
    navegador.find_element(By.ID, "cantidad-stock").send_keys("5")
    navegador.find_element(By.ID, "unidad-medida").send_keys("unidad")
    campo_fecha = navegador.find_element(By.ID, "fecha_vencimiento")
    navegador.execute_script(
        "arguments[0].value = arguments[1];",
        campo_fecha,
        fecha_vencimiento,
    )
    assert campo_fecha.get_attribute("value") == fecha_vencimiento
    time.sleep(5)
    navegador.find_element(By.ID, "btn-guardar").click()

    fila_producto = espera.until(EC.visibility_of_element_located((
        By.XPATH,
        f'//tbody[@id="tbody-productos"]/tr[td[normalize-space()="{nombre_producto}"]]'
    )))
    assert nombre_producto in fila_producto.text