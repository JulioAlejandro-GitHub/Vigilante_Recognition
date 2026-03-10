-- =========================================================
-- Vigilante v2 - Rediseño orientado a eventos de reconocimiento
-- Autor: OpenAI
-- Objetivo:
--   1) Separar identidad persistente (persona enrolada) de ocurrencias temporales
--   2) Evitar crear un "usuario" nuevo por cada reconocimiento
--   3) Mantener el embedding como activo principal del sistema
--   4) Permitir asignación/enrolamiento posterior desde un reconocimiento
-- Compatibilidad:
--   Diseñado para MySQL 8+
-- =========================================================

DROP DATABASE IF EXISTS `Vigilante`;
CREATE DATABASE `Vigilante` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `Vigilante`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =========================================================
-- 1) ESTRUCTURA ORGANIZACIONAL
-- =========================================================

CREATE TABLE `empresa` (
  `empresa_id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `estado` ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`empresa_id`),
  UNIQUE KEY `uq_empresa_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `sucursal` (
  `local_id` INT NOT NULL AUTO_INCREMENT,
  `empresa_id` INT NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `estado` ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`local_id`),
  UNIQUE KEY `uq_sucursal_empresa_nombre` (`empresa_id`,`nombre`),
  KEY `idx_sucursal_empresa` (`empresa_id`),
  CONSTRAINT `fk_sucursal_empresa`
    FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `camara` (
  `camara_id` INT NOT NULL AUTO_INCREMENT,
  `local_id` INT NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `ubicacion` ENUM('Ingreso','Estadia','Salida','Otro') NOT NULL DEFAULT 'Estadia',
  `estado` ENUM('Activo','Inactivo') NOT NULL DEFAULT 'Activo',
  `orden` INT DEFAULT NULL,
  `protocolo` ENUM('onvif','webcam','rtsp','archivo','dvr') NOT NULL DEFAULT 'onvif',
  `camara_hostname` VARCHAR(100) DEFAULT NULL,
  `camara_port` SMALLINT DEFAULT NULL,
  `camara_user` VARCHAR(100) DEFAULT NULL,
  `camara_pass` VARCHAR(255) DEFAULT NULL,
  `camara_params` VARCHAR(255) DEFAULT NULL,
  `stream_url` VARCHAR(500) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`camara_id`),
  UNIQUE KEY `uq_camara_local_nombre` (`local_id`,`nombre`),
  KEY `idx_camara_local_estado` (`local_id`,`estado`),
  CONSTRAINT `fk_camara_sucursal`
    FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- 2) USUARIOS DE LA APLICACIÓN (OPERADORES)
--    Separados de las personas reconocidas por el sistema.
-- =========================================================

CREATE TABLE `operador` (
  `operador_id` INT NOT NULL AUTO_INCREMENT,
  `local_id` INT NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `email` VARCHAR(200) NOT NULL,
  `rol` ENUM('admin','supervisor','operador','viewer') NOT NULL DEFAULT 'operador',
  `estado` ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  `gender` ENUM('male','female','other') NOT NULL DEFAULT 'other',
  `password_bcryptjs` VARCHAR(200) NOT NULL,
  `google` TINYINT(1) NOT NULL DEFAULT 0,
  `telegram_chat_id` VARCHAR(100) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`operador_id`),
  UNIQUE KEY `uq_operador_email` (`email`),
  KEY `idx_operador_local_estado` (`local_id`,`estado`),
  CONSTRAINT `fk_operador_sucursal`
    FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `operador_login` (
  `operador_login_id` BIGINT NOT NULL AUTO_INCREMENT,
  `operador_id` INT NOT NULL,
  `fecha_login` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ip_origen` VARCHAR(45) DEFAULT NULL,
  `user_agent` VARCHAR(500) DEFAULT NULL,
  PRIMARY KEY (`operador_login_id`),
  KEY `idx_operador_login_fecha` (`operador_id`,`fecha_login`),
  CONSTRAINT `fk_operador_login_operador`
    FOREIGN KEY (`operador_id`) REFERENCES `operador` (`operador_id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- 3) PERSONAS ENROLADAS EN EL SISTEMA
--    Esta tabla ya NO representa eventos. Solo identidades persistentes.
-- =========================================================

