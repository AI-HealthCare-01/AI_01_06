from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `nickname` VARCHAR(100) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255),
    `name` VARCHAR(100) NOT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'PATIENT',
    `birth_date` DATE,
    `gender` VARCHAR(10),
    `phone` VARCHAR(20),
    `font_size_mode` VARCHAR(20),
    `failed_login_attempts` INT NOT NULL DEFAULT 0,
    `locked_until` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `deleted_at` DATETIME(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `auth_providers` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `provider` VARCHAR(30) NOT NULL,
    `provider_user_id` VARCHAR(255) NOT NULL,
    `access_token` LONGTEXT,
    `refresh_token` LONGTEXT,
    `token_expires_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_auth_provid_provide_8f9da1` (`provider`, `provider_user_id`),
    CONSTRAINT `fk_auth_pro_users_bf191ac4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `terms_consents` (
    `terms_of_service` BOOL NOT NULL,
    `privacy_policy` BOOL NOT NULL,
    `marketing_consent` BOOL NOT NULL DEFAULT 0,
    `agreed_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` INT NOT NULL PRIMARY KEY,
    CONSTRAINT `fk_terms_co_users_8943b63c` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `patient_profiles` (
    `height_cm` DECIMAL(5,2),
    `weight_kg` DECIMAL(5,2),
    `has_allergy` BOOL NOT NULL DEFAULT 0,
    `allergy_details` LONGTEXT,
    `has_disease` BOOL NOT NULL DEFAULT 0,
    `disease_details` LONGTEXT,
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` INT NOT NULL PRIMARY KEY,
    CONSTRAINT `fk_patient__users_50a597b1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `caregiver_patient_mappings` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `requested_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `accepted_at` DATETIME(6),
    `caregiver_id` INT NOT NULL,
    `patient_id` INT NOT NULL,
    UNIQUE KEY `uid_caregiver_p_caregiv_78ed77` (`caregiver_id`, `patient_id`),
    CONSTRAINT `fk_caregive_users_83c02437` FOREIGN KEY (`caregiver_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_caregive_users_5f103d73` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `prescriptions` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `hospital_name` VARCHAR(200),
    `doctor_name` VARCHAR(100),
    `prescription_date` DATE,
    `diagnosis` VARCHAR(500),
    `ocr_raw` JSON,
    `ocr_status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `acted_by_id` INT,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_prescrip_users_dd0a98ff` FOREIGN KEY (`acted_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_prescrip_users_75d98828` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `medications` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `dosage` VARCHAR(100),
    `frequency` VARCHAR(200),
    `duration` VARCHAR(100),
    `instructions` LONGTEXT,
    `prescription_id` INT NOT NULL,
    CONSTRAINT `fk_medicati_prescrip_1f35ac11` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `medication_schedules` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `time_of_day` VARCHAR(20) NOT NULL,
    `specific_time` TIME(6),
    `start_date` DATE,
    `end_date` DATE,
    `medication_id` INT NOT NULL,
    CONSTRAINT `fk_medicati_medicati_b5bbf7c8` FOREIGN KEY (`medication_id`) REFERENCES `medications` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `adherence_logs` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `target_date` DATE NOT NULL,
    `status` VARCHAR(20) NOT NULL,
    `logged_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `note` LONGTEXT,
    `actor_user_id` INT NOT NULL,
    `schedule_id` INT NOT NULL,
    CONSTRAINT `fk_adherenc_users_e0d77460` FOREIGN KEY (`actor_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_adherenc_medicati_d203259c` FOREIGN KEY (`schedule_id`) REFERENCES `medication_schedules` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `notifications` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `notification_type` VARCHAR(50) NOT NULL,
    `title` VARCHAR(255),
    `body` LONGTEXT,
    `is_read` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `read_at` DATETIME(6),
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_notifica_users_ca29871f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    KEY `idx_notificatio_user_id_46dd57` (`user_id`, `is_read`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `notification_settings` (
    `medication_enabled` BOOL NOT NULL DEFAULT 1,
    `caregiver_enabled` BOOL NOT NULL DEFAULT 1,
    `time_format` VARCHAR(10),
    `sound_key` VARCHAR(50),
    `morning_time` VARCHAR(8),
    `noon_time` VARCHAR(8),
    `evening_time` VARCHAR(8),
    `bedtime_time` VARCHAR(8),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` INT NOT NULL PRIMARY KEY,
    CONSTRAINT `fk_notifica_users_ea1f99f3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `action_type` VARCHAR(100) NOT NULL,
    `resource_type` VARCHAR(50),
    `resource_id` VARCHAR(255),
    `ip_address` VARCHAR(45) NOT NULL,
    `outcome` VARCHAR(20),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `actor_id` INT NOT NULL,
    CONSTRAINT `fk_audit_lo_users_7e2888de` FOREIGN KEY (`actor_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `guides` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `content` JSON,
    `status` VARCHAR(20) NOT NULL DEFAULT 'generating',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `acted_by_id` INT,
    `prescription_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_guides_users_319e2f8e` FOREIGN KEY (`acted_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_guides_prescrip_324f227e` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_guides_users_73e91131` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chat_threads` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(40),
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `acted_by_id` INT,
    `prescription_id` INT,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_chat_thr_users_2aa6caeb` FOREIGN KEY (`acted_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_chat_thr_prescrip_b72fa94b` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_chat_thr_users_062fdbed` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `role` VARCHAR(20) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'completed',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `thread_id` INT NOT NULL,
    CONSTRAINT `fk_chat_mes_chat_thr_cea26d5c` FOREIGN KEY (`thread_id`) REFERENCES `chat_threads` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chat_feedbacks` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `feedback_type` VARCHAR(20) NOT NULL,
    `reason` VARCHAR(50),
    `reason_text` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `message_id` INT,
    `thread_id` INT,
    CONSTRAINT `fk_chat_fee_chat_mes_a116c643` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_chat_fee_chat_thr_fbe1f574` FOREIGN KEY (`thread_id`) REFERENCES `chat_threads` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `drug_documents` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `drug_name` VARCHAR(200) NOT NULL,
    `drug_name_en` VARCHAR(200),
    `section` VARCHAR(50) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `source` VARCHAR(100),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY `uid_drug_docume_drug_na_7d238b` (`drug_name`, `section`),
    KEY `idx_drug_docume_drug_na_d8e4a1` (`drug_name`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
