ALTER TABLE recognition_face
ADD COLUMN face_width SMALLINT NULL AFTER box,
ADD COLUMN face_height SMALLINT NULL AFTER face_width,
ADD COLUMN blur_score DECIMAL(10, 6) NULL AFTER face_height,
ADD COLUMN face_detector_score DECIMAL(10, 6) NULL AFTER blur_score,
ADD COLUMN pose_score DECIMAL(10, 6) NULL AFTER face_detector_score,
ADD COLUMN occlusion_score DECIMAL(10, 6) NULL AFTER pose_score,
ADD COLUMN discard_reason VARCHAR(255) NULL AFTER quality_score;
