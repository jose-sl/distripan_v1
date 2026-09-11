/* ==========================================================
   SISTEMA LOGÍSTICO PARA DISTRIBUIDORA
   SCRIPT COMPLETO DE INSTALACIÓN
   ========================================================== */

SET FOREIGN_KEY_CHECKS = 0;

/* ==========================================================
   DROP TABLES
   ========================================================== */

DROP TABLE IF EXISTS alertas;
DROP TABLE IF EXISTS detalle_movimiento;
DROP TABLE IF EXISTS movimientos_inventario;
DROP TABLE IF EXISTS detalle_pedido;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS rutas_distribucion;
DROP TABLE IF EXISTS recetas_producto;
DROP TABLE IF EXISTS materias_primas;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS revendedores;
DROP TABLE IF EXISTS distribuidora;
DROP TABLE IF EXISTS usuarios;

SET FOREIGN_KEY_CHECKS = 1;

/* ==========================================================
   USUARIOS
   ========================================================== */

CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,

    rol ENUM(
        'ADMINISTRADOR',
        'REVENDEDOR',
        'PRODUCCION',
        'DESPACHO'
    ) NOT NULL,

    estado BOOLEAN DEFAULT TRUE,

    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

/* ==========================================================
   DISTRIBUIDORA
   ========================================================== */

CREATE TABLE distribuidora (
    id_distribuidora INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

/* ==========================================================
   REVENDEDORES
   ========================================================== */

CREATE TABLE revendedores (
    id_revendedor INT AUTO_INCREMENT PRIMARY KEY,

    id_usuario INT NOT NULL,

    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL,
    telefono VARCHAR(20),
    zona VARCHAR(50),

    latitud DECIMAL(10,8),
    longitud DECIMAL(11,8),

    estado BOOLEAN DEFAULT TRUE,

    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_revendedor_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON DELETE RESTRICT
);

/* ==========================================================
   PRODUCTOS
   ========================================================== */

CREATE TABLE productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(200),

    precio DECIMAL(10,2) NOT NULL,

    stock_actual INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 0,

    estado BOOLEAN DEFAULT TRUE,

    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

/* ==========================================================
   MATERIAS PRIMAS
   ========================================================== */

CREATE TABLE materias_primas (
    id_materia INT AUTO_INCREMENT PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL,

    unidad_medida VARCHAR(20) NOT NULL,

    stock_actual DECIMAL(10,2) DEFAULT 0,
    stock_minimo DECIMAL(10,2) DEFAULT 0,

    estado BOOLEAN DEFAULT TRUE,

    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

/* ==========================================================
   RECETAS DE PRODUCCIÓN
   ========================================================== */

CREATE TABLE recetas_producto (
    id_receta INT AUTO_INCREMENT PRIMARY KEY,

    id_producto INT NOT NULL,
    id_materia INT NOT NULL,

    cantidad_requerida DECIMAL(10,4) NOT NULL,

    CONSTRAINT fk_receta_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
        ON DELETE CASCADE,

    CONSTRAINT fk_receta_materia
        FOREIGN KEY (id_materia)
        REFERENCES materias_primas(id_materia),

    CONSTRAINT uk_receta_producto_materia
        UNIQUE (id_producto, id_materia)
);

/* ==========================================================
   RUTAS DE DISTRIBUCIÓN
   ========================================================== */

CREATE TABLE rutas_distribucion (
    id_ruta INT AUTO_INCREMENT PRIMARY KEY,

    fecha_ruta DATE NOT NULL,

    zona VARCHAR(50) NOT NULL,

    estado ENUM(
        'PLANIFICADA',
        'CONFIRMADA',
        'EN_EJECUCION',
        'FINALIZADA'
    ) DEFAULT 'PLANIFICADA',

    id_usuario_despacho INT NOT NULL,

    CONSTRAINT fk_ruta_usuario
        FOREIGN KEY (id_usuario_despacho)
        REFERENCES usuarios(id_usuario)
);

/* ==========================================================
   PEDIDOS
   ========================================================== */

CREATE TABLE pedidos (
    id_pedido INT AUTO_INCREMENT PRIMARY KEY,

    id_distribuidora INT NOT NULL,
    id_revendedor INT NOT NULL,
    id_usuario INT NOT NULL,

    id_ruta INT NULL,

    fecha_pedido DATETIME DEFAULT CURRENT_TIMESTAMP,

    estado ENUM(
        'PENDIENTE',
        'EN_PRODUCCION',
        'LISTO_PARA_DESPACHO',
        'EN_RUTA',
        'ENTREGADO',
        'CANCELADO'
    ) DEFAULT 'PENDIENTE',

    total DECIMAL(12,2) DEFAULT 0,

    CONSTRAINT fk_pedido_distribuidora
        FOREIGN KEY (id_distribuidora)
        REFERENCES distribuidora(id_distribuidora),

    CONSTRAINT fk_pedido_revendedor
        FOREIGN KEY (id_revendedor)
        REFERENCES revendedores(id_revendedor),

    CONSTRAINT fk_pedido_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario),

    CONSTRAINT fk_pedido_ruta
        FOREIGN KEY (id_ruta)
        REFERENCES rutas_distribucion(id_ruta)
);

/* ==========================================================
   DETALLE PEDIDO
   ========================================================== */

CREATE TABLE detalle_pedido (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,

    id_pedido INT NOT NULL,
    id_producto INT NOT NULL,

    cantidad INT NOT NULL,

    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_detalle_pedido
        FOREIGN KEY (id_pedido)
        REFERENCES pedidos(id_pedido)
        ON DELETE CASCADE,

    CONSTRAINT fk_detalle_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto)
);

