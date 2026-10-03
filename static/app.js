const API = "/api/productos";
let editandoId = null;

const form = document.getElementById("form-producto");
const tbody = document.getElementById("tbody-productos");
const errorDiv = document.getElementById("error");
const btnGuardar = document.getElementById("btn-guardar");
const btnCancelar = document.getElementById("btn-cancelar");


function mostrarError(msg) {
    errorDiv.textContent = msg || "";
}


async function cargarProductos() {
    try {
        const res = await fetch(API);
        const data = await res.json();
        tbody.innerHTML = "";
        data.forEach(p => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${p.id}</td>
                <td>${p.nombre}</td>
                <td>${p.descripcion || ""}</td>
                <td>${p.precio}</td>
                <td>${p.fecha_vencimiento}</td>
                <td class="acciones">
                    <button onclick="editar(${p.id})">Editar</button>
                    <button onclick="eliminar(${p.id})">Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        mostrarError("Error al cargar productos");
    }
}


form.addEventListener("submit", async (e) => {
    e.preventDefault();
    mostrarError("");

    const payload = {
        nombre: document.getElementById("nombre").value,
        descripcion: document.getElementById("descripcion").value,
        precio: parseFloat(document.getElementById("precio").value),
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
    document.getElementById("fecha_vencimiento").value = p.fecha_vencimiento;
    editandoId = id;
    btnGuardar.textContent = "Actualizar";
    btnCancelar.style.display = "inline-block";
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
    btnGuardar.textContent = "Crear";
    btnCancelar.style.display = "none";
    document.getElementById("id").value = "";
}


btnCancelar.addEventListener("click", resetForm);


// Cargar al inicio
cargarProductos();