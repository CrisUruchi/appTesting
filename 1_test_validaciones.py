import pytest
from datetime import date, timedelta
from validaciones import (
    validar_nombre, validar_descripcion, validar_precio,
    validar_cantidad, validar_fecha_vencimiento, validar_producto
)

#ejecutar con
#python -m pytest 1_test_validaciones.py -v

# ===== Nombre =====
def test_nombre_valido():
    assert validar_nombre("Laptop") == "Laptop"

def test_nombre_con_espacios():
    assert validar_nombre("  Laptop  ") == "Laptop"

def test_nombre_vacio_lanza_error():
    with pytest.raises(ValueError):
        validar_nombre("")

def test_nombre_null_lanza_error():
    with pytest.raises(ValueError):
        validar_nombre(None)

def test_nombre_muy_largo_lanza_error():
    with pytest.raises(ValueError):
        validar_nombre("a" * 101)


# ===== Descripción =====
def test_descripcion_opcional():
    assert validar_descripcion(None) == ""

def test_descripcion_valida():
    assert validar_descripcion("Una descripción") == "Una descripción"

def test_descripcion_muy_larga_lanza_error():
    with pytest.raises(ValueError):
        validar_descripcion("a" * 256)


# ===== Precio =====
def test_precio_valido():
    assert validar_precio(1500) == 1500.0

def test_precio_string_numerico():
    assert validar_precio("1500.50") == 1500.50

def test_precio_cero_lanza_error():
    with pytest.raises(ValueError):
        validar_precio(0)

def test_precio_negativo_lanza_error():
    with pytest.raises(ValueError):
        validar_precio(-100)

def test_precio_no_numerico_lanza_error():
    with pytest.raises(ValueError):
        validar_precio("abc")


# ===== Fecha =====
def test_fecha_futura_valida():
    futura = date.today() + timedelta(days=30)
    assert validar_fecha_vencimiento(futura) == futura

def test_fecha_string_valida():
    futura = date.today() + timedelta(days=30)
    assert validar_fecha_vencimiento(futura.isoformat()) == futura

def test_fecha_pasada_lanza_error():
    with pytest.raises(ValueError):
        validar_fecha_vencimiento(date.today() - timedelta(days=1))

def test_fecha_hoy_lanza_error():
    with pytest.raises(ValueError):
        validar_fecha_vencimiento(date.today())

def test_fecha_formato_invalido_lanza_error():
    with pytest.raises(ValueError):
        validar_fecha_vencimiento("31-12-2026")


# ===== Producto completo =====
def test_producto_valido():
    futura = date.today() + timedelta(days=30)
    resultado = validar_producto("Laptop", "HP", 1500, futura)
    assert resultado["nombre"] == "Laptop"
    assert resultado["precio"] == 1500.0
    assert resultado["fecha_vencimiento"] == futura


def test_producto_incluye_stock_unidad_y_precio_por_unidad():
    futura = date.today() + timedelta(days=30)
    resultado = validar_producto("Manzana", "", 2.5, futura, 12.75, "kg")
    assert resultado["cantidad_stock"] == 12.75
    assert resultado["unidad_medida"] == "kg"
    assert resultado["precio_por_unidad"] == resultado["precio"] == 2.5


def test_cantidad_de_venta_debe_ser_positiva():
    assert validar_cantidad("0.250") == 0.25
    with pytest.raises(ValueError):
        validar_cantidad(0)
    with pytest.raises(ValueError):
        validar_cantidad("NaN")


def test_stock_no_puede_ser_negativo():
    with pytest.raises(ValueError):
        validar_cantidad(-1, permitir_cero=True)
    with pytest.raises(ValueError):
        validar_cantidad("NaN", permitir_cero=True)