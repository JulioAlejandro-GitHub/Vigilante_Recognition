ALTER TABLE recognition_event
ADD COLUMN frame_image_url VARCHAR(255) DEFAULT NULL AFTER frame_img;

ALTER TABLE recognition_face
ADD COLUMN face_preview_img VARCHAR(255) DEFAULT NULL AFTER face_img,
ADD COLUMN face_image_url VARCHAR(255) DEFAULT NULL AFTER face_preview_img,
ADD COLUMN face_preview_url VARCHAR(255) DEFAULT NULL AFTER face_image_url;