CREATE TABLE `persona` (
  `persona_id` BIGINT NOT NULL AUTO_INCREMENT,
  `local_id` INT NOT NULL,
  `codigo_externo` VARCHAR(100) DEFAULT NULL,
  `nombre` VARCHAR(150) NOT NULL,
  `tipo` ENUM('socio','empleado','familia','ladron','otro') NOT NULL DEFAULT 'otro',
  `estado` ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  `fecha_creacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_eliminacion` DATETIME DEFAULT NULL,
  `gender` ENUM('male','female','other','unknown') NOT NULL DEFAULT 'unknown',
  `email` VARCHAR(200) DEFAULT NULL,
  `telefono` VARCHAR(50) DEFAULT NULL,
  `img_referencia` VARCHAR(255) DEFAULT NULL,
  `notas` TEXT DEFAULT NULL,
  PRIMARY KEY (`persona_id`),
  UNIQUE KEY `uq_persona_local_codigo_externo` (`local_id`,`codigo_externo`),
  KEY `idx_persona_local_tipo_estado` (`local_id`,`tipo`,`estado`),
  KEY `idx_persona_nombre` (`nombre`),
  CONSTRAINT `fk_persona_sucursal`
    FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Embeddings de enrolamiento / galería de identidad.
-- Permite múltiples embeddings por persona y por engine/modelo.
CREATE TABLE `persona_embedding` (
  `persona_embedding_id` BIGINT NOT NULL AUTO_INCREMENT,
  `persona_id` BIGINT NOT NULL,
  `engine` ENUM('human','insightface','deepface','facenet','arcface','otro') NOT NULL,
  `model_name` VARCHAR(100) DEFAULT NULL,
  `model_version` VARCHAR(50) DEFAULT NULL,
  `embedding_dim` SMALLINT DEFAULT NULL,
  `embedding` JSON NOT NULL,
  `embedding_hash` CHAR(64) DEFAULT NULL,
  `img_origen` VARCHAR(255) DEFAULT NULL,
  `face_box` JSON DEFAULT NULL,
  `perfil` ENUM('front','left','right','top','undetected') NOT NULL DEFAULT 'undetected',
  `quality_score` DECIMAL(10,6) DEFAULT NULL,
  `is_primary` TINYINT(1) NOT NULL DEFAULT 0,
  `estado` ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by_operador_id` INT DEFAULT NULL,
  PRIMARY KEY (`persona_embedding_id`),
  UNIQUE KEY `uq_persona_embedding_hash` (`embedding_hash`),
  KEY `idx_persona_embedding_persona_estado` (`persona_id`,`estado`),
  KEY `idx_persona_embedding_engine_model` (`engine`,`model_name`,`model_version`),
  KEY `idx_persona_embedding_primary` (`persona_id`,`is_primary`),
  CONSTRAINT `fk_persona_embedding_persona`
    FOREIGN KEY (`persona_id`) REFERENCES `persona` (`persona_id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_persona_embedding_operador`
    FOREIGN KEY (`created_by_operador_id`) REFERENCES `operador` (`operador_id`)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- 4) PIPELINE DE INGESTA / SOLICITUDES DE RECONOCIMIENTO
-- =========================================================

CREATE TABLE `solicitud_recognition` (
  `id_solicitud` BIGINT NOT NULL AUTO_INCREMENT,
  `camera_id` INT DEFAULT NULL,
  `source_type` ENUM('camera','video_file','dvr','upload','api') NOT NULL DEFAULT 'camera',
  `source_ref` VARCHAR(500) DEFAULT NULL,
  `img` VARCHAR(255) DEFAULT NULL,
  `sharp_ok` TINYINT(1) DEFAULT NULL,
  `status` ENUM('pendiente','procesando','procesada','error') NOT NULL DEFAULT 'pendiente',
  `requested_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `processed_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id_solicitud`),
  KEY `idx_solicitud_camera_fecha` (`camera_id`,`requested_at`),
  CONSTRAINT `fk_solicitud_camara`
    FOREIGN KEY (`camera_id`) REFERENCES `camara` (`camara_id`)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- 5) EVENTO DE RECONOCIMIENTO
