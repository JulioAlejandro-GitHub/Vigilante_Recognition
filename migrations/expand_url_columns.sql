-- Migración: Expandir columnas URL de VARCHAR(255) a VARCHAR(1024)
-- Las URLs generadas por el Storage Service pueden superar 255 caracteres
-- en entornos de producción con dominios reales y paths anidados.

ALTER TABLE recognition_event
    MODIFY COLUMN frame_image_url VARCHAR(1024) DEFAULT NULL;

ALTER TABLE recognition_face
    MODIFY COLUMN face_image_url    VARCHAR(1024) DEFAULT NULL,
    MODIFY COLUMN face_preview_url  VARCHAR(1024) DEFAULT NULL;
