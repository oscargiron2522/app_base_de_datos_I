-- =============================================================================
-- Plataforma de Apuestas Deportivas y Pronósticos
-- Script de creación de base de datos - SQL Server (T-SQL)
-- Convertido a partir del script original de MySQL 8.0+
-- Nomenclatura: prefijo tbl_ , nombres de tabla y columna en español,
-- snake_case, siguiendo la normativa ya utilizada en el proyecto original.
--
-- Notas de conversión respecto al script MySQL original:
--   * AUTO_INCREMENT           -> IDENTITY(1,1)
--   * ENUM(...)                -> NVARCHAR(n) + CHECK constraint
--   * TINYINT(1) (booleano)    -> BIT
--   * INT/SMALLINT UNSIGNED    -> INT/SMALLINT + CHECK (col >= 0)
--   * DATETIME DEFAULT
--     CURRENT_TIMESTAMP        -> DATETIME2 DEFAULT SYSDATETIME()
--   * TEXT                     -> NVARCHAR(MAX)
--   * COMMENT '...'            -> eliminado (usar sp_addextendedproperty si se desea)
--   * INDEX inline en CREATE
--     TABLE                    -> CREATE INDEX independiente al final de cada tabla
--   * UNIQUE KEY nombre (...)  -> CONSTRAINT nombre UNIQUE (...)
--   * ENGINE=InnoDB DEFAULT
--     CHARSET=utf8mb4          -> eliminado (no aplica en SQL Server)
--
-- El orden de creación de tablas se conserva igual al original (ya respeta
-- las dependencias de llaves foráneas), por lo que no hace falta deshabilitar
-- la verificación de FKs como en MySQL (SET FOREIGN_KEY_CHECKS = 0).
-- =============================================================================

-- Crea la base de datos solo si no existe. Ajusta el nombre si lo necesitas.
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'bd_apuestas_deportivas')
BEGIN
    CREATE DATABASE bd_apuestas_deportivas;
END
GO

USE bd_apuestas_deportivas;
GO

-- =============================================================================
-- 1. CATÁLOGOS GENERALES
-- =============================================================================

CREATE TABLE tbl_pais (
    id_pais      INT IDENTITY(1,1) PRIMARY KEY,
    nombre_pais  NVARCHAR(100) NOT NULL,
    codigo_iso   NVARCHAR(5)   NOT NULL
);
GO

CREATE TABLE tbl_estado (
    id_estado         INT IDENTITY(1,1) PRIMARY KEY,
    nombre_estado     NVARCHAR(50)  NOT NULL,
    comentario_estado NVARCHAR(255) NULL
);
GO

CREATE TABLE tbl_departamento (
    id_departamento         INT IDENTITY(1,1) PRIMARY KEY,
    id_pais                 INT NOT NULL,
    nombre_departamento     NVARCHAR(100) NOT NULL,
    comentario_departamento NVARCHAR(255) NULL,
    CONSTRAINT fk_departamento_pais FOREIGN KEY (id_pais) REFERENCES tbl_pais(id_pais)
);
GO

CREATE TABLE tbl_municipio (
    id_municipio         INT IDENTITY(1,1) PRIMARY KEY,
    id_departamento      INT NOT NULL,
    nombre_municipio     NVARCHAR(100) NOT NULL,
    comentario_municipio NVARCHAR(255) NULL,
    CONSTRAINT fk_municipio_departamento FOREIGN KEY (id_departamento) REFERENCES tbl_departamento(id_departamento)
);
GO

CREATE TABLE tbl_deporte (
    id_deporte      INT IDENTITY(1,1) PRIMARY KEY,
    nombre_deporte  NVARCHAR(100) NOT NULL,
    id_estado       INT NOT NULL,
    CONSTRAINT fk_deporte_estado FOREIGN KEY (id_estado) REFERENCES tbl_estado(id_estado)
);
GO

CREATE TABLE tbl_liga (
    id_liga      INT IDENTITY(1,1) PRIMARY KEY,
    id_deporte   INT NOT NULL,
    id_pais      INT NOT NULL,
    nombre_liga  NVARCHAR(150) NOT NULL,
    CONSTRAINT fk_liga_deporte FOREIGN KEY (id_deporte) REFERENCES tbl_deporte(id_deporte),
    CONSTRAINT fk_liga_pais    FOREIGN KEY (id_pais)    REFERENCES tbl_pais(id_pais)
);
GO

