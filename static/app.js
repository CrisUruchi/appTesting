const API = "/api/productos";
let editandoId = null;
let compradorSeleccionado = null;
let temporizadorBusquedaCompradores = null;

const vistaLogin = document.getElementById("vista-login");
const vistaApp = document.getElementById("vista-app");
const formLogin = document.getElementById("form-login");
const form = document.getElementById("form-producto");
const tbody = document.getElementById("tbody-productos");
const errorDiv = document.getElementById("error");
const btnGuardar = document.getElementById("btn-guardar");
const btnCancelar = document.getElementById("btn-cancelar");
const seccionProducto = document.getElementById("seccion-producto");
const seccionUsuarios = document.getElementById("seccion-usuarios");
const seccionVentas = document.getElementById("seccion-ventas");
const perfilNombres = { admin: "Gerente", compras: "Encargado de compras", vendedor: "Vendedor" };


function mostrarError(msg) {
    errorDiv.textContent = msg || "";
}


async function cargarProductos() {
    try {
        const res = await fetch(API);
        if (res.status === 401) return mostrarLogin();
        const data = await res.json();
        tbody.innerHTML = "";
        const selectorVenta = document.getElementById("producto-venta");
        if (selectorVenta) {
            selectorVenta.replaceChildren();
            data.forEach(producto => {
                const opcion = document.createElement("option");
                opcion.value = producto.id;
                opcion.textContent = `${producto.nombre} (${producto.cantidad_stock} ${producto.unidad_medida} disponibles)`;
                selectorVenta.appendChild(opcion);
            });
        }
        data.forEach(p => {
            const tr = document.createElement("tr");
            [p.id, p.nombre, p.descripcion || "", p.cantidad_stock,
                p.unidad_medida, `${Number(p.precio_por_unidad).toFixed(2)} / ${p.unidad_medida}`,
                p.fecha_vencimiento]
                .forEach(valor => {
                    const celda = document.createElement("td");
                    celda.textContent = valor;
                    tr.appendChild(celda);
                });
            if (window.usuarioActual.rol !== "vendedor") {
                const acciones = document.createElement("td");
                acciones.className = "acciones";
                const botonEditar = document.createElement("button");
                botonEditar.textContent = "Editar";
                botonEditar.addEventListener("click", () => editar(p.id));
                acciones.appendChild(botonEditar);
                if (window.usuarioActual.rol === "admin") {
                    const botonEliminar = document.createElement("button");
                    botonEliminar.textContent = "Eliminar";
                    botonEliminar.addEventListener("click", () => eliminar(p.id));
                    acciones.appendChild(botonEliminar);
                }
                tr.appendChild(acciones);
            }
            tbody.appendChild(tr);
        });
    } catch (e) {
        mostrarError("Error al cargar productos");
    }
}


function mostrarLogin(mensaje = "") {
    vistaLogin.hidden = false;
    vistaApp.hidden = true;
    document.getElementById("error-login").textContent = mensaje;
    window.usuarioActual = null;
}


async function mostrarAplicacion(usuario) {
    window.usuarioActual = usuario;
    vistaLogin.hidden = true;
    vistaApp.hidden = false;
    document.getElementById("usuario-nombre").textContent = usuario.nombre;
    document.getElementById("usuario-perfil").textContent = perfilNombres[usuario.rol];
    const esAdmin = usuario.rol === "admin";
    seccionProducto.hidden = usuario.rol === "vendedor";
    seccionUsuarios.hidden = !esAdmin;
    seccionVentas.hidden = !["admin", "vendedor"].includes(usuario.rol);
    document.getElementById("th-acciones").hidden = usuario.rol === "vendedor";
    document.getElementById("th-vendedor").hidden = !esAdmin;
    document.getElementById("contenido").classList.toggle("single", usuario.rol === "vendedor");
    await cargarProductos();
    if (esAdmin) await cargarUsuarios();
    if (["admin", "vendedor"].includes(usuario.rol)) await cargarVentas();
}


formLogin.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const respuesta = await fetch("/api/sesion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            correo: document.getElementById("correo-login").value,
            contrasena: document.getElementById("contrasena-login").value
        })
    });
    const data = await respuesta.json();
    if (!respuesta.ok) {
        document.getElementById("error-login").textContent = data.error || "No se pudo iniciar sesión";
        return;
    }
    formLogin.reset();
    await mostrarAplicacion(data);
});