/* ==========================================================
   MOVIMIENTOS INVENTARIO
   ========================================================== */

CREATE TABLE movimientos_inventario (
    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,

    fecha_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP,

    tipo_movimiento ENUM(
        'ENTRADA',
        'SALIDA'
    ) NOT NULL,

    observaciones VARCHAR(200),

    id_usuario INT NOT NULL,

    CONSTRAINT fk_movimiento_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
);

/* ==========================================================
   DETALLE MOVIMIENTO
   ========================================================== */

CREATE TABLE detalle_movimiento (
    id_detalle_movimiento INT AUTO_INCREMENT PRIMARY KEY,

    id_movimiento INT NOT NULL,

    id_producto INT NULL,
    id_materia INT NULL,

    cantidad DECIMAL(10,2) NOT NULL,

    CONSTRAINT fk_det_mov_movimiento
        FOREIGN KEY (id_movimiento)
        REFERENCES movimientos_inventario(id_movimiento)
        ON DELETE CASCADE,

    CONSTRAINT fk_det_mov_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto),

    CONSTRAINT fk_det_mov_materia
        FOREIGN KEY (id_materia)
        REFERENCES materias_primas(id_materia)
);

/* ==========================================================
   ALERTAS
   ========================================================== */

CREATE TABLE alertas (
    id_alerta INT AUTO_INCREMENT PRIMARY KEY,

    descripcion VARCHAR(255) NOT NULL,

    estado ENUM(
        'PENDIENTE',
        'ATENDIDA'
    ) DEFAULT 'PENDIENTE',

    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,

    id_producto INT NULL,
    id_materia INT NULL,

    CONSTRAINT fk_alerta_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos(id_producto),

    CONSTRAINT fk_alerta_materia
        FOREIGN KEY (id_materia)
        REFERENCES materias_primas(id_materia)
);

/* ==========================================================
   ÍNDICES
   ========================================================== */

CREATE INDEX idx_productos_nombre
ON productos(nombre);

CREATE INDEX idx_revendedores_nombre
ON revendedores(nombre);

CREATE INDEX idx_revendedores_mapa
ON revendedores(latitud, longitud);

CREATE INDEX idx_pedidos_estado
ON pedidos(estado);

CREATE INDEX idx_pedidos_fecha
ON pedidos(fecha_pedido);

CREATE INDEX idx_rutas_fecha
ON rutas_distribucion(fecha_ruta);

CREATE INDEX idx_movimientos_fecha
ON movimientos_inventario(fecha_movimiento);

CREATE INDEX idx_alertas_estado
ON alertas(estado);

