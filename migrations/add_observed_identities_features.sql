-- =========================================================
-- Migración: Extensiones para Identidades Observadas
-- =========================================================

-- 1. Actualizar tabla observed_identity
ALTER TABLE `observed_identity`
MODIFY COLUMN `status` ENUM('active','archived','merged','promoted','expired') NOT NULL DEFAULT 'active',
ADD COLUMN `current_label` ENUM('unknown','observed','ladron','sospechoso','persona_interes','visitante','proveedor') NOT NULL DEFAULT 'unknown' AFTER `status`,
ADD COLUMN `risk_level` ENUM('low','medium','high','critical') NOT NULL DEFAULT 'low' AFTER `current_label`,
ADD COLUMN `alert_enabled` TINYINT(1) NOT NULL DEFAULT 0 AFTER `risk_level`,
ADD COLUMN `retention_policy` VARCHAR(50) DEFAULT NULL AFTER `promoted_persona_id`,
ADD COLUMN `expires_at` DATETIME DEFAULT NULL AFTER `retention_policy`;

-- 2. Crear tabla observed_identity_label_history
CREATE TABLE `observed_identity_label_history` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `observed_identity_id` BIGINT NOT NULL,
  `old_label` VARCHAR(50) DEFAULT NULL,
  `new_label` VARCHAR(50) NOT NULL,
  `old_risk_level` VARCHAR(50) DEFAULT NULL,
  `new_risk_level` VARCHAR(50) NOT NULL,
  `changed_by` INT DEFAULT NULL,
  `reason` TEXT DEFAULT NULL,
  `changed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_observed_identity_label_history_id` (`observed_identity_id`),
  CONSTRAINT `fk_observed_identity_label_history_identity`
    FOREIGN KEY (`observed_identity_id`) REFERENCES `observed_identity` (`observed_identity_id`)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
