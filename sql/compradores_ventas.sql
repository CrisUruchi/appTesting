-- Ejecutar una sola vez sobre crud_productos después de la migración de inventario.
CREATE TABLE compradores (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_compradores_nombre (apellido, nombre),
    INDEX idx_compradores_telefono (telefono)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- NULL preserva las ventas históricas anteriores al registro de compradores.
-- La API exige comprador_id para todas las ventas nuevas.
ALTER TABLE ventas
    ADD COLUMN comprador_id INT UNSIGNED NULL AFTER vendedor_id,
    ADD CONSTRAINT fk_ventas_comprador FOREIGN KEY (comprador_id)
        REFERENCES compradores(id) ON DELETE RESTRICT,
    ADD INDEX idx_ventas_comprador_fecha (comprador_id, vendido_en);