CREATE INDEX idx_recetas_producto
ON recetas_producto(id_producto);

CREATE INDEX idx_recetas_materia
ON recetas_producto(id_materia);

/* ==========================================================
   DATOS INICIALES
   ========================================================== */

INSERT INTO distribuidora (
    nombre
)
VALUES (
    'Distribuidora San Francisco'
);

INSERT INTO usuarios (
    nombre,
    usuario,
    contrasena,
    rol
)
VALUES
(
    'ADMIN',
    'admin',
    'admin123',
    'ADMINISTRADOR'
),
(
    'San Francisco',
    'francisco',
    'francisco123',
    'REVENDEDOR'
),
(
    'Esquipulas',
    'esquipulas',
    'esquipulas123',
    'REVENDEDOR'
);

INSERT INTO revendedores (
    id_usuario,
    nombre,
    direccion,
    telefono,
    zona,
    latitud,
    longitud
)
VALUES
(
    2,
    'Panadería San Francisco',
    '2 calle',
    '11111111',
    '2',
    14.56960600,
    -90.49842200
),
(
    3,
    'Panadería Esquipulas',
    '5 avenida',
    '22222222',
    '2',
    14.567795,
    -90.497767
);

INSERT INTO alertas (
    descripcion
) VALUES (
    'Cantidad de harina por debajo de 2 paquetes'
);

/* ==========================================================
   PRODUCTOS INICIALES
   ========================================================== */

INSERT INTO productos
(
    nombre,
    descripcion,
    precio,
    stock_actual,
    stock_minimo,
    estado
)
VALUES
(
    'Pan Francés',
    'Pan francés tradicional',
    0.50,
    0,
    0,
    1
),
(
    'Champurradas',
    'Galleta tradicional tipo champurrada',
    1.50,
    0,
    0,
    1
),
(
    'Cubiletes',
    'Pan dulce tipo cubilete',
    2.00,
    0,
    0,
    1
),
(
    'Pan Redondo',
    'Pan redondo tradicional',
    1.00,
    0,
    0,
    1
),
(
    'Pirujo Grande',
    'Pirujo tamaño grande',
    1.25,
    0,
    0,
    1
),
(
    'Pirujo Pequeño',
    'Pirujo tamaño pequeño',
    0.75,
    0,
    0,
    1
),
(
    'Campechanas',
    'Pan dulce tipo campechana',
    2.50,
    0,
    0,
    1
),
(
    'Pan Tostado',
    'Pan tostado para consumo y distribución',
    1.50,
    0,
    0,
    1
),
(
    'Pan de Queso',
    'Pan elaborado con queso',
    2.25,
    0,
    0,
    1
);

/* ==========================================================
   MATERIAS PRIMAS INICIALES
   ========================================================== */

INSERT INTO materias_primas
(
    nombre,
    unidad_medida,
    stock_actual,
    stock_minimo,
    estado
)
VALUES
(
    'Harina',
    'Kg',
    120.50,
    20.00,
    1
),
(
    'Azúcar',
    'Kg',
    50.75,
    10.00,
    1
),
(
    'Manteca',
    'Kg',
    18.25,
    5.00,
    1
),
(
    'Levadura',
    'Kg',
    10.50,
    2.00,
    1
),
(
    'Queso',
    'Kg',
    25.00,
    5.00,
    1
),
(
    'Huevos',
    'Unidad',
    500.00,
    100.00,
    1
),
(
    'Sal',
    'Kg',
    15.00,
    3.00,
    1
),
(
    'Leche',
    'Litro',
    40.00,
    10.00,
    1
),
(
    'Margarina',
    'Kg',
    25.00,
    5.00,
    1
),
(
    'Aceite',
    'Litro',
    20.00,
    5.00,
    1
),
(
    'Polvo para Hornear',
    'Kg',
    5.00,
    1.00,
    1
),
(
    'Ajonjolí',
    'Kg',
    3.00,
    0.50,
    1
),
(
    'Vainilla',
    'Litro',
    2.00,
    0.50,
    1
),
(
    'Canela',
    'Kg',
    2.50,
    0.50,
    1
),
(
    'Agua',
    'Litro',
    500.00,
    100.00,
    1
);