--    Un evento representa un frame / imagen / instante procesado.
--    Puede contener una o varias caras detectadas.
-- =========================================================

CREATE TABLE `recognition_event` (
  `recognition_event_id` BIGINT NOT NULL AUTO_INCREMENT,
  `id_solicitud` BIGINT DEFAULT NULL,
  `camara_id` INT NOT NULL,
  `local_id` INT NOT NULL,
  `occurred_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `frame_img` VARCHAR(255) DEFAULT NULL,
  `frame_metadata` JSON DEFAULT NULL,
  `source_type` ENUM('camera','video_file','dvr','upload','api') NOT NULL DEFAULT 'camera',
  `processing_status` ENUM('ok','sin_rostro','error') NOT NULL DEFAULT 'ok',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`recognition_event_id`),
  KEY `idx_recognition_event_fecha` (`occurred_at`),
  KEY `idx_recognition_event_camara_fecha` (`camara_id`,`occurred_at`),
  KEY `idx_recognition_event_local_fecha` (`local_id`,`occurred_at`),
  KEY `idx_recognition_event_solicitud` (`id_solicitud`),
  CONSTRAINT `fk_recognition_event_solicitud`
    FOREIGN KEY (`id_solicitud`) REFERENCES `solicitud_recognition` (`id_solicitud`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `fk_recognition_event_camara`
    FOREIGN KEY (`camara_id`) REFERENCES `camara` (`camara_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT `fk_recognition_event_sucursal`
    FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Cada cara detectada dentro de un evento.
-- Aquí vive la decisión final de negocio: quedó sin asignar, asignada o enrolada.
CREATE TABLE `recognition_face` (
  `recognition_face_id` BIGINT NOT NULL AUTO_INCREMENT,
  `recognition_event_id` BIGINT NOT NULL,
  `face_index` SMALLINT NOT NULL DEFAULT 1,
  `face_img` VARCHAR(255) DEFAULT NULL,
  `box` JSON DEFAULT NULL,
  `perfil` ENUM('front','left','right','top','undetected') NOT NULL DEFAULT 'undetected',
  `quality_score` DECIMAL(10,6) DEFAULT NULL,
  `human_score` DECIMAL(10,6) DEFAULT NULL,
  `final_label` ENUM('desconocido','identificado','ladron','rechazado','revisar') NOT NULL DEFAULT 'desconocido',
  `estado_validacion` ENUM('valido','por_validar','invalido') NOT NULL DEFAULT 'por_validar',
  `assigned_persona_id` BIGINT DEFAULT NULL,
  `assigned_status` ENUM('sin_asignar','auto_asignado','manual_asignado','enrolado_desde_evento') NOT NULL DEFAULT 'sin_asignar',
  `best_similarity` DECIMAL(10,8) DEFAULT NULL,
  `best_engine` ENUM('human','insightface','deepface','facenet','arcface','otro') DEFAULT NULL,
  `reviewed_by_operador_id` INT DEFAULT NULL,
  `reviewed_at` DATETIME DEFAULT NULL,
  `notas` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`recognition_face_id`),
  UNIQUE KEY `uq_recognition_face_event_index` (`recognition_event_id`,`face_index`),
  KEY `idx_recognition_face_label_fecha` (`final_label`,`created_at`),
  KEY `idx_recognition_face_persona_fecha` (`assigned_persona_id`,`created_at`),
  KEY `idx_recognition_face_estado_fecha` (`estado_validacion`,`created_at`),
  KEY `idx_recognition_face_best_engine` (`best_engine`),
  CONSTRAINT `fk_recognition_face_event`
    FOREIGN KEY (`recognition_event_id`) REFERENCES `recognition_event` (`recognition_event_id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_recognition_face_persona`
    FOREIGN KEY (`assigned_persona_id`) REFERENCES `persona` (`persona_id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `fk_recognition_face_operador`
    FOREIGN KEY (`reviewed_by_operador_id`) REFERENCES `operador` (`operador_id`)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Resultado detallado por engine para cada cara detectada.
-- Aquí se almacena el embedding inferido del reconocimiento.
CREATE TABLE `recognition_engine_result` (
  `recognition_engine_result_id` BIGINT NOT NULL AUTO_INCREMENT,
  `recognition_face_id` BIGINT NOT NULL,
  `engine` ENUM('human','insightface','deepface','facenet','arcface','otro') NOT NULL,
  `model_name` VARCHAR(100) DEFAULT NULL,
  `model_version` VARCHAR(50) DEFAULT NULL,
  `detected_human` TINYINT(1) DEFAULT NULL,
  `similarity` DECIMAL(10,8) DEFAULT NULL,
  `candidate_persona_id` BIGINT DEFAULT NULL,
  `candidate_persona_embedding_id` BIGINT DEFAULT NULL,
  `img` VARCHAR(255) DEFAULT NULL,
  `box` JSON DEFAULT NULL,
  `embedding` JSON DEFAULT NULL,
  `embedding_dim` SMALLINT DEFAULT NULL,
  `embedding_hash` CHAR(64) DEFAULT NULL,
  `processing_ms` INT DEFAULT NULL,
  `raw_response` JSON DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`recognition_engine_result_id`),
  KEY `idx_recognition_engine_face_engine` (`recognition_face_id`,`engine`),
  KEY `idx_recognition_engine_candidate` (`candidate_persona_id`,`similarity`),
  KEY `idx_recognition_engine_hash` (`embedding_hash`),
  CONSTRAINT `fk_recognition_engine_face`
    FOREIGN KEY (`recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_recognition_engine_candidate_persona`
    FOREIGN KEY (`candidate_persona_id`) REFERENCES `persona` (`persona_id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `fk_recognition_engine_candidate_embedding`
    FOREIGN KEY (`candidate_persona_embedding_id`) REFERENCES `persona_embedding` (`persona_embedding_id`)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- =========================================================
-- 6) CONFIGURACION FUNCIONAL DEL SISTEMA
--    Flexible, extensible y separada de secretos (.env / credenciales).
--    Permite parámetros globales, por sucursal, por cámara y por canal.
-- =========================================================

CREATE TABLE `config_scope_type` (
  `scope_type_id` TINYINT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(30) NOT NULL,
  `nombre` VARCHAR(80) NOT NULL,
  `descripcion` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`scope_type_id`),
  UNIQUE KEY `uq_config_scope_type_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `config_group` (
  `config_group_id` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(60) NOT NULL,
  `nombre` VARCHAR(120) NOT NULL,
  `descripcion` VARCHAR(255) DEFAULT NULL,
  `sort_order` INT NOT NULL DEFAULT 100,
  `estado` ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_group_id`),
  UNIQUE KEY `uq_config_group_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `config_definition` (
  `config_definition_id` BIGINT NOT NULL AUTO_INCREMENT,
  `config_group_id` INT NOT NULL,
  `codigo` VARCHAR(100) NOT NULL,
  `nombre` VARCHAR(150) NOT NULL,
  `descripcion` VARCHAR(500) DEFAULT NULL,
  `data_type` ENUM('string','text','int','decimal','boolean','json','enum','time','datetime') NOT NULL,
  `enum_options` JSON DEFAULT NULL,
  `default_value_string` TEXT DEFAULT NULL,
  `default_value_json` JSON DEFAULT NULL,
  `is_required` TINYINT(1) NOT NULL DEFAULT 0,
  `is_array` TINYINT(1) NOT NULL DEFAULT 0,
  `is_secret` TINYINT(1) NOT NULL DEFAULT 0,
  `allow_global` TINYINT(1) NOT NULL DEFAULT 1,
  `allow_local` TINYINT(1) NOT NULL DEFAULT 1,
  `allow_camera` TINYINT(1) NOT NULL DEFAULT 1,
  `allow_channel` TINYINT(1) NOT NULL DEFAULT 1,
  `allow_schedule` TINYINT(1) NOT NULL DEFAULT 0,
  `validation_regex` VARCHAR(255) DEFAULT NULL,
  `sort_order` INT NOT NULL DEFAULT 100,
  `estado` ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_definition_id`),
  UNIQUE KEY `uq_config_definition_codigo` (`codigo`),
  KEY `idx_config_definition_group_estado` (`config_group_id`,`estado`),
  CONSTRAINT `fk_config_definition_group`
    FOREIGN KEY (`config_group_id`) REFERENCES `config_group` (`config_group_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `alert_channel` (
  `alert_channel_id` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(30) NOT NULL,
  `nombre` VARCHAR(80) NOT NULL,
  `descripcion` VARCHAR(255) DEFAULT NULL,
  `estado` ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  PRIMARY KEY (`alert_channel_id`),
  UNIQUE KEY `uq_alert_channel_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



CREATE TABLE `config_value` (
  `config_value_id` BIGINT NOT NULL AUTO_INCREMENT,
  `config_definition_id` BIGINT NOT NULL,
  `scope_type_id` TINYINT NOT NULL,
  `scope_ref_id` BIGINT DEFAULT NULL,
  `alert_channel_id` INT DEFAULT NULL,
  `schedule_name` VARCHAR(100) DEFAULT NULL,
  `schedule_days_mask` VARCHAR(20) DEFAULT NULL,
  `schedule_start_time` TIME DEFAULT NULL,
  `schedule_end_time` TIME DEFAULT NULL,
  `value_string` TEXT DEFAULT NULL,
  `value_json` JSON DEFAULT NULL,
  `enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `priority` INT NOT NULL DEFAULT 100,
  `notes` VARCHAR(255) DEFAULT NULL,
  `updated_by_operador_id` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_value_id`),
  UNIQUE KEY `uq_config_value_scope` (`config_definition_id`,`scope_type_id`,`scope_ref_id`,`alert_channel_id`,`schedule_name`),
  KEY `idx_config_value_scope_lookup` (`scope_type_id`,`scope_ref_id`,`enabled`),
  KEY `idx_config_value_channel` (`alert_channel_id`,`enabled`),
  KEY `idx_config_value_schedule` (`schedule_start_time`,`schedule_end_time`),
  CONSTRAINT `fk_config_value_definition`
    FOREIGN KEY (`config_definition_id`) REFERENCES `config_definition` (`config_definition_id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
CONSTRAINT `fk_config_value_scope_type`
  FOREIGN KEY (`scope_type_id`) REFERENCES `config_scope_type` (`scope_type_id`)
  ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT `fk_config_value_channel`
    FOREIGN KEY (`alert_channel_id`) REFERENCES `alert_channel` (`alert_channel_id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `fk_config_value_operador`
    FOREIGN KEY (`updated_by_operador_id`) REFERENCES `operador` (`operador_id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `chk_config_scope_ref_required`
    CHECK (
      (`scope_type_id` = 1 AND `scope_ref_id` IS NULL) OR
      (`scope_type_id` IN (2,3,4) AND `scope_ref_id` IS NOT NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;







-- Reglas de alertas configurables para múltiples canales y horarios.
CREATE TABLE `alert_rule` (
  `alert_rule_id` BIGINT NOT NULL AUTO_INCREMENT,
  `local_id` INT DEFAULT NULL,
  `camara_id` INT DEFAULT NULL,
  `nombre` VARCHAR(120) NOT NULL,
  `descripcion` VARCHAR(255) DEFAULT NULL,
  `evento_tipo` ENUM('ladron','desconocido','identificado','rechazado','revisar','cualquier_reconocimiento') NOT NULL,
  `alert_channel_id` INT NOT NULL,
  `mensaje_template` TEXT DEFAULT NULL,
  `only_in_schedule` TINYINT(1) NOT NULL DEFAULT 0,
  `days_mask` VARCHAR(20) DEFAULT NULL,
  `start_time` TIME DEFAULT NULL,
  `end_time` TIME DEFAULT NULL,
  `cooldown_seconds` INT NOT NULL DEFAULT 0,
  `enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `priority` INT NOT NULL DEFAULT 100,
  `created_by_operador_id` INT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`alert_rule_id`),
  KEY `idx_alert_rule_lookup` (`enabled`,`evento_tipo`,`camara_id`,`local_id`),
  KEY `idx_alert_rule_channel` (`alert_channel_id`,`enabled`),
  CONSTRAINT `fk_alert_rule_local`
    FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_alert_rule_camara`
    FOREIGN KEY (`camara_id`) REFERENCES `camara` (`camara_id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_alert_rule_channel`
    FOREIGN KEY (`alert_channel_id`) REFERENCES `alert_channel` (`alert_channel_id`)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT `fk_alert_rule_operador`
    FOREIGN KEY (`created_by_operador_id`) REFERENCES `operador` (`operador_id`)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- 7) ALERTAS
--    Ahora la alerta se asocia a una cara/evento de reconocimiento,
--    no a un "acceso" ficticio.
-- =========================================================

CREATE TABLE `alerta_enviada` (
  `alerta_enviada_id` BIGINT NOT NULL AUTO_INCREMENT,
  `recognition_face_id` BIGINT NOT NULL,
  `canal` ENUM('whatsapp','telegram','email','webhook','sms','otro') NOT NULL DEFAULT 'telegram',
  `text_alert` JSON DEFAULT NULL,
  `fecha_alerta` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `estado_envio` ENUM('pendiente','enviado','error') NOT NULL DEFAULT 'enviado',
  PRIMARY KEY (`alerta_enviada_id`),
  KEY `idx_alerta_fecha` (`fecha_alerta`),
  KEY `idx_alerta_face_fecha` (`recognition_face_id`,`fecha_alerta`),
  CONSTRAINT `fk_alerta_face`
    FOREIGN KEY (`recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- 8) VISTAS ÚTILES PARA REPORTERÍA / UX
-- =========================================================

CREATE OR REPLACE VIEW `vw_recognition_timeline` AS
SELECT
  re.recognition_event_id,
  rf.recognition_face_id,
  re.local_id,
  re.camara_id,
  re.occurred_at,
  rf.face_index,
  rf.face_img,
  rf.perfil,
  rf.final_label,
  rf.estado_validacion,
  rf.best_similarity,
  rf.best_engine,
  rf.assigned_status,
  rf.assigned_persona_id,
  p.nombre AS persona_nombre,
  p.tipo AS persona_tipo,
  c.nombre AS camara_nombre,
  c.ubicacion AS camara_ubicacion
FROM recognition_event re
JOIN recognition_face rf ON rf.recognition_event_id = re.recognition_event_id
JOIN camara c ON c.camara_id = re.camara_id
LEFT JOIN persona p ON p.persona_id = rf.assigned_persona_id;

CREATE OR REPLACE VIEW `vw_recognition_engine_best_match` AS
SELECT
  rer.recognition_face_id,
  rer.engine,
  rer.similarity,
  rer.candidate_persona_id,
  rer.candidate_persona_embedding_id,
  rer.model_name,
  rer.model_version,
  rer.created_at
FROM recognition_engine_result rer;



CREATE OR REPLACE VIEW `vw_config_effective` AS
SELECT
  cd.codigo AS config_codigo,
  cd.nombre AS config_nombre,
  cst.codigo AS scope_tipo,
  cv.scope_ref_id,
  ac.codigo AS alert_channel_codigo,
  cv.schedule_name,
  cv.schedule_days_mask,
  cv.schedule_start_time,
  cv.schedule_end_time,
  cv.value_string,
  cv.value_json,
  cv.enabled,
  cv.priority,
  cv.updated_at
FROM config_value cv
JOIN config_definition cd ON cd.config_definition_id = cv.config_definition_id
JOIN config_scope_type cst ON cst.scope_type_id = cv.scope_type_id
LEFT JOIN alert_channel ac ON ac.alert_channel_id = cv.alert_channel_id;

-- =========================================================
-- 9) DATOS BASE / SEMILLA
-- =========================================================

