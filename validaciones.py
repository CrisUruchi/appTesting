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
    if precio <= 0:
        raise ValueError("El precio debe ser mayor a 0")
    if precio > 99999999.99:
        raise ValueError("El precio es demasiado alto")
    return round(precio, 2)


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


def validar_producto(nombre, descripcion, precio, fecha_vencimiento):
    """Orquesta todas las validaciones. Devuelve datos limpios."""
    return {
        "nombre": validar_nombre(nombre),
        "descripcion": validar_descripcion(descripcion),
        "precio": validar_precio(precio),
        "fecha_vencimiento": validar_fecha_vencimiento(fecha_vencimiento),
    }