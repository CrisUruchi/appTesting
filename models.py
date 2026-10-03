from db import get_connection


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

    def crear(self, nombre, descripcion, precio, fecha_vencimiento):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO productos (nombre, descripcion, precio, fecha_vencimiento)
               VALUES (%s, %s, %s, %s)""",
            (nombre, descripcion, precio, fecha_vencimiento)
        )
        conn.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return nuevo_id

    def actualizar(self, id_producto, nombre, descripcion, precio, fecha_vencimiento):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE productos
               SET nombre = %s, descripcion = %s, precio = %s, fecha_vencimiento = %s
               WHERE id = %s""",
            (nombre, descripcion, precio, fecha_vencimiento, id_producto)
        )
        conn.commit()
        filas = cursor.rowcount
        cursor.close()
        conn.close()
        return filas > 0

    def eliminar(self, id_producto):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = %s", (id_producto,))
        conn.commit()
        filas = cursor.rowcount
        cursor.close()
        conn.close()
        return filas > 0