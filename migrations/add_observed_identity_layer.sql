-- Migración: Implementar Capa Observed Identity (Re-identificación)
-- Crea las tablas observed_identity, observed_identity_embedding,
-- observed_identity_label_history y las dependencias (FKs) en
-- recognition_event y recognition_face.

-- 1. Crear tabla `observed_identity`
CREATE TABLE `observed_identity` (
    `observed_identity_id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `status` ENUM('active', 'archived', 'merged', 'promoted', 'expired') NOT NULL DEFAULT 'active',
    `current_label` ENUM('unknown', 'observed', 'ladron', 'sospechoso', 'persona_interes', 'visitante', 'proveedor') NOT NULL DEFAULT 'unknown',
    `risk_level` ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'low',
    `alert_enabled` TINYINT(1) NOT NULL DEFAULT 0,
    `display_label` VARCHAR(150) NULL,
    `first_seen_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_seen_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `times_seen` INT NOT NULL DEFAULT 1,
    `last_camera_id` INT NULL,
    `best_recognition_face_id` BIGINT NULL,
    `best_face_image_url` VARCHAR(1024) NULL,
    `retention_policy` VARCHAR(50) NULL,
    `expires_at` DATETIME NULL,
    `notes` TEXT NULL,
    `promoted_persona_id` BIGINT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_oi_last_camera_id` FOREIGN KEY (`last_camera_id`) REFERENCES `camara` (`camara_id`) ON DELETE SET NULL,
    CONSTRAINT `fk_oi_promoted_persona` FOREIGN KEY (`promoted_persona_id`) REFERENCES `persona` (`persona_id`) ON DELETE SET NULL
    -- La foreign key best_recognition_face_id la definimos luego para evitar dependencias circulares complejas al inicio
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Crear tabla `observed_identity_embedding`
CREATE TABLE `observed_identity_embedding` (
    `observed_identity_embedding_id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `observed_identity_id` BIGINT NOT NULL,
    `recognition_face_id` BIGINT NOT NULL,
    `engine` ENUM('human', 'insightface', 'deepface', 'facenet', 'arcface', 'otro') NOT NULL,
    `model_name` VARCHAR(100) NULL,
    `embedding_vector` JSON NOT NULL,
    `embedding_dim` SMALLINT NULL,
    `quality_score` DECIMAL(10, 6) NULL,
    `is_representative` TINYINT(1) NOT NULL DEFAULT 0,
    `is_centroid` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_oie_observed_identity` FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_oie_recognition_face` FOREIGN KEY (`recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Crear tabla `observed_identity_label_history`
CREATE TABLE `observed_identity_label_history` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `observed_identity_id` BIGINT NOT NULL,
    `old_label` VARCHAR(50) NULL,
    `new_label` VARCHAR(50) NOT NULL,
    `old_risk_level` VARCHAR(50) NULL,
    `new_risk_level` VARCHAR(50) NOT NULL,
    `changed_by` INT NULL,
    `reason` TEXT NULL,
    `changed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_oil_history_identity` FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 4. Modificar tabla `recognition_event`
ALTER TABLE `recognition_event`
ADD COLUMN `observed_identity_id` BIGINT NULL AFTER `processing_status`,
ADD CONSTRAINT `fk_re_observed_identity` FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`) ON DELETE SET NULL;


-- 5. Modificar tabla `recognition_face`
ALTER TABLE `recognition_face`
ADD COLUMN `observed_identity_id` BIGINT NULL AFTER `best_engine`,
ADD CONSTRAINT `fk_rf_observed_identity` FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`) ON DELETE SET NULL;


-- 6. Agregar restricción circular faltante en `observed_identity`
ALTER TABLE `observed_identity`
ADD CONSTRAINT `fk_oi_best_recognition_face` FOREIGN KEY (`best_recognition_face_id`) REFERENCES `recognition_face` (`recognition_face_id`) ON DELETE SET NULL;
