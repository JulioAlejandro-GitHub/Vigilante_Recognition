ALTER TABLE `observed_identity_embedding` ADD COLUMN `is_centroid` tinyint(1) NOT NULL DEFAULT '0' AFTER `is_representative`;
