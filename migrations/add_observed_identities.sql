-- =========================================================
-- Migración: Identidades Observadas Persistentes
-- =========================================================

-- 1. Crear tabla observed_identity
CREATE TABLE `observed_identity` (
  `observed_identity_id` BIGINT NOT NULL AUTO_INCREMENT,
  `status` ENUM('active','archived','merged','promoted') NOT NULL DEFAULT 'active',
  `display_label` VARCHAR(150) DEFAULT NULL,
  `first_seen_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `times_seen` INT NOT NULL DEFAULT 1,
  `last_camera_id` INT DEFAULT NULL,
  `best_recognition_face_id` BIGINT DEFAULT NULL,
  `best_face_image_url` VARCHAR(1024) DEFAULT NULL,
  `notes` TEXT DEFAULT NULL,
  `promoted_persona_id` BIGINT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`observed_identity_id`),
  KEY `idx_observed_identity_status` (`status`),
  KEY `idx_observed_identity_last_seen` (`last_seen_at`),
  CONSTRAINT `fk_observed_identity_last_camera`
    FOREIGN KEY (`last_camera_id`) REFERENCES `camara` (`camara_id`)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `fk_observed_identity_promoted_persona`
    FOREIGN KEY (`promoted_persona_id`) REFERENCES `persona` (`persona_id`)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Crear tabla observed_identity_embedding
CREATE TABLE `observed_identity_embedding` (
  `observed_identity_embedding_id` BIGINT NOT NULL AUTO_INCREMENT,
  `observed_identity_id` BIGINT NOT NULL,
  `recognition_face_id` BIGINT NOT NULL,
  `engine` ENUM('human','insightface','deepface','facenet','arcface','otro') NOT NULL,
  `model_name` VARCHAR(100) DEFAULT NULL,
  `embedding_vector` JSON NOT NULL,
  `embedding_dim` SMALLINT DEFAULT NULL,
  `quality_score` DECIMAL(10,6) DEFAULT NULL,
  `is_representative` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`observed_identity_embedding_id`),
  KEY `idx_observed_identity_embedding_observed_identity` (`observed_identity_id`),
  KEY `idx_observed_identity_embedding_engine` (`engine`),
  CONSTRAINT `fk_observed_identity_embedding_observed_identity`
    FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT `fk_observed_identity_embedding_recognition_face`
    FOREIGN KEY (`recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Extender recognition_face
ALTER TABLE `recognition_face`
ADD COLUMN `observed_identity_id` BIGINT DEFAULT NULL AFTER `assigned_persona_id`,
ADD CONSTRAINT `fk_recognition_face_observed_identity`
  FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`)
  ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE `observed_identity`
ADD CONSTRAINT `fk_observed_identity_best_recognition_face`
  FOREIGN KEY (`best_recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`)
  ON UPDATE CASCADE ON DELETE SET NULL;

-- 4. Crear vista opcional resumen
CREATE OR REPLACE VIEW `vw_observed_identity_summary` AS
SELECT
  oi.observed_identity_id AS id,
  oi.status,
  oi.first_seen_at,
  oi.last_seen_at,
  oi.times_seen,
  oi.last_camera_id,
  c.nombre AS last_camera_nombre,
  oi.best_face_image_url,
  oi.promoted_persona_id
FROM `observed_identity` oi
LEFT JOIN `camara` c ON c.camara_id = oi.last_camera_id;