document.getElementById("btn-salir").addEventListener("click", async () => {
    await fetch("/api/sesion", { method: "DELETE" });
    mostrarLogin();
});


async function cargarUsuarios() {
    const respuesta = await fetch("/api/usuarios");
    if (!respuesta.ok) return;
    const usuarios = await respuesta.json();
    const cuerpo = document.getElementById("tbody-usuarios");
    cuerpo.innerHTML = "";
    usuarios.forEach(usuario => {
        const fila = document.createElement("tr");
        [usuario.nombre, usuario.correo, perfilNombres[usuario.rol]].forEach(valor => {
            const celda = document.createElement("td");
            celda.textContent = valor;
            fila.appendChild(celda);
        });
        cuerpo.appendChild(fila);
    });
}


document.getElementById("form-usuario").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const respuesta = await fetch("/api/usuarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            nombre: document.getElementById("nombre-usuario").value,
            correo: document.getElementById("correo-usuario").value,
            contrasena: document.getElementById("contrasena-usuario").value,
            rol: document.getElementById("rol-usuario").value
        })
    });
    const data = await respuesta.json();
    const errorUsuarios = document.getElementById("error-usuarios");
    errorUsuarios.textContent = respuesta.ok ? "Cuenta creada" : (data.error || "No se pudo crear la cuenta");
    errorUsuarios.classList.toggle("success", respuesta.ok);
    if (respuesta.ok) {
        evento.target.reset();
        await cargarUsuarios();
    }
});


async function cargarVentas() {
    const respuesta = await fetch("/api/ventas");
    if (!respuesta.ok) return;
    const historial = await respuesta.json();
    const cuerpo = document.getElementById("tbody-ventas");
    cuerpo.innerHTML = "";
    historial.forEach(venta => {
        const fila = document.createElement("tr");
        const celdas = [
            new Date(venta.vendido_en).toLocaleString(),
            venta.producto_nombre,
            `${venta.comprador_nombre || ""} ${venta.comprador_apellido || ""}`.trim(),
            `${venta.cantidad} ${venta.unidad_medida}`,
            Number(venta.precio_por_unidad).toFixed(2),
            Number(venta.total).toFixed(2)
        ];
        if (window.usuarioActual.rol === "admin") celdas.push(venta.vendedor_nombre);
        celdas.forEach(valor => {
            const celda = document.createElement("td");
            celda.textContent = valor;
            fila.appendChild(celda);
        });
        cuerpo.appendChild(fila);
    });
}


function seleccionarComprador(comprador) {
    compradorSeleccionado = comprador;
    document.getElementById("comprador-id").value = comprador.id;
    document.getElementById("buscar-comprador").value = `${comprador.nombre} ${comprador.apellido}`;
    document.getElementById("comprador-seleccionado").textContent = `Teléfono: ${comprador.telefono}`;
    document.getElementById("resultados-compradores").replaceChildren();
}


document.getElementById("buscar-comprador").addEventListener("input", (evento) => {
    const termino = evento.target.value.trim();
    compradorSeleccionado = null;
    document.getElementById("comprador-id").value = "";
    document.getElementById("comprador-seleccionado").textContent = "";
    clearTimeout(temporizadorBusquedaCompradores);
    const resultados = document.getElementById("resultados-compradores");
    resultados.replaceChildren();
    if (termino.length < 2) return;

    temporizadorBusquedaCompradores = setTimeout(async () => {
        const respuesta = await fetch(`/api/compradores?buscar=${encodeURIComponent(termino)}`);
        if (!respuesta.ok) return;
        const encontrados = await respuesta.json();
        encontrados.forEach(comprador => {
            const opcion = document.createElement("button");
            opcion.type = "button";
            opcion.setAttribute("role", "option");
            opcion.textContent = `${comprador.nombre} ${comprador.apellido} · ${comprador.telefono}`;
            opcion.addEventListener("click", () => seleccionarComprador(comprador));
            resultados.appendChild(opcion);
        });
        if (!encontrados.length) {
            const vacio = document.createElement("p");
            vacio.className = "muted";
            vacio.textContent = "No se encontraron compradores.";
            resultados.appendChild(vacio);
        }
    }, 180);
});


