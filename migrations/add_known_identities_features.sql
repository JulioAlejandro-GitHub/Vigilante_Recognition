-- Migración para añadir soporte de galería representativa y centroides a personas conocidas

ALTER TABLE persona_embedding
ADD COLUMN is_representative BOOLEAN NOT NULL DEFAULT TRUE,
ADD COLUMN is_centroid BOOLEAN NOT NULL DEFAULT FALSE;