INSERT INTO `empresa` (`nombre`,`estado`) VALUES
  ('Test Vigilante','activo');

INSERT INTO `sucursal` (`empresa_id`,`nombre`,`estado`) VALUES
  (1,'Sucursal Principal','activo');

INSERT INTO `config_scope_type` (`codigo`,`nombre`,`descripcion`) VALUES
  ('global','Global','Configuración aplicable a todo el sistema'),
  ('local','Sucursal','Configuración aplicable a una sucursal'),
  ('camera','Cámara','Configuración aplicable a una cámara específica'),
  ('channel','Canal','Configuración aplicable a un canal de alerta');

INSERT INTO `config_group` (`codigo`,`nombre`,`descripcion`,`sort_order`) VALUES
  ('ui','Interfaz y visualización','Preferencias funcionales de visualización del sistema',10),
  ('recognition','Reconocimiento facial','Parámetros funcionales del motor de reconocimiento',20),
  ('audio','Audio','Comportamiento sonoro del sistema',30),
  ('alerts','Alertas','Mensajes, reglas y envío de alertas',40);

INSERT INTO `alert_channel` (`codigo`,`nombre`,`descripcion`,`estado`) VALUES
  ('whatsapp','WhatsApp','Canal de alertas por WhatsApp','activo'),
  ('telegram','Telegram','Canal de alertas por Telegram','activo'),
  ('email','Email','Canal de alertas por correo electrónico','activo'),
  ('sms','SMS','Canal de alertas por mensajería SMS','activo');

