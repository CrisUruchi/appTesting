from decimal import Decimal

import pytest
from mysql.connector import IntegrityError

import models


class CursorFake:
    def __init__(self, connection):
        self.connection = connection
        self.resultado = None
        self.lastrowid = None

    def execute(self, consulta, parametros):
        if consulta.lstrip().startswith("SELECT"):
            if "FROM compradores" in consulta:
                self.resultado = {"id": parametros[0]} if parametros[0] == 12 else None
            else:
                producto_id = parametros[0]
                self.resultado = (
                    dict(self.connection.producto)
                    if producto_id == self.connection.producto["id"]
                    else None
                )
        elif consulta.lstrip().startswith("UPDATE productos"):
            cantidad, producto_id = parametros
            assert producto_id == self.connection.producto["id"]
            self.connection.producto["cantidad_stock"] -= cantidad
        elif consulta.lstrip().startswith("INSERT INTO ventas"):
            self.connection.ventas.append(parametros)
            self.lastrowid = len(self.connection.ventas)

    def fetchone(self):
        return self.resultado

    def close(self):
        pass


class ConnectionFake:
    def __init__(self):
        self.producto = {
            "id": 7,
            "nombre": "Manzana",
            "cantidad_stock": Decimal("4.250"),
            "unidad_medida": "kg",
            "precio_por_unidad": Decimal("2.35"),
        }
        self.ventas = []
        self.commits = 0
        self.rollbacks = 0
        self.snapshot = None

    def cursor(self, dictionary=False):
        assert dictionary is True
        return CursorFake(self)

    def start_transaction(self):
        self.snapshot = (self.producto["cantidad_stock"], list(self.ventas))

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1
        self.producto["cantidad_stock"], self.ventas = self.snapshot

    def close(self):
        pass


def test_venta_guarda_total_y_descuenta_stock_en_una_transaccion(monkeypatch):
    conexion = ConnectionFake()
    monkeypatch.setattr(models, "get_connection", lambda: conexion)

    venta = models.VentaRepository().registrar(7, 3, 1.25, 12)

    assert venta["total"] == 2.94
    assert venta["comprador_id"] == 12
    assert conexion.producto["cantidad_stock"] == Decimal("3.000")
    assert len(conexion.ventas) == 1
    assert conexion.ventas[0][2] == 12
    assert "Ana" not in conexion.ventas[0]
    assert conexion.commits == 1
    assert conexion.rollbacks == 0


def test_stock_insuficiente_hace_rollback_y_no_registra_venta(monkeypatch):
    conexion = ConnectionFake()
    monkeypatch.setattr(models, "get_connection", lambda: conexion)

    with pytest.raises(models.StockInsuficiente):
        models.VentaRepository().registrar(7, 3, 5, 12)

    assert conexion.producto["cantidad_stock"] == Decimal("4.250")
    assert conexion.ventas == []
    assert conexion.commits == 0
    assert conexion.rollbacks == 1


class DeleteCursorFake:
    def __init__(self, connection):
        self.connection = connection
        self.rowcount = 1

    def execute(self, consulta, parametros):
        assert consulta == "DELETE FROM productos WHERE id = %s"
        assert parametros == (7,)
        if self.connection.referenciado:
            raise IntegrityError("Producto referenciado por ventas")

    def close(self):
        pass


class DeleteConnectionFake:
    def __init__(self, referenciado=False):
        self.referenciado = referenciado
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return DeleteCursorFake(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        pass


def test_eliminar_producto_confirma_el_borrado(monkeypatch):
    conexion = DeleteConnectionFake()
    monkeypatch.setattr(models, "get_connection", lambda: conexion)

    assert models.ProductoRepository().eliminar(7) is True
    assert conexion.commits == 1
    assert conexion.rollbacks == 0


def test_eliminar_producto_referenciado_hace_rollback(monkeypatch):
    conexion = DeleteConnectionFake(referenciado=True)
    monkeypatch.setattr(models, "get_connection", lambda: conexion)

    assert models.ProductoRepository().eliminar(7) is False
    assert conexion.commits == 0
    assert conexion.rollbacks == 1