from decimal import Decimal, ROUND_HALF_UP

from mysql.connector import IntegrityError

from db import get_connection


class UsuarioRepository:

    def buscar_por_correo(self, correo):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        return usuario

    def listar(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre, correo, rol, activo FROM usuarios ORDER BY id"
        )
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        return usuarios

    def crear(self, nombre, correo, password_hash, rol):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO usuarios (nombre, correo, password_hash, rol)
               VALUES (%s, %s, %s, %s)""",
            (nombre, correo, password_hash, rol)
        )
        conn.commit()
        usuario_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return usuario_id


class CompradorRepository:

    def buscar(self, termino):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        patron = f"%{termino}%"
        cursor.execute(
            """SELECT id, nombre, apellido, telefono FROM compradores
               WHERE nombre LIKE %s OR apellido LIKE %s OR telefono LIKE %s
               ORDER BY apellido, nombre LIMIT 20""",
            (patron, patron, patron)
        )
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return resultados

    def crear(self, nombre, apellido, telefono):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO compradores (nombre, apellido, telefono)
               VALUES (%s, %s, %s)""",
            (nombre, apellido, telefono)
        )
        conn.commit()
        comprador_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return comprador_id


class ProductoRepository:

    def listar(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM productos ORDER BY id DESC")
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return resultados

    def obtener(self, id_producto):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM productos WHERE id = %s", (id_producto,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        return resultado

    def crear(
        self, nombre, descripcion, precio, fecha_vencimiento,
        cantidad_stock, unidad_medida, precio_por_unidad
    ):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO productos
               (nombre, descripcion, precio, fecha_vencimiento, cantidad_stock,
                unidad_medida, precio_por_unidad)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (nombre, descripcion, precio_por_unidad, fecha_vencimiento,
             cantidad_stock, unidad_medida, precio_por_unidad)
        )
        conn.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return nuevo_id

    def actualizar(
        self, id_producto, nombre, descripcion, precio, fecha_vencimiento,
        cantidad_stock, unidad_medida, precio_por_unidad
    ):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE productos
               SET nombre = %s, descripcion = %s, precio = %s,
                   fecha_vencimiento = %s, cantidad_stock = %s,
                   unidad_medida = %s, precio_por_unidad = %s
               WHERE id = %s""",
            (nombre, descripcion, precio_por_unidad, fecha_vencimiento,
             cantidad_stock, unidad_medida, precio_por_unidad, id_producto)
        )
        conn.commit()
        filas = cursor.rowcount
        cursor.close()
        conn.close()
        return filas > 0

    def eliminar(self, id_producto):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM productos WHERE id = %s", (id_producto,))
            conn.commit()
            return cursor.rowcount > 0
        except IntegrityError:
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()


class ProductoNoEncontrado(Exception):
    pass


class StockInsuficiente(Exception):
    def __init__(self, disponible):
        self.disponible = float(disponible)


class CompradorNoEncontrado(Exception):
    pass


class VentaRepository:

    def registrar(self, producto_id, vendedor_id, cantidad, comprador_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            cursor.execute(
                "SELECT id FROM compradores WHERE id = %s FOR UPDATE",
                (comprador_id,)
            )
            if cursor.fetchone() is None:
                raise CompradorNoEncontrado
            cursor.execute(
                """SELECT id, nombre, cantidad_stock, unidad_medida, precio_por_unidad
                   FROM productos WHERE id = %s FOR UPDATE""",
                (producto_id,)
            )
            producto = cursor.fetchone()
            if producto is None:
                raise ProductoNoEncontrado

            cantidad = Decimal(str(cantidad))
            disponible = Decimal(str(producto["cantidad_stock"]))
            if cantidad > disponible:
                raise StockInsuficiente(disponible)

            precio = Decimal(str(producto["precio_por_unidad"]))
            total = (cantidad * precio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            cursor.execute(
                "UPDATE productos SET cantidad_stock = cantidad_stock - %s WHERE id = %s",
                (cantidad, producto_id)
            )
            cursor.execute(
                """INSERT INTO ventas
                         (producto_id, vendedor_id, comprador_id, producto_nombre, cantidad,
                          unidad_medida, precio_por_unidad, total)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                     (producto_id, vendedor_id, comprador_id, producto["nombre"], cantidad,
                 producto["unidad_medida"], precio, total)
            )
            venta_id = cursor.lastrowid
            conn.commit()
            return {
                "id": venta_id,
                "producto_id": producto_id,
                "comprador_id": comprador_id,
                "producto_nombre": producto["nombre"],
                "cantidad": float(cantidad),
                "unidad_medida": producto["unidad_medida"],
                "precio_por_unidad": float(precio),
                "total": float(total),
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def listar(self, vendedor_id=None):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if vendedor_id is None:
            cursor.execute(
                  """SELECT v.*, u.nombre AS vendedor_nombre,
                         c.nombre AS comprador_nombre, c.apellido AS comprador_apellido,
                         c.telefono AS comprador_telefono
                     FROM ventas v
                   JOIN usuarios u ON u.id = v.vendedor_id
                     LEFT JOIN compradores c ON c.id = v.comprador_id
                   ORDER BY v.vendido_en DESC, v.id DESC"""
            )
        else:
            cursor.execute(
                     """SELECT v.*, u.nombre AS vendedor_nombre,
                                  c.nombre AS comprador_nombre, c.apellido AS comprador_apellido,
                                  c.telefono AS comprador_telefono
                         FROM ventas v
                   JOIN usuarios u ON u.id = v.vendedor_id
                         LEFT JOIN compradores c ON c.id = v.comprador_id
                   WHERE v.vendedor_id = %s
                   ORDER BY v.vendido_en DESC, v.id DESC""",
                (vendedor_id,)
            )
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return resultados
