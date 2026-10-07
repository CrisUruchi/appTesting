# Acceso y perfiles

## Inicialización

1. Ejecuta `sql/crear_tabla_usuarios.sql` en la base de datos `crud_productos` si aún no lo hiciste.
2. Crea la tabla de ventas y los campos de inventario ejecutando una sola vez `sql/actualizar_inventario_y_ventas.sql`. El stock inicial queda en cero; la migración copia el precio existente a `precio_por_unidad`.
3. Crea la tabla de compradores y agrega el vínculo a ventas ejecutando una sola vez `sql/compradores_ventas.sql`.
4. Crea la primera cuenta gerente desde la carpeta del proyecto con `python crear_usuario.py`. El asistente solicita nombre, correo y contraseña; la contraseña se guarda como hash.
5. Inicia Flask como antes (`python app.py`) y entra en `http://localhost:5000`.
6. Inicia sesión como gerente. Desde **Cuentas de usuario** puedes crear usuarios con cualquiera de los tres perfiles.

El campo `precio` anterior se conserva por compatibilidad y se sincroniza con `precio_por_unidad`. El stock es decimal para permitir cantidades fraccionarias (por ejemplo, 0.250 kg). El formulario valida contraseñas de al menos 8 caracteres.

## Permisos

| Perfil | Productos | Ventas | Cuentas |
| --- | --- | --- |
| Gerente (`admin`) | Consultar, crear, editar y eliminar | Registrar y consultar todas | Consultar y crear |
| Encargado de compras (`compras`) | Consultar, crear y editar stock | Sin acceso | Sin acceso |
| Vendedor (`vendedor`) | Solo consultar stock | Registrar ventas y consultar las propias | Sin acceso |

Los permisos se verifican en Flask; ocultar controles en la interfaz no es la única barrera. Los endpoints de productos ahora requieren iniciar sesión.
Cada venta guarda una copia del precio y unidad utilizados, el identificador del comprador seleccionado y descuenta el stock en la misma transacción. Los datos personales del comprador se conservan solo en `compradores` y el historial los muestra mediante una relación. Se rechaza la venta si el comprador no existe o la cantidad supera las existencias disponibles. Vendedores y gerentes pueden buscar y registrar compradores desde el formulario de venta.

## Pruebas de API

Los clientes de ejemplo conservan la cookie de sesión. Configura las credenciales de una cuenta gerente en PowerShell antes de ejecutarlos:

```powershell
python -m pytest 4_test_api_productos.py -v
python 3_api_client.py
```

`5_test_autenticacion.py` usa repositorios simulados y no necesita conexión a MySQL:

```powershell
python -m pytest 1_test_validaciones.py 5_test_autenticacion.py -v
```

## Prueba UI con Selenium

Usa `usuarios_prueba.json` y reemplaza el correo y la contraseña por los de una cuenta local con perfil `admin` o `compras`. El archivo real está excluido de Git para no publicar contraseñas. Con Flask activo en `http://localhost:5000`, ejecuta:

```powershell
python -m pytest 7_pruebaUISelenium.py -v
```

Selenium abre Chrome visible. Al terminar, el producto creado permanece en la base de datos para que puedas verificarlo. Puedes cambiar la URL de Flask con `SELENIUM_BASE_URL`.

## Prueba UI con Cypress

La prueba `8_pruebaUICypress.cy.js` verifica el mismo login exitoso que Selenium y lee las credenciales de `usuarios_prueba.json`. Usa una cuenta local con perfil `admin` o `compras`. Instala las dependencias de Node una vez con `npm.cmd install`, inicia Flask y ejecuta:

```powershell
npm.cmd run test:cypress
```

Para recorrerla en el navegador interactivo usa `npm.cmd run cypress:open`. Cypress usa `http://localhost:5000` por defecto; puedes cambiarlo con `SELENIUM_BASE_URL` o `CYPRESS_BASE_URL`. Si el archivo no contiene una cuenta `admin` o `compras`, el caso se marca como omitido.

Define `FLASK_SECRET_KEY` con un valor aleatorio privado en cualquier despliegue compartido. La clave predeterminada solo sirve para desarrollo local. Al publicar sobre HTTPS, configura también `FLASK_COOKIE_SECURE=1` para que el navegador solo envíe la cookie por conexiones seguras.