CREATE TABLE tbl_equipo_atleta (
    id_equipo      INT IDENTITY(1,1) PRIMARY KEY,
    nombre_equipo  NVARCHAR(150) NOT NULL,
    id_deporte     INT NOT NULL,
    CONSTRAINT fk_equipo_deporte FOREIGN KEY (id_deporte) REFERENCES tbl_deporte(id_deporte)
);
GO

CREATE TABLE tbl_tipo_mercado (
    id_tipo_mercado  INT IDENTITY(1,1) PRIMARY KEY,
    nombre_mercado   NVARCHAR(100) NOT NULL
);
GO

CREATE TABLE tbl_metodo_pago (
    id_metodo_pago       INT IDENTITY(1,1) PRIMARY KEY,
    nombre_metodo        NVARCHAR(100) NOT NULL,
    comision_porcentaje  DECIMAL(5,2) NOT NULL DEFAULT 0.00
);
GO

CREATE TABLE tbl_pregunta_seguridad (
    id_pregunta     INT IDENTITY(1,1) PRIMARY KEY,
    texto_pregunta  NVARCHAR(255) NOT NULL
);
GO

-- =============================================================================
-- 2. LOGIN, USUARIOS, ADMINISTRADORES Y SEGURIDAD DE CUENTA
-- =============================================================================

-- contrasena_usuario: Hash de contraseña (nunca texto plano)
CREATE TABLE tbl_login (
    id_login               INT IDENTITY(1,1) PRIMARY KEY,
    id_sistema_us          NVARCHAR(50)  NOT NULL UNIQUE,
    nombre_usuario         NVARCHAR(100) NOT NULL UNIQUE,
    contrasena_usuario     NVARCHAR(255) NOT NULL,
    tipo_usuario           NVARCHAR(20) NOT NULL,
    fecha_registro_login   DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    intentos_fallidos      SMALLINT NOT NULL DEFAULT 0,
    bloqueado_hasta        DATETIME2 NULL,
    ultimo_cambio_password DATETIME2 NULL,
    CONSTRAINT chk_login_tipo_usuario CHECK (tipo_usuario IN ('USUARIO','ADMIN','SUPER_ADMIN')),
    CONSTRAINT chk_login_intentos_fallidos_no_negativo CHECK (intentos_fallidos >= 0)
);
GO

CREATE TABLE tbl_login_log (
    id_login_log          INT IDENTITY(1,1) PRIMARY KEY,
    id_login              INT NOT NULL,
    fecha_registro_log_us DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    ip_acceso             NVARCHAR(45) NOT NULL,
    CONSTRAINT fk_loginlog_login FOREIGN KEY (id_login) REFERENCES tbl_login(id_login) ON DELETE CASCADE
);
GO

CREATE TABLE tbl_usuario (
    id_usuario           INT IDENTITY(1,1) PRIMARY KEY,
    id_login             INT NOT NULL UNIQUE,
    primer_nombre_us     NVARCHAR(80) NOT NULL,
    segundo_nombre_us    NVARCHAR(80) NULL,
    primer_apellido_us   NVARCHAR(80) NOT NULL,
    segundo_apellido_us  NVARCHAR(80) NULL,
    apellido_casada_us   NVARCHAR(80) NULL,
    fecha_nacimiento_us  DATE NOT NULL,
    id_departamento_us   INT NOT NULL,
    id_municipio_us      INT NOT NULL,
    direccion_us         NVARCHAR(255) NOT NULL,
    correo_us            NVARCHAR(254) NOT NULL UNIQUE,
    telefono_us          NVARCHAR(20) NOT NULL,
    id_estado            INT NOT NULL,
    CONSTRAINT fk_usuario_login        FOREIGN KEY (id_login)           REFERENCES tbl_login(id_login) ON DELETE CASCADE,
    CONSTRAINT fk_usuario_departamento FOREIGN KEY (id_departamento_us) REFERENCES tbl_departamento(id_departamento),
    CONSTRAINT fk_usuario_municipio    FOREIGN KEY (id_municipio_us)    REFERENCES tbl_municipio(id_municipio),
    CONSTRAINT fk_usuario_estado       FOREIGN KEY (id_estado)          REFERENCES tbl_estado(id_estado)
);
GO