INSERT INTO `config_definition`
  (`config_group_id`,`codigo`,`nombre`,`descripcion`,`data_type`,`enum_options`,`default_value_string`,`default_value_json`,`is_required`,`is_array`,`is_secret`,`allow_global`,`allow_local`,`allow_camera`,`allow_channel`,`allow_schedule`,`sort_order`,`estado`)
VALUES
  (1,'ui.visualization_style','Estilo de visualización','Define el estilo visual funcional del sistema: claro, medio u oscuro','enum',JSON_ARRAY('claro','medio','oscuro'),'oscuro',NULL,1,0,0,1,1,1,0,0,10,'activo'),
  (2,'recognition.minScore_similarity','Similarity mínima','Umbral mínimo de similarity para aceptar coincidencias automáticas','decimal',NULL,'0.75',NULL,1,0,0,1,1,1,0,0,10,'activo'),
  (3,'audio.sound_alert','Sonido de alerta','Activa reproducción de sonido cuando ocurre una alerta','boolean',NULL,'false',NULL,1,0,0,1,1,1,0,0,10,'activo'),
  (3,'audio.sound_ok','Sonido OK','Activa reproducción de sonido cuando una coincidencia es válida','boolean',NULL,'false',NULL,1,0,0,1,1,1,0,0,20,'activo'),
  (4,'alerts.message_template','Plantilla de mensaje de alerta','Texto o plantilla para mensajes de alerta, configurable por cámara/canal/horario','text',NULL,'Alerta en {{camara_nombre}} a las {{occurred_at}}. Tipo: {{final_label}}. Similaridad: {{best_similarity}}',NULL,0,0,0,1,1,1,1,1,10,'activo');

