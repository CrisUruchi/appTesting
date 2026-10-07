import math
from datetime import date, datetime


def validar_nombre(nombre):
    """Valida que el nombre no sea vacío ni demasiado largo."""
    if nombre is None:
        raise ValueError("El nombre no puede ser nulo")
    if not isinstance(nombre, str):
        raise ValueError("El nombre debe ser texto")
    nombre = nombre.strip()
    if len(nombre) == 0:
        raise ValueError("El nombre no puede estar vacío")
    if len(nombre) > 100:
        raise ValueError("El nombre no puede superar 100 caracteres")
    return nombre


def validar_descripcion(descripcion):
    """La descripción es opcional, pero si existe no puede superar 255 chars."""
    if descripcion is None:
        return ""
    if not isinstance(descripcion, str):
        raise ValueError("La descripción debe ser texto")
    descripcion = descripcion.strip()
    if len(descripcion) > 255:
        raise ValueError("La descripción no puede superar 255 caracteres")
    return descripcion


def validar_precio(precio):
    """El precio debe ser numérico y mayor a 0."""
    if precio is None:
        raise ValueError("El precio no puede ser nulo")
    try:
        precio = float(precio)
    except (ValueError, TypeError):
        raise ValueError("El precio debe ser un número")
    if not math.isfinite(precio):
        raise ValueError("El precio debe ser un número finito")
    if precio <= 0:
        raise ValueError("El precio debe ser mayor a 0")
    if precio > 99999999.99:
        raise ValueError("El precio es demasiado alto")
    return round(precio, 2)


def validar_cantidad(cantidad, permitir_cero=False):
    if cantidad is None or isinstance(cantidad, bool):
        raise ValueError("La cantidad debe ser un número")
    try:
        cantidad = float(cantidad)
    except (ValueError, TypeError):
        raise ValueError("La cantidad debe ser un número")
    if not math.isfinite(cantidad):
        raise ValueError("La cantidad debe ser un número finito")
    minimo = 0 if permitir_cero else 0.001
    if cantidad < minimo:
        mensaje = "La cantidad no puede ser negativa" if permitir_cero else "La cantidad debe ser mayor a 0"
        raise ValueError(mensaje)
    if cantidad > 999999999.999:
        raise ValueError("La cantidad es demasiado alta")
    return round(cantidad, 3)


def validar_unidad_medida(unidad_medida):
    if not isinstance(unidad_medida, str):
        raise ValueError("La unidad de medida debe ser texto")
    unidad_medida = unidad_medida.strip()
    if not unidad_medida:
        raise ValueError("La unidad de medida es obligatoria")
    if len(unidad_medida) > 30:
        raise ValueError("La unidad de medida no puede superar 30 caracteres")
    return unidad_medida


def validar_fecha_vencimiento(fecha):
    """La fecha debe ser válida y futura."""
    if fecha is None:
        raise ValueError("La fecha de vencimiento no puede ser nula")

    if isinstance(fecha, str):
        try:
            fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD")

    if not isinstance(fecha, date):
        raise ValueError("La fecha debe ser un objeto date")

    if fecha <= date.today():
        raise ValueError("La fecha de vencimiento debe ser futura")

    return fecha


def validar_producto(
    nombre,
    descripcion,
    precio,
    fecha_vencimiento,
    cantidad_stock=0,
    unidad_medida="unidad",
    precio_por_unidad=None,
):
    """Orquesta todas las validaciones. Devuelve datos limpios."""
    precio_validado = validar_precio(precio if precio_por_unidad is None else precio_por_unidad)
    return {
        "nombre": validar_nombre(nombre),
        "descripcion": validar_descripcion(descripcion),
        "precio": precio_validado,
        "precio_por_unidad": precio_validado,
        "cantidad_stock": validar_cantidad(cantidad_stock, permitir_cero=True),
        "unidad_medida": validar_unidad_medida(unidad_medida),
        "fecha_vencimiento": validar_fecha_vencimiento(fecha_vencimiento),
    }