CREATE TABLE tbl_administrador (
    id_admin              INT IDENTITY(1,1) PRIMARY KEY,
    id_login              INT NOT NULL UNIQUE,
    codigo_empleado       NVARCHAR(30) NOT NULL UNIQUE,
    primer_nombre_admin   NVARCHAR(80) NOT NULL,
    primer_apellido_admin NVARCHAR(80) NOT NULL,
    departamento_empresa  NVARCHAR(100) NOT NULL,
    correo_corporativo    NVARCHAR(254) NOT NULL,
    rol_administrativo    NVARCHAR(20) NOT NULL DEFAULT 'OPERADOR_EVENTOS',
    id_estado             INT NOT NULL,
    CONSTRAINT fk_admin_login  FOREIGN KEY (id_login)  REFERENCES tbl_login(id_login) ON DELETE CASCADE,
    CONSTRAINT fk_admin_estado FOREIGN KEY (id_estado) REFERENCES tbl_estado(id_estado),
    CONSTRAINT chk_admin_rol CHECK (rol_administrativo IN ('OPERADOR_EVENTOS','CAJERO','AUDITOR'))
);
GO

CREATE TABLE tbl_super_administrador (
    id_super_admin    INT IDENTITY(1,1) PRIMARY KEY,
    id_login          INT NOT NULL UNIQUE,
    nombre_completo   NVARCHAR(150) NOT NULL,
    correo_maestro    NVARCHAR(254) NOT NULL,
    llave_mfa_secret  NVARCHAR(64) NULL,
    fecha_asignacion  DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_superadmin_login FOREIGN KEY (id_login) REFERENCES tbl_login(id_login) ON DELETE CASCADE
);
GO

-- respuesta_hash: Hash de la respuesta, nunca texto plano
CREATE TABLE tbl_usuario_pregunta_seguridad (
    id_usuario_pregunta  INT IDENTITY(1,1) PRIMARY KEY,
    id_login             INT NOT NULL,
    id_pregunta          INT NOT NULL,
    respuesta_hash       NVARCHAR(255) NOT NULL,
    CONSTRAINT fk_upresp_login    FOREIGN KEY (id_login)    REFERENCES tbl_login(id_login) ON DELETE CASCADE,
    CONSTRAINT fk_upresp_pregunta FOREIGN KEY (id_pregunta) REFERENCES tbl_pregunta_seguridad(id_pregunta),
    CONSTRAINT uq_login_pregunta UNIQUE (id_login, id_pregunta)
);
GO

CREATE TABLE tbl_recuperacion_password (
    id_recuperacion   INT IDENTITY(1,1) PRIMARY KEY,
    id_login          INT NOT NULL,
    token             CHAR(36) NOT NULL UNIQUE,
    fecha_solicitud   DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    fecha_expiracion  DATETIME2 NOT NULL,
    usado             BIT NOT NULL DEFAULT 0,
    ip_solicitud      NVARCHAR(45) NULL,
    CONSTRAINT fk_recuperacion_login FOREIGN KEY (id_login) REFERENCES tbl_login(id_login) ON DELETE CASCADE
);
GO

CREATE TABLE tbl_admin_log (
    id_admin_log       BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_login           INT NOT NULL,
    accion_realizada   NVARCHAR(255) NOT NULL,
    tabla_afectada     NVARCHAR(100) NOT NULL,
    fecha_registro     DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_adminlog_login FOREIGN KEY (id_login) REFERENCES tbl_login(id_login) ON DELETE CASCADE
);
GO

CREATE TABLE tbl_historial_sesiones (
    id_historial_sesion    BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_login               INT NOT NULL,
    ip_origen              NVARCHAR(45) NOT NULL,
    dispositivo_navegador  NVARCHAR(255) NOT NULL,
    resultado              NVARCHAR(10) NOT NULL,
    fecha_conexion         DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_histsesion_login FOREIGN KEY (id_login) REFERENCES tbl_login(id_login) ON DELETE CASCADE,
    CONSTRAINT chk_histsesion_resultado CHECK (resultado IN ('EXITOSO','FALLIDO'))
);
GO

