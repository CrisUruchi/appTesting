const { defineConfig } = require("cypress");
const fs = require("node:fs");
const path = require("node:path");

function leerCredenciales() {
    const archivo = path.join(__dirname, "usuarios_prueba.json");
    if (!fs.existsSync(archivo)) {
        throw new Error(`No existe ${path.basename(archivo)}.`);
    }

    let datos;
    try {
        datos = JSON.parse(fs.readFileSync(archivo, "utf8"));
    } catch (error) {
        throw new Error(`No se pudo leer ${path.basename(archivo)}: ${error.message}`);
    }

    if (!datos || !Array.isArray(datos.usuarios)) {
        throw new Error(`${path.basename(archivo)} debe contener una lista llamada "usuarios".`);
    }

    const usuario = datos.usuarios.find(cuenta =>
        cuenta
        && ["admin", "compras"].includes(cuenta.rol)
        && cuenta.correo
        && cuenta.contrasena
    );

    return usuario
        ? { correo: usuario.correo, contrasena: usuario.contrasena }
        : { correo: "", contrasena: "" };
}

const credenciales = leerCredenciales();

module.exports = defineConfig({
    e2e: {
        baseUrl: process.env.CYPRESS_BASE_URL
            || process.env.SELENIUM_BASE_URL
            || "http://localhost:5000",
        specPattern: "8_pruebaUICypress.cy.js",
    },
    env: credenciales,
});