INSERT INTO `config_value`
  (`config_definition_id`,`scope_type_id`,`scope_ref_id`,`alert_channel_id`,`schedule_name`,`schedule_days_mask`,`schedule_start_time`,`schedule_end_time`,`value_string`,`value_json`,`enabled`,`priority`,`notes`,`updated_by_operador_id`)
VALUES
  (1,1,NULL,NULL,NULL,NULL,NULL,NULL,'oscuro',NULL,1,100,'Valor global inicial',NULL),
  (2,1,NULL,NULL,NULL,NULL,NULL,NULL,'0.75',NULL,1,100,'Valor global inicial',NULL),
  (3,1,NULL,NULL,NULL,NULL,NULL,NULL,'false',NULL,1,100,'Valor global inicial',NULL),
  (4,1,NULL,NULL,NULL,NULL,NULL,NULL,'false',NULL,1,100,'Valor global inicial',NULL),
  (5,1,NULL,2,'horario_diurno','1,2,3,4,5', '08:00:00','20:00:00','Alerta Telegram en {{camara_nombre}}. Tipo: {{final_label}}. Hora: {{occurred_at}}',NULL,1,100,'Plantilla ejemplo por horario',NULL);

INSERT INTO `alert_rule`
  (`local_id`,`camara_id`,`nombre`,`descripcion`,`evento_tipo`,`alert_channel_id`,`mensaje_template`,`only_in_schedule`,`days_mask`,`start_time`,`end_time`,`cooldown_seconds`,`enabled`,`priority`,`created_by_operador_id`)
