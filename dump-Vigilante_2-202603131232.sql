-- MySQL dump 10.13  Distrib 9.5.0, for macos15 (arm64)
--
-- Host: localhost    Database: Vigilante_2
-- ------------------------------------------------------
-- Server version	9.5.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ 'ec6692fe-c44b-11f0-b832-e9e8d15c5ab0:1-37162';

--
-- Table structure for table `alert_channel`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alert_channel` (
  `alert_channel_id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(30) NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  PRIMARY KEY (`alert_channel_id`),
  UNIQUE KEY `uq_alert_channel_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `alert_rule`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alert_rule` (
  `alert_rule_id` bigint NOT NULL AUTO_INCREMENT,
  `local_id` int DEFAULT NULL,
  `camara_id` int DEFAULT NULL,
  `nombre` varchar(120) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `evento_tipo` enum('ladron','desconocido','identificado','rechazado','revisar','cualquier_reconocimiento') NOT NULL,
  `alert_channel_id` int NOT NULL,
  `mensaje_template` text,
  `only_in_schedule` tinyint(1) NOT NULL DEFAULT '0',
  `days_mask` varchar(20) DEFAULT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `cooldown_seconds` int NOT NULL DEFAULT '0',
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `priority` int NOT NULL DEFAULT '100',
  `created_by_operador_id` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`alert_rule_id`),
  KEY `idx_alert_rule_lookup` (`enabled`,`evento_tipo`,`camara_id`,`local_id`),
  KEY `idx_alert_rule_channel` (`alert_channel_id`,`enabled`),
  KEY `fk_alert_rule_local` (`local_id`),
  KEY `fk_alert_rule_camara` (`camara_id`),
  KEY `fk_alert_rule_operador` (`created_by_operador_id`),
  CONSTRAINT `fk_alert_rule_camara` FOREIGN KEY (`camara_id`) REFERENCES `camara` (`camara_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_alert_rule_channel` FOREIGN KEY (`alert_channel_id`) REFERENCES `alert_channel` (`alert_channel_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_alert_rule_local` FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_alert_rule_operador` FOREIGN KEY (`created_by_operador_id`) REFERENCES `operador` (`operador_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `alerta_enviada`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alerta_enviada` (
  `alerta_enviada_id` bigint NOT NULL AUTO_INCREMENT,
  `recognition_face_id` bigint NOT NULL,
  `canal` enum('telegram','email','webhook','sms','otro') NOT NULL DEFAULT 'telegram',
  `text_alert` json DEFAULT NULL,
  `fecha_alerta` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `estado_envio` enum('pendiente','enviado','error') NOT NULL DEFAULT 'enviado',
  PRIMARY KEY (`alerta_enviada_id`),
  KEY `idx_alerta_fecha` (`fecha_alerta`),
  KEY `idx_alerta_face_fecha` (`recognition_face_id`,`fecha_alerta`),
  CONSTRAINT `fk_alerta_face` FOREIGN KEY (`recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `camara`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `camara` (
  `camara_id` int NOT NULL AUTO_INCREMENT,
  `local_id` int NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `ubicacion` enum('Ingreso','Estadia','Salida','Otro') NOT NULL DEFAULT 'Estadia',
  `estado` enum('Activo','Inactivo') NOT NULL DEFAULT 'Activo',
  `orden` int DEFAULT NULL,
  `protocolo` enum('onvif','webcam','rtsp','archivo','dvr') NOT NULL DEFAULT 'onvif',
  `camara_hostname` varchar(100) DEFAULT NULL,
  `camara_port` smallint DEFAULT NULL,
  `camara_user` varchar(100) DEFAULT NULL,
  `camara_pass` varchar(255) DEFAULT NULL,
  `camara_params` varchar(255) DEFAULT NULL,
  `stream_url` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`camara_id`),
  UNIQUE KEY `uq_camara_local_nombre` (`local_id`,`nombre`),
  KEY `idx_camara_local_estado` (`local_id`,`estado`),
  CONSTRAINT `fk_camara_sucursal` FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `config_definition`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `config_definition` (
  `config_definition_id` bigint NOT NULL AUTO_INCREMENT,
  `config_group_id` int NOT NULL,
  `codigo` varchar(100) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `descripcion` varchar(500) DEFAULT NULL,
  `data_type` enum('string','text','int','decimal','boolean','json','enum','time','datetime') NOT NULL,
  `enum_options` json DEFAULT NULL,
  `default_value_string` text,
  `default_value_json` json DEFAULT NULL,
  `is_required` tinyint(1) NOT NULL DEFAULT '0',
  `is_array` tinyint(1) NOT NULL DEFAULT '0',
  `is_secret` tinyint(1) NOT NULL DEFAULT '0',
  `allow_global` tinyint(1) NOT NULL DEFAULT '1',
  `allow_local` tinyint(1) NOT NULL DEFAULT '1',
  `allow_camera` tinyint(1) NOT NULL DEFAULT '1',
  `allow_channel` tinyint(1) NOT NULL DEFAULT '1',
  `allow_schedule` tinyint(1) NOT NULL DEFAULT '0',
  `validation_regex` varchar(255) DEFAULT NULL,
  `sort_order` int NOT NULL DEFAULT '100',
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_definition_id`),
  UNIQUE KEY `uq_config_definition_codigo` (`codigo`),
  KEY `idx_config_definition_group_estado` (`config_group_id`,`estado`),
  CONSTRAINT `fk_config_definition_group` FOREIGN KEY (`config_group_id`) REFERENCES `config_group` (`config_group_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `config_group`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `config_group` (
  `config_group_id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(60) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `sort_order` int NOT NULL DEFAULT '100',
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_group_id`),
  UNIQUE KEY `uq_config_group_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `config_scope_type`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `config_scope_type` (
  `scope_type_id` tinyint NOT NULL AUTO_INCREMENT,
  `codigo` varchar(30) NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`scope_type_id`),
  UNIQUE KEY `uq_config_scope_type_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `config_value`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `config_value` (
  `config_value_id` bigint NOT NULL AUTO_INCREMENT,
  `config_definition_id` bigint NOT NULL,
  `scope_type_id` tinyint NOT NULL,
  `scope_ref_id` bigint DEFAULT NULL,
  `alert_channel_id` int DEFAULT NULL,
  `schedule_name` varchar(100) DEFAULT NULL,
  `schedule_days_mask` varchar(20) DEFAULT NULL,
  `schedule_start_time` time DEFAULT NULL,
  `schedule_end_time` time DEFAULT NULL,
  `value_string` text,
  `value_json` json DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '1',
  `priority` int NOT NULL DEFAULT '100',
  `notes` varchar(255) DEFAULT NULL,
  `updated_by_operador_id` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`config_value_id`),
  UNIQUE KEY `uq_config_value_scope` (`config_definition_id`,`scope_type_id`,`scope_ref_id`,`alert_channel_id`,`schedule_name`),
  KEY `idx_config_value_scope_lookup` (`scope_type_id`,`scope_ref_id`,`enabled`),
  KEY `idx_config_value_channel` (`alert_channel_id`,`enabled`),
  KEY `idx_config_value_schedule` (`schedule_start_time`,`schedule_end_time`),
  KEY `fk_config_value_operador` (`updated_by_operador_id`),
  CONSTRAINT `fk_config_value_channel` FOREIGN KEY (`alert_channel_id`) REFERENCES `alert_channel` (`alert_channel_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_config_value_definition` FOREIGN KEY (`config_definition_id`) REFERENCES `config_definition` (`config_definition_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_config_value_operador` FOREIGN KEY (`updated_by_operador_id`) REFERENCES `operador` (`operador_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_config_value_scope_type` FOREIGN KEY (`scope_type_id`) REFERENCES `config_scope_type` (`scope_type_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `chk_config_scope_ref_required` CHECK ((((`scope_type_id` = 1) and (`scope_ref_id` is null)) or ((`scope_type_id` in (2,3,4)) and (`scope_ref_id` is not null))))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `empresa`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `empresa` (
  `empresa_id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`empresa_id`),
  UNIQUE KEY `uq_empresa_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `observed_identity`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
-- Vigilante_2.observed_identity definition

CREATE TABLE `observed_identity` (
  `observed_identity_id` bigint NOT NULL AUTO_INCREMENT,
  `status` enum('active','archived','merged','promoted','expired') NOT NULL DEFAULT 'active',
  `current_label` enum('unknown','observed','ladron','sospechoso','persona_interes','visitante','proveedor') NOT NULL DEFAULT 'unknown',
  `risk_level` enum('low','medium','high','critical') NOT NULL DEFAULT 'low',
  `alert_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `display_label` varchar(150) DEFAULT NULL,
  `first_seen_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `times_seen` int NOT NULL DEFAULT '1',
  `last_camera_id` int DEFAULT NULL,
  `best_recognition_face_id` bigint DEFAULT NULL,
  `best_face_image_url` varchar(1024) DEFAULT NULL,
  `notes` text,
  `promoted_persona_id` bigint DEFAULT NULL,
  `retention_policy` varchar(50) DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`observed_identity_id`),
  KEY `idx_observed_identity_status` (`status`),
  KEY `idx_observed_identity_last_seen` (`last_seen_at`),
  KEY `fk_observed_identity_last_camera` (`last_camera_id`),
  KEY `fk_observed_identity_promoted_persona` (`promoted_persona_id`),
  KEY `fk_observed_identity_best_recognition_face` (`best_recognition_face_id`),
  CONSTRAINT `fk_observed_identity_best_recognition_face` FOREIGN KEY (`best_recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_observed_identity_last_camera` FOREIGN KEY (`last_camera_id`) REFERENCES `camara` (`camara_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_observed_identity_promoted_persona` FOREIGN KEY (`promoted_persona_id`) REFERENCES `persona` (`persona_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `observed_identity_embedding`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `observed_identity_embedding` (
  `observed_identity_embedding_id` bigint NOT NULL AUTO_INCREMENT,
  `observed_identity_id` bigint NOT NULL,
  `recognition_face_id` bigint NOT NULL,
  `engine` enum('human','insightface','deepface','facenet','arcface','otro') NOT NULL,
  `model_name` varchar(100) DEFAULT NULL,
  `embedding_vector` json NOT NULL,
  `embedding_dim` smallint DEFAULT NULL,
  `quality_score` decimal(10,6) DEFAULT NULL,
  `is_representative` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`observed_identity_embedding_id`),
  KEY `idx_observed_identity_embedding_observed_identity` (`observed_identity_id`),
  KEY `idx_observed_identity_embedding_engine` (`engine`),
  KEY `fk_observed_identity_embedding_recognition_face` (`recognition_face_id`),
  CONSTRAINT `fk_observed_identity_embedding_observed_identity` FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_observed_identity_embedding_recognition_face` FOREIGN KEY (`recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `operador`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operador` (
  `operador_id` int NOT NULL AUTO_INCREMENT,
  `local_id` int NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(200) NOT NULL,
  `rol` enum('admin','supervisor','operador','viewer') NOT NULL DEFAULT 'operador',
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `gender` enum('male','female','other') NOT NULL DEFAULT 'other',
  `password_bcryptjs` varchar(200) NOT NULL,
  `google` tinyint(1) NOT NULL DEFAULT '0',
  `telegram_chat_id` varchar(100) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`operador_id`),
  UNIQUE KEY `uq_operador_email` (`email`),
  KEY `idx_operador_local_estado` (`local_id`,`estado`),
  CONSTRAINT `fk_operador_sucursal` FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `operador_login`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operador_login` (
  `operador_login_id` bigint NOT NULL AUTO_INCREMENT,
  `operador_id` int NOT NULL,
  `fecha_login` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ip_origen` varchar(45) DEFAULT NULL,
  `user_agent` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`operador_login_id`),
  KEY `idx_operador_login_fecha` (`operador_id`,`fecha_login`),
  CONSTRAINT `fk_operador_login_operador` FOREIGN KEY (`operador_id`) REFERENCES `operador` (`operador_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `persona`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `persona` (
  `persona_id` bigint NOT NULL AUTO_INCREMENT,
  `local_id` int NOT NULL,
  `codigo_externo` varchar(100) DEFAULT NULL,
  `nombre` varchar(150) NOT NULL,
  `tipo` enum('socio','empleado','familia','ladron','otro') NOT NULL DEFAULT 'otro',
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `fecha_creacion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_eliminacion` datetime DEFAULT NULL,
  `gender` enum('male','female','other','unknown') NOT NULL DEFAULT 'unknown',
  `email` varchar(200) DEFAULT NULL,
  `telefono` varchar(50) DEFAULT NULL,
  `img_referencia` varchar(255) DEFAULT NULL,
  `notas` text,
  PRIMARY KEY (`persona_id`),
  UNIQUE KEY `uq_persona_local_codigo_externo` (`local_id`,`codigo_externo`),
  KEY `idx_persona_local_tipo_estado` (`local_id`,`tipo`,`estado`),
  KEY `idx_persona_nombre` (`nombre`),
  CONSTRAINT `fk_persona_sucursal` FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `persona_embedding`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `persona_embedding` (
  `persona_embedding_id` bigint NOT NULL AUTO_INCREMENT,
  `persona_id` bigint NOT NULL,
  `engine` enum('human','insightface','deepface','facenet','arcface','otro') NOT NULL,
  `model_name` varchar(100) DEFAULT NULL,
  `model_version` varchar(50) DEFAULT NULL,
  `embedding_dim` smallint DEFAULT NULL,
  `embedding` json NOT NULL,
  `embedding_hash` char(64) DEFAULT NULL,
  `img_origen` varchar(255) DEFAULT NULL,
  `face_box` json DEFAULT NULL,
  `perfil` enum('front','left','right','top','undetected') NOT NULL DEFAULT 'undetected',
  `quality_score` decimal(10,6) DEFAULT NULL,
  `is_primary` tinyint(1) NOT NULL DEFAULT '0',
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by_operador_id` int DEFAULT NULL,
  PRIMARY KEY (`persona_embedding_id`),
  UNIQUE KEY `uq_persona_embedding_hash` (`embedding_hash`),
  KEY `idx_persona_embedding_persona_estado` (`persona_id`,`estado`),
  KEY `idx_persona_embedding_engine_model` (`engine`,`model_name`,`model_version`),
  KEY `idx_persona_embedding_primary` (`persona_id`,`is_primary`),
  KEY `fk_persona_embedding_operador` (`created_by_operador_id`),
  CONSTRAINT `fk_persona_embedding_operador` FOREIGN KEY (`created_by_operador_id`) REFERENCES `operador` (`operador_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_persona_embedding_persona` FOREIGN KEY (`persona_id`) REFERENCES `persona` (`persona_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recognition_engine_result`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recognition_engine_result` (
  `recognition_engine_result_id` bigint NOT NULL AUTO_INCREMENT,
  `recognition_face_id` bigint NOT NULL,
  `engine` enum('human','insightface','deepface','facenet','arcface','otro') NOT NULL,
  `model_name` varchar(100) DEFAULT NULL,
  `model_version` varchar(50) DEFAULT NULL,
  `detected_human` tinyint(1) DEFAULT NULL,
  `similarity` decimal(10,8) DEFAULT NULL,
  `candidate_persona_id` bigint DEFAULT NULL,
  `candidate_persona_embedding_id` bigint DEFAULT NULL,
  `img` varchar(255) DEFAULT NULL,
  `box` json DEFAULT NULL,
  `embedding` json DEFAULT NULL,
  `embedding_dim` smallint DEFAULT NULL,
  `embedding_hash` char(64) DEFAULT NULL,
  `processing_ms` int DEFAULT NULL,
  `raw_response` json DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`recognition_engine_result_id`),
  KEY `idx_recognition_engine_face_engine` (`recognition_face_id`,`engine`),
  KEY `idx_recognition_engine_candidate` (`candidate_persona_id`,`similarity`),
  KEY `idx_recognition_engine_hash` (`embedding_hash`),
  KEY `fk_recognition_engine_candidate_embedding` (`candidate_persona_embedding_id`),
  CONSTRAINT `fk_recognition_engine_candidate_embedding` FOREIGN KEY (`candidate_persona_embedding_id`) REFERENCES `persona_embedding` (`persona_embedding_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_recognition_engine_candidate_persona` FOREIGN KEY (`candidate_persona_id`) REFERENCES `persona` (`persona_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_recognition_engine_face` FOREIGN KEY (`recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1626 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recognition_event`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recognition_event` (
  `recognition_event_id` bigint NOT NULL AUTO_INCREMENT,
  `id_solicitud` bigint DEFAULT NULL,
  `camara_id` int NOT NULL,
  `local_id` int NOT NULL,
  `occurred_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `frame_img` varchar(255) DEFAULT NULL,
  `frame_image_url` varchar(1024) DEFAULT NULL,
  `frame_metadata` json DEFAULT NULL,
  `source_type` enum('camera','video_file','dvr','upload','api') NOT NULL DEFAULT 'camera',
  `processing_status` enum('ok','sin_rostro','error') NOT NULL DEFAULT 'ok',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`recognition_event_id`),
  KEY `idx_recognition_event_fecha` (`occurred_at`),
  KEY `idx_recognition_event_camara_fecha` (`camara_id`,`occurred_at`),
  KEY `idx_recognition_event_local_fecha` (`local_id`,`occurred_at`),
  KEY `idx_recognition_event_solicitud` (`id_solicitud`),
  CONSTRAINT `fk_recognition_event_camara` FOREIGN KEY (`camara_id`) REFERENCES `camara` (`camara_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_recognition_event_solicitud` FOREIGN KEY (`id_solicitud`) REFERENCES `solicitud_recognition` (`id_solicitud`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_recognition_event_sucursal` FOREIGN KEY (`local_id`) REFERENCES `sucursal` (`local_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1447 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recognition_face`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
-- Vigilante_2.recognition_face definition

CREATE TABLE `recognition_face` (
  `recognition_face_id` bigint NOT NULL AUTO_INCREMENT,
  `recognition_event_id` bigint NOT NULL,
  `face_index` smallint NOT NULL DEFAULT '1',
  `face_img` varchar(255) DEFAULT NULL,
  `face_preview_img` varchar(255) DEFAULT NULL,
  `face_image_url` varchar(1024) DEFAULT NULL,
  `face_preview_url` varchar(1024) DEFAULT NULL,
  `box` json DEFAULT NULL,
  `face_width` smallint DEFAULT NULL,
  `face_height` smallint DEFAULT NULL,
  `blur_score` decimal(10,6) DEFAULT NULL,
  `face_detector_score` decimal(10,6) DEFAULT NULL,
  `pose_score` decimal(10,6) DEFAULT NULL,
  `occlusion_score` decimal(10,6) DEFAULT NULL,
  `perfil` enum('front','left','right','top','undetected') NOT NULL DEFAULT 'undetected',
  `quality_score` decimal(10,6) DEFAULT NULL,
  `discard_reason` varchar(255) DEFAULT NULL,
  `human_score` decimal(10,6) DEFAULT NULL,
  `final_label` enum('desconocido','identificado','ladron','rechazado','revisar') NOT NULL DEFAULT 'desconocido',
  `estado_validacion` enum('valido','por_validar','invalido') NOT NULL DEFAULT 'por_validar',
  `assigned_persona_id` bigint DEFAULT NULL,
  `observed_identity_id` bigint DEFAULT NULL,
  `assigned_status` enum('sin_asignar','auto_asignado','manual_asignado','enrolado_desde_evento') NOT NULL DEFAULT 'sin_asignar',
  `best_similarity` decimal(10,8) DEFAULT NULL,
  `best_engine` enum('human','insightface','deepface','facenet','arcface','otro') DEFAULT NULL,
  `reviewed_by_operador_id` int DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `notas` text,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`recognition_face_id`),
  UNIQUE KEY `uq_recognition_face_event_index` (`recognition_event_id`,`face_index`),
  KEY `idx_recognition_face_label_fecha` (`final_label`,`created_at`),
  KEY `idx_recognition_face_persona_fecha` (`assigned_persona_id`,`created_at`),
  KEY `idx_recognition_face_estado_fecha` (`estado_validacion`,`created_at`),
  KEY `idx_recognition_face_best_engine` (`best_engine`),
  KEY `fk_recognition_face_operador` (`reviewed_by_operador_id`),
  KEY `fk_recognition_face_observed_identity` (`observed_identity_id`),
  CONSTRAINT `fk_recognition_face_event` FOREIGN KEY (`recognition_event_id`) REFERENCES `recognition_event` (`recognition_event_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_recognition_face_observed_identity` FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_recognition_face_operador` FOREIGN KEY (`reviewed_by_operador_id`) REFERENCES `operador` (`operador_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_recognition_face_persona` FOREIGN KEY (`assigned_persona_id`) REFERENCES `persona` (`persona_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1979 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `solicitud_recognition`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `solicitud_recognition` (
  `id_solicitud` bigint NOT NULL AUTO_INCREMENT,
  `camera_id` int DEFAULT NULL,
  `source_type` enum('camera','video_file','dvr','upload','api') NOT NULL DEFAULT 'camera',
  `source_ref` varchar(500) DEFAULT NULL,
  `img` varchar(255) DEFAULT NULL,
  `sharp_ok` tinyint(1) DEFAULT NULL,
  `status` enum('pendiente','procesando','procesada','error') NOT NULL DEFAULT 'pendiente',
  `requested_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `processed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id_solicitud`),
  KEY `idx_solicitud_camera_fecha` (`camera_id`,`requested_at`),
  CONSTRAINT `fk_solicitud_camara` FOREIGN KEY (`camera_id`) REFERENCES `camara` (`camara_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1447 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `storage_object`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `storage_object` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bucket` varchar(100) NOT NULL,
  `object_key` varchar(500) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `content_type` varchar(100) NOT NULL,
  `size_bytes` bigint NOT NULL,
  `checksum_sha256` varchar(64) DEFAULT NULL,
  `public_url` varchar(500) NOT NULL,
  `relative_url` varchar(500) NOT NULL,
  `storage_backend` varchar(50) NOT NULL DEFAULT 'local',
  `source_service` varchar(100) NOT NULL,
  `image_kind` enum('frame_full','face_crop','face_preview') NOT NULL,
  `camera_id` bigint DEFAULT NULL,
  `recognition_event_id` bigint DEFAULT NULL,
  `recognition_face_id` bigint DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bucket_object_key` (`bucket`,`object_key`),
  KEY `idx_recognition_event_id` (`recognition_event_id`),
  KEY `idx_recognition_face_id` (`recognition_face_id`),
  KEY `idx_camera_id` (`camera_id`),
  KEY `idx_image_kind` (`image_kind`)
) ENGINE=InnoDB AUTO_INCREMENT=2630 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sucursal`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sucursal` (
  `local_id` int NOT NULL AUTO_INCREMENT,
  `empresa_id` int NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `estado` enum('activo','inactivo') NOT NULL DEFAULT 'activo',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`local_id`),
  UNIQUE KEY `uq_sucursal_empresa_nombre` (`empresa_id`,`nombre`),
  KEY `idx_sucursal_empresa` (`empresa_id`),
  CONSTRAINT `fk_sucursal_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresa` (`empresa_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `view_event_main_image`
--

SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `view_event_main_image` AS SELECT 
 1 AS `recognition_event_id`,
 1 AS `frame_image_url`,
 1 AS `last_updated`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `view_face_crop`
--

SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `view_face_crop` AS SELECT 
 1 AS `recognition_face_id`,
 1 AS `face_image_url`,
 1 AS `last_updated`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `view_face_preview`
--

SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `view_face_preview` AS SELECT 
 1 AS `recognition_face_id`,
 1 AS `face_preview_url`,
 1 AS `last_updated`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_observed_identity_summary`
--

SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_observed_identity_summary` AS SELECT 
 1 AS `id`,
 1 AS `status`,
 1 AS `first_seen_at`,
 1 AS `last_seen_at`,
 1 AS `times_seen`,
 1 AS `last_camera_id`,
 1 AS `last_camera_nombre`,
 1 AS `best_face_image_url`,
 1 AS `promoted_persona_id`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_recognition_engine_best_match`
--

SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_recognition_engine_best_match` AS SELECT 
 1 AS `recognition_face_id`,
 1 AS `engine`,
 1 AS `similarity`,
 1 AS `candidate_persona_id`,
 1 AS `candidate_persona_embedding_id`,
 1 AS `model_name`,
 1 AS `model_version`,
 1 AS `created_at`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `vw_recognition_timeline`
--

SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vw_recognition_timeline` AS SELECT 
 1 AS `recognition_event_id`,
 1 AS `recognition_face_id`,
 1 AS `local_id`,
 1 AS `camara_id`,
 1 AS `occurred_at`,
 1 AS `face_index`,
 1 AS `face_img`,
 1 AS `perfil`,
 1 AS `final_label`,
 1 AS `estado_validacion`,
 1 AS `best_similarity`,
 1 AS `best_engine`,
 1 AS `assigned_status`,
 1 AS `assigned_persona_id`,
 1 AS `persona_nombre`,
 1 AS `persona_tipo`,
 1 AS `camara_nombre`,
 1 AS `camara_ubicacion`*/;
SET character_set_client = @saved_cs_client;

--
-- Dumping routines for database 'Vigilante_2'
--

--
-- Final view structure for view `view_event_main_image`
--

/*!50001 DROP VIEW IF EXISTS `view_event_main_image`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `view_event_main_image` AS select `storage_object`.`recognition_event_id` AS `recognition_event_id`,max(`storage_object`.`public_url`) AS `frame_image_url`,max(`storage_object`.`created_at`) AS `last_updated` from `storage_object` where ((`storage_object`.`image_kind` = 'frame_full') and (`storage_object`.`recognition_event_id` is not null)) group by `storage_object`.`recognition_event_id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `view_face_crop`
--

/*!50001 DROP VIEW IF EXISTS `view_face_crop`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `view_face_crop` AS select `storage_object`.`recognition_face_id` AS `recognition_face_id`,max(`storage_object`.`public_url`) AS `face_image_url`,max(`storage_object`.`created_at`) AS `last_updated` from `storage_object` where ((`storage_object`.`image_kind` = 'face_crop') and (`storage_object`.`recognition_face_id` is not null)) group by `storage_object`.`recognition_face_id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `view_face_preview`
--

/*!50001 DROP VIEW IF EXISTS `view_face_preview`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `view_face_preview` AS select `storage_object`.`recognition_face_id` AS `recognition_face_id`,max(`storage_object`.`public_url`) AS `face_preview_url`,max(`storage_object`.`created_at`) AS `last_updated` from `storage_object` where ((`storage_object`.`image_kind` = 'face_preview') and (`storage_object`.`recognition_face_id` is not null)) group by `storage_object`.`recognition_face_id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_observed_identity_summary`
--

/*!50001 DROP VIEW IF EXISTS `vw_observed_identity_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_observed_identity_summary` AS select `oi`.`observed_identity_id` AS `id`,`oi`.`status` AS `status`,`oi`.`first_seen_at` AS `first_seen_at`,`oi`.`last_seen_at` AS `last_seen_at`,`oi`.`times_seen` AS `times_seen`,`oi`.`last_camera_id` AS `last_camera_id`,`c`.`nombre` AS `last_camera_nombre`,`oi`.`best_face_image_url` AS `best_face_image_url`,`oi`.`promoted_persona_id` AS `promoted_persona_id` from (`observed_identity` `oi` left join `camara` `c` on((`c`.`camara_id` = `oi`.`last_camera_id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_recognition_engine_best_match`
--

/*!50001 DROP VIEW IF EXISTS `vw_recognition_engine_best_match`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_recognition_engine_best_match` AS select `rer`.`recognition_face_id` AS `recognition_face_id`,`rer`.`engine` AS `engine`,`rer`.`similarity` AS `similarity`,`rer`.`candidate_persona_id` AS `candidate_persona_id`,`rer`.`candidate_persona_embedding_id` AS `candidate_persona_embedding_id`,`rer`.`model_name` AS `model_name`,`rer`.`model_version` AS `model_version`,`rer`.`created_at` AS `created_at` from `recognition_engine_result` `rer` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_recognition_timeline`
--

/*!50001 DROP VIEW IF EXISTS `vw_recognition_timeline`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_recognition_timeline` AS select `re`.`recognition_event_id` AS `recognition_event_id`,`rf`.`recognition_face_id` AS `recognition_face_id`,`re`.`local_id` AS `local_id`,`re`.`camara_id` AS `camara_id`,`re`.`occurred_at` AS `occurred_at`,`rf`.`face_index` AS `face_index`,`rf`.`face_img` AS `face_img`,`rf`.`perfil` AS `perfil`,`rf`.`final_label` AS `final_label`,`rf`.`estado_validacion` AS `estado_validacion`,`rf`.`best_similarity` AS `best_similarity`,`rf`.`best_engine` AS `best_engine`,`rf`.`assigned_status` AS `assigned_status`,`rf`.`assigned_persona_id` AS `assigned_persona_id`,`p`.`nombre` AS `persona_nombre`,`p`.`tipo` AS `persona_tipo`,`c`.`nombre` AS `camara_nombre`,`c`.`ubicacion` AS `camara_ubicacion` from (((`recognition_event` `re` join `recognition_face` `rf` on((`rf`.`recognition_event_id` = `re`.`recognition_event_id`))) join `camara` `c` on((`c`.`camara_id` = `re`.`camara_id`))) left join `persona` `p` on((`p`.`persona_id` = `rf`.`assigned_persona_id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-13 12:32:19




-- Vigilante_2.view_event_main_image source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `vigilante_2`.`view_event_main_image` AS
select
    `vigilante_2`.`storage_object`.`recognition_event_id` AS `recognition_event_id`,
    max(`vigilante_2`.`storage_object`.`public_url`) AS `frame_image_url`,
    max(`vigilante_2`.`storage_object`.`created_at`) AS `last_updated`
from
    `vigilante_2`.`storage_object`
where
    ((`vigilante_2`.`storage_object`.`image_kind` = 'frame_full')
        and (`vigilante_2`.`storage_object`.`recognition_event_id` is not null))
group by
    `vigilante_2`.`storage_object`.`recognition_event_id`;



-- Vigilante_2.view_face_crop source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `vigilante_2`.`view_face_crop` AS
select
    `vigilante_2`.`storage_object`.`recognition_face_id` AS `recognition_face_id`,
    max(`vigilante_2`.`storage_object`.`public_url`) AS `face_image_url`,
    max(`vigilante_2`.`storage_object`.`created_at`) AS `last_updated`
from
    `vigilante_2`.`storage_object`
where
    ((`vigilante_2`.`storage_object`.`image_kind` = 'face_crop')
        and (`vigilante_2`.`storage_object`.`recognition_face_id` is not null))
group by
    `vigilante_2`.`storage_object`.`recognition_face_id`;


-- Vigilante_2.view_face_preview source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `vigilante_2`.`view_face_preview` AS
select
    `vigilante_2`.`storage_object`.`recognition_face_id` AS `recognition_face_id`,
    max(`vigilante_2`.`storage_object`.`public_url`) AS `face_preview_url`,
    max(`vigilante_2`.`storage_object`.`created_at`) AS `last_updated`
from
    `vigilante_2`.`storage_object`
where
    ((`vigilante_2`.`storage_object`.`image_kind` = 'face_preview')
        and (`vigilante_2`.`storage_object`.`recognition_face_id` is not null))
group by
    `vigilante_2`.`storage_object`.`recognition_face_id`;

-- Vigilante_2.vw_observed_identity_summary source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `vigilante_2`.`vw_observed_identity_summary` AS
select
    `oi`.`observed_identity_id` AS `id`,
    `oi`.`status` AS `status`,
    `oi`.`first_seen_at` AS `first_seen_at`,
    `oi`.`last_seen_at` AS `last_seen_at`,
    `oi`.`times_seen` AS `times_seen`,
    `oi`.`last_camera_id` AS `last_camera_id`,
    `c`.`nombre` AS `last_camera_nombre`,
    `oi`.`best_face_image_url` AS `best_face_image_url`,
    `oi`.`promoted_persona_id` AS `promoted_persona_id`
from
    (`vigilante_2`.`observed_identity` `oi`
left join `vigilante_2`.`camara` `c` on
    ((`c`.`camara_id` = `oi`.`last_camera_id`)));


-- Vigilante_2.vw_recognition_engine_best_match source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `vigilante_2`.`vw_recognition_engine_best_match` AS
select
    `rer`.`recognition_face_id` AS `recognition_face_id`,
    `rer`.`engine` AS `engine`,
    `rer`.`similarity` AS `similarity`,
    `rer`.`candidate_persona_id` AS `candidate_persona_id`,
    `rer`.`candidate_persona_embedding_id` AS `candidate_persona_embedding_id`,
    `rer`.`model_name` AS `model_name`,
    `rer`.`model_version` AS `model_version`,
    `rer`.`created_at` AS `created_at`
from
    `vigilante_2`.`recognition_engine_result` `rer`;


-- Vigilante_2.vw_recognition_timeline source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `vigilante_2`.`vw_recognition_timeline` AS
select
    `re`.`recognition_event_id` AS `recognition_event_id`,
    `rf`.`recognition_face_id` AS `recognition_face_id`,
    `re`.`local_id` AS `local_id`,
    `re`.`camara_id` AS `camara_id`,
    `re`.`occurred_at` AS `occurred_at`,
    `rf`.`face_index` AS `face_index`,
    `rf`.`face_img` AS `face_img`,
    `rf`.`perfil` AS `perfil`,
    `rf`.`final_label` AS `final_label`,
    `rf`.`estado_validacion` AS `estado_validacion`,
    `rf`.`best_similarity` AS `best_similarity`,
    `rf`.`best_engine` AS `best_engine`,
    `rf`.`assigned_status` AS `assigned_status`,
    `rf`.`assigned_persona_id` AS `assigned_persona_id`,
    `p`.`nombre` AS `persona_nombre`,
    `p`.`tipo` AS `persona_tipo`,
    `c`.`nombre` AS `camara_nombre`,
    `c`.`ubicacion` AS `camara_ubicacion`
from
    (((`vigilante_2`.`recognition_event` `re`
join `vigilante_2`.`recognition_face` `rf` on
    ((`rf`.`recognition_event_id` = `re`.`recognition_event_id`)))
join `vigilante_2`.`camara` `c` on
    ((`c`.`camara_id` = `re`.`camara_id`)))
left join `vigilante_2`.`persona` `p` on
    ((`p`.`persona_id` = `rf`.`assigned_persona_id`)));



-- 3. Actualizar vista resumen
CREATE OR REPLACE VIEW `vw_observed_identity_summary` AS
SELECT
  oi.observed_identity_id AS id,
  oi.status,
  oi.current_label,
  oi.risk_level,
  oi.first_seen_at,
  oi.last_seen_at,
  oi.times_seen,
  oi.last_camera_id,
  c.nombre AS last_camera_nombre,
  oi.best_face_image_url,
  oi.promoted_persona_id,
  oi.expires_at
FROM `observed_identity` oi
LEFT JOIN `camara` c ON c.camara_id = oi.last_camera_id;