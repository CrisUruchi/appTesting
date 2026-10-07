from getpass import getpass

from werkzeug.security import generate_password_hash

from models import UsuarioRepository


def main():
    nombre = input("Nombre completo: ").strip()
    correo = input("Correo: ").strip().lower()
    rol = input("Perfil (admin/compras/vendedor): ").strip().lower()
    if rol not in {"admin", "compras", "vendedor"}:
        raise SystemExit("Perfil inválido.")

    contrasena = getpass("Contraseña (mínimo 8 caracteres): ")
    confirmacion = getpass("Confirmar contraseña: ")
    if len(contrasena) < 8 or contrasena != confirmacion:
        raise SystemExit("Las contraseñas no coinciden o tienen menos de 8 caracteres.")

    UsuarioRepository().crear(
        nombre, correo, generate_password_hash(contrasena), rol
    )
    print(f"Usuario {correo} creado con perfil {rol}.")


if __name__ == "__main__":
    main()