VALUES
  (1,NULL,'Alerta de ladrón por Telegram','Notifica eventos clasificados como ladrón dentro del horario definido','ladron',2,'[Telegram] Alerta de ladrón en {{camara_nombre}} a las {{occurred_at}}',1,'1,2,3,4,5,6,7','00:00:00','23:59:59',30,1,10,NULL),
  (1,NULL,'Alerta de desconocido por Email','Notifica eventos desconocidos durante horario laboral','desconocido',3,'[Email] Desconocido detectado en {{camara_nombre}} a las {{occurred_at}}',1,'1,2,3,4,5','08:00:00','20:00:00',60,1,20,NULL);

INSERT INTO `operador` (
  `local_id`,`nombre`,`email`,`rol`,`estado`,`gender`,`password_bcryptjs`,`google`,`telegram_chat_id`
) VALUES (
  1,
  'Julio Morales',
  'juliomoralesgutierrez@gmail.com',
  'admin',
  'activo',
  'male',
  '$2a$10$/pRqJ8LTWbnnUirDNjz0TO2q.uysnXUUW/H7j8ZGOGDj46t54FwyO',
  0,
  NULL
);

INSERT INTO `camara` (
  `local_id`,`nombre`,`ubicacion`,`estado`,`orden`,`protocolo`,`camara_hostname`,`camara_port`,`camara_user`,`camara_pass`,`camara_params`
) VALUES
  (1,'entrada 1','Ingreso','Activo',1,'onvif','192.168.100.143',554,'admin','admin123','/cam/realmonitor?channel=1&subtype=0'),
  (1,'salida 1','Salida','Inactivo',6,'onvif','192.168.100.143',554,'admin','admin123','/cam/realmonitor?channel=1&subtype=0'),
  (1,'Ingreso 2','Ingreso','Inactivo',2,'onvif','192.168.100.143',554,'admin','admin123','/cam/realmonitor?channel=1&subtype=0'),
  (1,'Salida 7','Estadia','Inactivo',7,'onvif','192.168.100.143',554,'admin','admin123','/cam/realmonitor?channel=1&subtype=0'),
  (1,'Estadia 3','Estadia','Inactivo',3,'onvif','192.168.100.143',554,'admin','admin123','/cam/realmonitor?channel=1&subtype=0'),
  (1,'Estadia 4','Estadia','Inactivo',4,'onvif','192.168.100.143',554,'admin','admin123','/cam/realmonitor?channel=1&subtype=0'),
  (1,'Estadia 5','Estadia','Inactivo',5,'onvif','192.168.100.143',554,'admin','admin123','/cam/realmonitor?channel=1&subtype=0');

