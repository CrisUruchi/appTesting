-- Ejecutar una sola vez sobre la base crud_productos.
-- El stock inicial queda en cero porque no se conoce el inventario actual.
ALTER TABLE productos
    ADD COLUMN cantidad_stock DECIMAL(12,3) NOT NULL DEFAULT 0,
    ADD COLUMN unidad_medida VARCHAR(30) NOT NULL DEFAULT 'unidad',
    ADD COLUMN precio_por_unidad DECIMAL(12,2) NOT NULL DEFAULT 0;

-- Mantiene el precio ya registrado como precio de una unidad de medida.
UPDATE productos SET precio_por_unidad = precio;

CREATE TABLE ventas (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    vendedor_id INT UNSIGNED NOT NULL,
    producto_nombre VARCHAR(100) NOT NULL,
    cantidad DECIMAL(12,3) NOT NULL,
    unidad_medida VARCHAR(30) NOT NULL,
    precio_por_unidad DECIMAL(12,2) NOT NULL,
    total DECIMAL(14,2) NOT NULL,
    vendido_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_ventas_cantidad CHECK (cantidad > 0),
    CONSTRAINT fk_ventas_producto FOREIGN KEY (producto_id)
        REFERENCES productos(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ventas_vendedor FOREIGN KEY (vendedor_id)
        REFERENCES usuarios(id) ON DELETE RESTRICT,
    INDEX idx_ventas_vendedor_fecha (vendedor_id, vendido_en),
    INDEX idx_ventas_producto_fecha (producto_id, vendido_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;