CREATE TABLE tbl_historial_bloqueos_cuenta (
    id_historial_bloqueo  INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario            INT NOT NULL,
    motivo_bloqueo        NVARCHAR(255) NOT NULL,
    solicitado_por        NVARCHAR(10) NOT NULL,
    fecha_inicio_bloqueo  DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    fecha_fin_bloqueo     DATETIME2 NULL,
    CONSTRAINT fk_bloqueo_usuario FOREIGN KEY (id_usuario) REFERENCES tbl_usuario(id_usuario) ON DELETE CASCADE,
    CONSTRAINT chk_bloqueo_solicitado_por CHECK (solicitado_por IN ('SISTEMA','ADMIN','USUARIO'))
);
GO

CREATE TABLE tbl_intento_login (
    id_intento     BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_sistema_us  NVARCHAR(50) NULL,
    ip_origen      NVARCHAR(45) NOT NULL,
    exitoso        BIT NOT NULL DEFAULT 0,
    fecha_intento  DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX idx_intento_ip_fecha ON tbl_intento_login (ip_origen, fecha_intento);
GO
CREATE INDEX idx_intento_usuario_fecha ON tbl_intento_login (id_sistema_us, fecha_intento);
GO

-- =============================================================================
-- 3. BILLETERA VIRTUAL Y MOVIMIENTOS FINANCIEROS
-- =============================================================================

CREATE TABLE tbl_billetera (
    id_billetera       INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario         INT NOT NULL UNIQUE,
    saldo_disponible   DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    saldo_retenido     DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    id_estado          INT NOT NULL,
    CONSTRAINT fk_billetera_usuario FOREIGN KEY (id_usuario) REFERENCES tbl_usuario(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_billetera_estado  FOREIGN KEY (id_estado)  REFERENCES tbl_estado(id_estado),
    CONSTRAINT chk_saldo_disponible_no_negativo CHECK (saldo_disponible >= 0),
    CONSTRAINT chk_saldo_retenido_no_negativo   CHECK (saldo_retenido >= 0)
);
GO

CREATE TABLE tbl_transaccion (
    id_transaccion    BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_billetera      INT NOT NULL,
    id_metodo_pago    INT NULL,
    tipo_transaccion  NVARCHAR(15) NOT NULL,
    monto             DECIMAL(14,2) NOT NULL,
    fecha_hora        DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_transaccion_billetera FOREIGN KEY (id_billetera)   REFERENCES tbl_billetera(id_billetera) ON DELETE CASCADE,
    CONSTRAINT fk_transaccion_metodo    FOREIGN KEY (id_metodo_pago) REFERENCES tbl_metodo_pago(id_metodo_pago),
    CONSTRAINT chk_monto_transaccion_positivo CHECK (monto > 0),
    CONSTRAINT chk_transaccion_tipo CHECK (tipo_transaccion IN ('DEPOSITO','RETIRO','APUESTA','PREMIO','AJUSTE'))
);
GO

CREATE TABLE tbl_cuenta_bancaria_usuario (
    id_cuenta_bancaria  INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario          INT NOT NULL,
    nombre_banco        NVARCHAR(100) NOT NULL,
    numero_cuenta       NVARCHAR(40) NOT NULL,
    tipo_cuenta         NVARCHAR(10) NOT NULL,
    CONSTRAINT fk_cuentabancaria_usuario FOREIGN KEY (id_usuario) REFERENCES tbl_usuario(id_usuario) ON DELETE CASCADE,
    CONSTRAINT chk_cuentabancaria_tipo CHECK (tipo_cuenta IN ('MONETARIA','AHORRO'))
);
GO

CREATE TABLE tbl_solicitud_retiro (
    id_solicitud       INT IDENTITY(1,1) PRIMARY KEY,
    id_billetera       INT NOT NULL,
    id_cuenta_bancaria INT NOT NULL,
    monto_solicitado   DECIMAL(14,2) NOT NULL,
    estado_solicitud   NVARCHAR(15) NOT NULL DEFAULT 'PENDIENTE',
    fecha_solicitud    DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_solicitudretiro_billetera FOREIGN KEY (id_billetera)       REFERENCES tbl_billetera(id_billetera),
    CONSTRAINT fk_solicitudretiro_cuenta    FOREIGN KEY (id_cuenta_bancaria) REFERENCES tbl_cuenta_bancaria_usuario(id_cuenta_bancaria),
    CONSTRAINT chk_monto_retiro_positivo CHECK (monto_solicitado > 0),
    CONSTRAINT chk_solicitudretiro_estado CHECK (estado_solicitud IN ('PENDIENTE','APROBADA','RECHAZADA','PAGADA'))
);
GO

CREATE TABLE tbl_historial_saldo_billetera (
    id_historial_saldo  BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_billetera        INT NOT NULL,
    saldo_anterior      DECIMAL(14,2) NOT NULL,
    saldo_nuevo         DECIMAL(14,2) NOT NULL,
    monto_movimiento    DECIMAL(14,2) NOT NULL,
    tipo_operacion      NVARCHAR(20) NOT NULL,
    fecha_movimiento    DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_histsaldo_billetera FOREIGN KEY (id_billetera) REFERENCES tbl_billetera(id_billetera) ON DELETE CASCADE,
    CONSTRAINT chk_histsaldo_tipo_operacion CHECK (tipo_operacion IN ('DEPOSITO','RETIRO','DEBITO_APUESTA','CREDITO_PREMIO','RETENCION','LIBERACION','AJUSTE_ADMIN'))
);
GO

-- =============================================================================
-- 4. EVENTOS, MERCADOS Y OPCIONES DE APUESTA
-- =============================================================================

CREATE TABLE tbl_evento (
    id_evento            INT IDENTITY(1,1) PRIMARY KEY,
    id_liga              INT NOT NULL,
    id_equipo_local      INT NOT NULL,
    id_equipo_visitante  INT NOT NULL,
    fecha_inicio         DATETIME2 NOT NULL,
    estado_evento        NVARCHAR(15) NOT NULL DEFAULT 'PROGRAMADO',
    CONSTRAINT fk_evento_liga   FOREIGN KEY (id_liga)             REFERENCES tbl_liga(id_liga),
    CONSTRAINT fk_evento_local  FOREIGN KEY (id_equipo_local)     REFERENCES tbl_equipo_atleta(id_equipo),
    CONSTRAINT fk_evento_visita FOREIGN KEY (id_equipo_visitante) REFERENCES tbl_equipo_atleta(id_equipo),
    CONSTRAINT chk_evento_estado CHECK (estado_evento IN ('PROGRAMADO','EN_JUEGO','FINALIZADO','SUSPENDIDO','CANCELADO'))
);
GO

CREATE INDEX idx_evento_fecha_inicio ON tbl_evento (fecha_inicio);
GO

CREATE TABLE tbl_resultado_evento (
    id_resultado          INT IDENTITY(1,1) PRIMARY KEY,
    id_evento             INT NOT NULL UNIQUE,
    puntuacion_local      INT NOT NULL,
    puntuacion_visitante  INT NOT NULL,
    observaciones         NVARCHAR(255) NULL,
    fecha_registro        DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_resultado_evento FOREIGN KEY (id_evento) REFERENCES tbl_evento(id_evento) ON DELETE CASCADE,
    CONSTRAINT chk_puntuacion_local_no_negativa      CHECK (puntuacion_local >= 0),
    CONSTRAINT chk_puntuacion_visitante_no_negativa  CHECK (puntuacion_visitante >= 0)
);
GO

CREATE TABLE tbl_mercado_evento (
    id_mercado_evento  INT IDENTITY(1,1) PRIMARY KEY,
    id_evento          INT NOT NULL,
    id_tipo_mercado    INT NOT NULL,
    estado_mercado     NVARCHAR(10) NOT NULL DEFAULT 'ABIERTO',
    CONSTRAINT fk_mercadoevento_evento FOREIGN KEY (id_evento)       REFERENCES tbl_evento(id_evento) ON DELETE CASCADE,
    CONSTRAINT fk_mercadoevento_tipo   FOREIGN KEY (id_tipo_mercado) REFERENCES tbl_tipo_mercado(id_tipo_mercado),
    CONSTRAINT uq_evento_tipo_mercado UNIQUE (id_evento, id_tipo_mercado),
    CONSTRAINT chk_mercadoevento_estado CHECK (estado_mercado IN ('ABIERTO','CERRADO','LIQUIDADO'))
);
GO

CREATE TABLE tbl_opcion_apuesta (
    id_opcion            INT IDENTITY(1,1) PRIMARY KEY,
    id_mercado_evento    INT NOT NULL,
    descripcion_opcion   NVARCHAR(150) NOT NULL,
    cuota_actual         DECIMAL(6,2) NOT NULL,
    es_ganadora          BIT NOT NULL DEFAULT 0,
    CONSTRAINT fk_opcion_mercado FOREIGN KEY (id_mercado_evento) REFERENCES tbl_mercado_evento(id_mercado_evento) ON DELETE CASCADE,
    CONSTRAINT chk_cuota_valida CHECK (cuota_actual > 1.00)
);
GO

CREATE TABLE tbl_promocion_cuota (
    id_promocion         INT IDENTITY(1,1) PRIMARY KEY,
    id_opcion            INT NOT NULL,
    porcentaje_aumento   DECIMAL(5,2) NOT NULL,
    fecha_inicio         DATETIME2 NOT NULL,
    fecha_fin            DATETIME2 NOT NULL,
    CONSTRAINT fk_promocion_opcion FOREIGN KEY (id_opcion) REFERENCES tbl_opcion_apuesta(id_opcion) ON DELETE CASCADE,
    CONSTRAINT chk_porcentaje_no_negativo CHECK (porcentaje_aumento >= 0)
);
GO

-- =============================================================================
-- 5. BOLETOS DE APUESTA
-- =============================================================================

CREATE TABLE tbl_boleto (
    id_boleto           BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_billetera        INT NOT NULL,
    monto_apostado      DECIMAL(14,2) NOT NULL,
    cuota_total         DECIMAL(8,2) NOT NULL,
    ganancia_potencial  DECIMAL(14,2) NOT NULL,
    estado_boleto       NVARCHAR(10) NOT NULL DEFAULT 'PENDIENTE',
    fecha_emision       DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_boleto_billetera FOREIGN KEY (id_billetera) REFERENCES tbl_billetera(id_billetera),
    CONSTRAINT chk_monto_apostado_positivo CHECK (monto_apostado > 0),
    CONSTRAINT chk_ganancia_no_negativa CHECK (ganancia_potencial >= 0),
    CONSTRAINT chk_boleto_estado CHECK (estado_boleto IN ('PENDIENTE','GANADO','PERDIDO','ANULADO','PAGADO'))
);
GO

CREATE TABLE tbl_detalle_boleto (
    id_detalle     BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_boleto      BIGINT NOT NULL,
    id_opcion      INT NOT NULL,
    cuota_momento  DECIMAL(6,2) NOT NULL,
    CONSTRAINT fk_detalle_boleto FOREIGN KEY (id_boleto) REFERENCES tbl_boleto(id_boleto) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_opcion FOREIGN KEY (id_opcion) REFERENCES tbl_opcion_apuesta(id_opcion),
    CONSTRAINT uq_boleto_opcion UNIQUE (id_boleto, id_opcion)
);
GO

-- =============================================================================
-- 6. HISTORIALES Y BITÁCORAS (AUDITORÍA)
-- =============================================================================

CREATE TABLE tbl_historial_cuotas (
    id_historial_cuota  BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_opcion           INT NOT NULL,
    cuota_anterior      DECIMAL(6,2) NOT NULL,
    cuota_nueva         DECIMAL(6,2) NOT NULL,
    fecha_cambio        DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    id_admin            INT NULL,
    CONSTRAINT fk_histcuota_opcion FOREIGN KEY (id_opcion) REFERENCES tbl_opcion_apuesta(id_opcion) ON DELETE CASCADE,
    CONSTRAINT fk_histcuota_admin  FOREIGN KEY (id_admin)  REFERENCES tbl_administrador(id_admin) ON DELETE SET NULL
);
GO

CREATE TABLE tbl_historial_estado_boleto (
    id_historial_boleto  BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_boleto            BIGINT NOT NULL,
    estado_anterior      NVARCHAR(10) NOT NULL,
    estado_nuevo         NVARCHAR(10) NOT NULL,
    motivo_cambio        NVARCHAR(255) NULL,
    fecha_cambio         DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_histestadoboleto_boleto FOREIGN KEY (id_boleto) REFERENCES tbl_boleto(id_boleto) ON DELETE CASCADE,
    CONSTRAINT chk_histestadoboleto_estado_anterior CHECK (estado_anterior IN ('PENDIENTE','GANADO','PERDIDO','ANULADO','PAGADO')),
    CONSTRAINT chk_histestadoboleto_estado_nuevo    CHECK (estado_nuevo    IN ('PENDIENTE','GANADO','PERDIDO','ANULADO','PAGADO'))
);
GO

CREATE TABLE tbl_historial_cambios_evento (
    id_historial_evento  BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_evento            INT NOT NULL,
    estado_anterior      NVARCHAR(15) NOT NULL,
    estado_nuevo         NVARCHAR(15) NOT NULL,
    minuto_partido       SMALLINT NULL,
    marcador_momento     NVARCHAR(20) NULL,
    fecha_registro       DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_histevento_evento FOREIGN KEY (id_evento) REFERENCES tbl_evento(id_evento) ON DELETE CASCADE,
    CONSTRAINT chk_histevento_estado_anterior CHECK (estado_anterior IN ('PROGRAMADO','EN_JUEGO','FINALIZADO','SUSPENDIDO','CANCELADO')),
    CONSTRAINT chk_histevento_estado_nuevo    CHECK (estado_nuevo    IN ('PROGRAMADO','EN_JUEGO','FINALIZADO','SUSPENDIDO','CANCELADO')),
    CONSTRAINT chk_histevento_minuto_no_negativo CHECK (minuto_partido IS NULL OR minuto_partido >= 0)
);
GO

-- mes_ano: Formato AAAA-MM
CREATE TABLE tbl_historial_jugador_resumen (
    id_resumen               INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario               INT NOT NULL,
    mes_ano                  CHAR(7) NOT NULL,
    total_boletos_creados    INT NOT NULL DEFAULT 0,
    monto_total_apostado     DECIMAL(14,2) NOT NULL DEFAULT 0,
    monto_total_reclamado    DECIMAL(14,2) NOT NULL DEFAULT 0,
    rendimiento_neto         DECIMAL(14,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_resumen_usuario FOREIGN KEY (id_usuario) REFERENCES tbl_usuario(id_usuario) ON DELETE CASCADE,
    CONSTRAINT uq_usuario_mes UNIQUE (id_usuario, mes_ano),
    CONSTRAINT chk_resumen_total_boletos_no_negativo CHECK (total_boletos_creados >= 0)
);
GO

CREATE TABLE tbl_bitacora_seguridad (
    id_bitacora       BIGINT IDENTITY(1,1) PRIMARY KEY,
    tipo_evento       NVARCHAR(20) NOT NULL,
    ip_origen         NVARCHAR(45) NOT NULL,
    ruta_solicitada   NVARCHAR(255) NOT NULL,
    detalle           NVARCHAR(MAX) NULL,
    bloqueado         BIT NOT NULL DEFAULT 1,
    fecha_registro    DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT chk_bitacora_tipo_evento CHECK (tipo_evento IN ('SQLI','DDOS','VALOR_INVALIDO','RATE_LIMIT','ACCESO_NO_AUTORIZADO','OTRO'))
);
GO

CREATE INDEX idx_bitacora_ip_fecha ON tbl_bitacora_seguridad (ip_origen, fecha_registro);
GO
CREATE INDEX idx_bitacora_tipo ON tbl_bitacora_seguridad (tipo_evento);
GO

-- =============================================================================
-- FIN DEL SCRIPT
-- Total de tablas: 38  (33 del modelo original conservado + 5 nuevas para
-- cumplir con recuperación de contraseña por correo, preguntas de seguridad
-- y bitácora de seguridad perimetral anti SQL-Injection/DDOS).
-- =============================================================================