-- Persona de ejemplo ya enrolada (opcional)
INSERT INTO `persona` (
  `local_id`,`codigo_externo`,`nombre`,`tipo`,`estado`,`gender`,`email`,`img_referencia`,`notas`
) VALUES (
  1,
  'PERS-0001',
  'Julio',
  'familia',
  'activo',
  'male',
  'juliomoralesgutierrez@gmail.com',
  NULL,
  'Persona de ejemplo enrolada en la galería'
);

SET FOREIGN_KEY_CHECKS = 1;

-- =========================================================
-- NOTAS DE MIGRACIÓN DESDE LA BD ANTERIOR
-- =========================================================
-- 1) usuario            -> separar en operador y persona
-- 2) acceso             -> reemplazar por recognition_event + recognition_face
-- 3) acceso_engine_result -> reemplazar por recognition_engine_result
-- 4) alerts_send        -> reemplazar por alerta_enviada
-- 5) "desconocido" ya no debe existir como persona creada automáticamente.
--    Ahora es un estado / etiqueta del reconocimiento_face.final_label.
-- 6) Cuando un reconocimiento se confirma, se puede:
--      a) asignar recognition_face.assigned_persona_id a una persona existente
--      b) enrolar una nueva persona y luego vincularla al recognition_face
-- 7) Los embeddings históricos de los reconocimientos quedan en recognition_engine_result.embedding
--    y los embeddings de galería / enrolamiento quedan en persona_embedding.embedding
-- 8) La configuración funcional del sistema queda en:
--      a) config_definition  -> catálogo de parámetros
--      b) config_value       -> valores por ámbito (global, sucursal, cámara, canal)
--      c) alert_rule         -> reglas explícitas de alertas por evento, horario y canal
-- 9) Las credenciales sensibles (API keys, tokens, passwords, secretos SMTP, etc.)
--    NO deben almacenarse aquí; deben quedar en .env, vault o gestor de secretos.
-- =========================================================