document.getElementById("form-comprador").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const respuesta = await fetch("/api/compradores", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            nombre: document.getElementById("nombre-comprador").value,
            apellido: document.getElementById("apellido-comprador").value,
            telefono: document.getElementById("telefono-comprador").value
        })
    });
    const data = await respuesta.json();
    const errorVentas = document.getElementById("error-ventas");
    if (!respuesta.ok) {
        errorVentas.textContent = data.error || "No se pudo registrar al comprador";
        errorVentas.classList.remove("success");
        return;
    }
    seleccionarComprador(data);
    evento.target.reset();
    evento.target.closest("details").open = false;
    errorVentas.textContent = "Comprador registrado y seleccionado.";
    errorVentas.classList.add("success");
});


document.getElementById("form-venta").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    if (!compradorSeleccionado) {
        document.getElementById("error-ventas").textContent = "Busca y selecciona un comprador registrado.";
        return;
    }
    const respuesta = await fetch("/api/ventas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            producto_id: Number(document.getElementById("producto-venta").value),
            comprador_id: compradorSeleccionado.id,
            cantidad: Number(document.getElementById("cantidad-venta").value)
        })
    });
    const data = await respuesta.json();
    const errorVentas = document.getElementById("error-ventas");
    errorVentas.textContent = respuesta.ok
        ? `Venta registrada: ${data.cantidad} ${data.unidad_medida} de ${data.producto_nombre}, total ${Number(data.total).toFixed(2)}`
        : (data.disponible !== undefined
            ? `${data.error}. Disponible: ${data.disponible}`
            : (data.error || "No se pudo registrar la venta"));
    errorVentas.classList.toggle("success", respuesta.ok);
    if (respuesta.ok) {
        document.getElementById("cantidad-venta").value = "";
        await cargarProductos();
        await cargarVentas();
    }
});


form.addEventListener("submit", async (e) => {
    e.preventDefault();
    mostrarError("");

    const payload = {
        nombre: document.getElementById("nombre").value,
        descripcion: document.getElementById("descripcion").value,
        precio: parseFloat(document.getElementById("precio").value),
        precio_por_unidad: parseFloat(document.getElementById("precio").value),
        cantidad_stock: parseFloat(document.getElementById("cantidad-stock").value),
        unidad_medida: document.getElementById("unidad-medida").value,
        fecha_vencimiento: document.getElementById("fecha_vencimiento").value
    };

    const url = editandoId ? `${API}/${editandoId}` : API;
    const method = editandoId ? "PUT" : "POST";

    const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
        mostrarError(data.error || "Error al guardar");
        return;
    }

    resetForm();
    cargarProductos();
});


async function editar(id) {
    const res = await fetch(`${API}/${id}`);
    const p = await res.json();
    document.getElementById("id").value = p.id;
    document.getElementById("nombre").value = p.nombre;
    document.getElementById("descripcion").value = p.descripcion || "";
    document.getElementById("precio").value = p.precio;
    document.getElementById("cantidad-stock").value = p.cantidad_stock;
    document.getElementById("unidad-medida").value = p.unidad_medida;
    document.getElementById("fecha_vencimiento").value = p.fecha_vencimiento;
    editandoId = id;
    btnGuardar.textContent = "Actualizar";
    btnCancelar.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
}


async function eliminar(id) {
    if (!confirm("¿Eliminar producto?")) return;
    const res = await fetch(`${API}/${id}`, { method: "DELETE" });
    if (res.ok) cargarProductos();
    else mostrarError("Error al eliminar");
}


function resetForm() {
    form.reset();
    editandoId = null;
    btnGuardar.textContent = "Crear producto";
    btnCancelar.hidden = true;
    document.getElementById("id").value = "";
}


btnCancelar.addEventListener("click", resetForm);


fetch("/api/sesion")
    .then(respuesta => respuesta.ok ? respuesta.json() : null)
    .then(usuario => usuario ? mostrarAplicacion(usuario) : mostrarLogin())
    .catch(() => mostrarLogin());