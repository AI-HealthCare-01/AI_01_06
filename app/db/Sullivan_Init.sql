/* 1) 사용자 / 인증 / 동의 / 접근성 */

CREATE TABLE `users` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `email` VARCHAR(255) UNIQUE NOT NULL COMMENT '이메일 인증 필수',
  `password_hash` VARCHAR(255) COMMENT '로컬 로그인 시 해시 저장',
  `name` VARCHAR(100) NOT NULL,
  `nickname` VARCHAR(50) UNIQUE NOT NULL COMMENT '보호자-환자 검색/표시용 별명',
  `phone_number` VARCHAR(20),
  `gender` VARCHAR(20) NOT NULL,
  `birthdate` DATE NOT NULL COMMENT '가이드/LLM 맥락 제공(연령)',
  `role` VARCHAR(20) NOT NULL COMMENT 'PATIENT | GUARDIAN',
  `font_size_mode` VARCHAR(20) COMMENT 'SMALL | LARGE 등',
  `failed_login_attempts` INT DEFAULT 0 COMMENT '로그인 실패 횟수',
  `locked_until` TIMESTAMP NULL COMMENT '잠금 해제 시각',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` TIMESTAMP NULL COMMENT '논리 삭제 시각',
  INDEX `idx_users_role` (`role`)
);

CREATE TABLE `auth_providers` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `user_id` VARCHAR(36) NOT NULL,
  `provider` VARCHAR(30) NOT NULL COMMENT 'LOCAL | KAKAO | NAVER | GOOGLE 등',
  `provider_user_id` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE INDEX `uk_provider` (`provider`, `provider_user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);

CREATE TABLE `terms_consents` (
  `user_id` VARCHAR(36) PRIMARY KEY,
  `terms_of_service` BOOLEAN NOT NULL COMMENT '필수',
  `privacy_policy` BOOLEAN NOT NULL COMMENT '필수',
  `marketing_consent` BOOLEAN DEFAULT FALSE COMMENT '선택',
  `agreed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);

/* 2) 보호자-환자 매핑 / 환자 프로필 */

CREATE TABLE `caregiver_patient_mappings` (
  `caregiver_id` VARCHAR(36) NOT NULL,
  `patient_id` VARCHAR(36) NOT NULL,
  `status` VARCHAR(20) NOT NULL COMMENT 'PENDING | APPROVED | REJECTED | REVOKED',
  `requested_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `accepted_at` TIMESTAMP NULL,
  PRIMARY KEY (`caregiver_id`, `patient_id`),
  INDEX `idx_patient_mapping` (`patient_id`),
  FOREIGN KEY (`caregiver_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`)
);

CREATE TABLE `patient_profiles` (
  `user_id` VARCHAR(36) PRIMARY KEY,
  `height_cm` DECIMAL(5,2),
  `weight_kg` DECIMAL(5,2),
  `has_allergies` BOOLEAN DEFAULT FALSE,
  `allergy_details` TEXT COMMENT '알러지/금기 정보',
  `has_diseases` BOOLEAN DEFAULT FALSE,
  `disease_details` TEXT COMMENT '기저질환/만성질환',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);

/* 3) 처방전 / 이미지 / OCR / 약물 */

CREATE TABLE `prescriptions` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `patient_id` VARCHAR(36) NOT NULL,
  `created_by_user_id` VARCHAR(36) NOT NULL,
  `hospital_name` VARCHAR(255),
  `doctor_name` VARCHAR(255),
  `prescription_date` DATE,
  `diagnosis` VARCHAR(255) COMMENT '진단명(텍스트)',
  `verification_status` VARCHAR(30) COMMENT 'DRAFT | CONFIRMED 등',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_pres_patient` (`patient_id`),
  INDEX `idx_pres_date` (`prescription_date`),
  FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`created_by_user_id`) REFERENCES `users` (`id`)
);

CREATE TABLE `prescription_images` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `prescription_id` VARCHAR(36) NOT NULL,
  `file_url` VARCHAR(512) NOT NULL,
  `mime_type` VARCHAR(100),
  `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`)
);

CREATE TABLE `ocr_jobs` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `prescription_image_id` VARCHAR(36) NOT NULL,
  `provider` VARCHAR(50),
  `status` VARCHAR(20) NOT NULL,
  `raw_ocr_json` JSON COMMENT 'MySQL 5.7+ JSON 지원',
  `extracted_text` TEXT,
  `extracted_json` JSON,
  `requested_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `processed_at` TIMESTAMP NULL,
  INDEX `idx_ocr_status` (`status`),
  FOREIGN KEY (`prescription_image_id`) REFERENCES `prescription_images` (`id`)
);

CREATE TABLE `medications` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `prescription_id` VARCHAR(36) NOT NULL,
  `drug_name` VARCHAR(255) NOT NULL,
  `dosage` VARCHAR(100),
  `frequency` VARCHAR(100),
  `administration` VARCHAR(255),
  `duration_days` INT,
  `is_deleted` BOOLEAN DEFAULT FALSE,
  INDEX `idx_med_drug` (`drug_name`),
  FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`)
);

/* 4) 가이드 / 약물 카드 */

CREATE TABLE `medication_guides` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `prescription_id` VARCHAR(36) UNIQUE NOT NULL,
  `guide_markdown` TEXT NOT NULL,
  `precautions` TEXT,
  `lifestyle_advice` TEXT,
  `summary_json` JSON,
  `generated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`)
);

CREATE TABLE `guide_medication_cards` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `guide_id` VARCHAR(36) NOT NULL,
  `medication_id` VARCHAR(36) NOT NULL,
  `usage_text` TEXT,
  `warning_text` TEXT,
  UNIQUE INDEX `uk_guide_med` (`guide_id`, `medication_id`),
  FOREIGN KEY (`guide_id`) REFERENCES `medication_guides` (`id`),
  FOREIGN KEY (`medication_id`) REFERENCES `medications` (`id`)
);

/* 5) 스케줄 / 로그 */

CREATE TABLE `medication_schedules` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `medication_id` VARCHAR(36) NOT NULL,
  `time_of_day` VARCHAR(20) NOT NULL COMMENT 'MORNING | NOON | EVENING | BEDTIME',
  `specific_time` TIME,
  `start_date` DATE,
  `end_date` DATE,
  FOREIGN KEY (`medication_id`) REFERENCES `medications` (`id`)
);

CREATE TABLE `adherence_logs` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `schedule_id` VARCHAR(36) NOT NULL,
  `actor_user_id` VARCHAR(36) NOT NULL,
  `target_date` DATE NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `logged_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `note` TEXT,
  INDEX `idx_log_date` (`target_date`),
  FOREIGN KEY (`schedule_id`) REFERENCES `medication_schedules` (`id`),
  FOREIGN KEY (`actor_user_id`) REFERENCES `users` (`id`)
);

/* 6) 알림 */

CREATE TABLE `notification_settings` (
  `user_id` VARCHAR(36) PRIMARY KEY,
  `time_format` VARCHAR(10),
  `sound_key` VARCHAR(50),
  `morning_time` TIME,
  `noon_time` TIME,
  `evening_time` TIME,
  `bedtime_time` TIME,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);

CREATE TABLE `notifications` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `user_id` VARCHAR(36) NOT NULL,
  `type` VARCHAR(50) NOT NULL,
  `title` VARCHAR(255),
  `body` TEXT,
  `is_read` BOOLEAN DEFAULT FALSE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `read_at` TIMESTAMP NULL,
  INDEX `idx_noti_user` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);

/* 7) 챗봇 */

CREATE TABLE `chat_sessions` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `patient_id` VARCHAR(36) NOT NULL,
  `prescription_id` VARCHAR(36),
  `guide_id` VARCHAR(36),
  `started_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `is_active` BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`),
  FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`),
  FOREIGN KEY (`guide_id`) REFERENCES `medication_guides` (`id`)
);

CREATE TABLE `chat_messages` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `session_id` VARCHAR(36) NOT NULL,
  `sender_type` VARCHAR(20) NOT NULL,
  `message_text` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`)
);

CREATE TABLE `chat_feedbacks` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `message_id` VARCHAR(36) UNIQUE NOT NULL,
  `feedback_category` VARCHAR(255) NOT NULL,
  `additional_notes` TEXT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`)
);

/* 8) 감사 로그 */

CREATE TABLE `audit_logs` (
  `id` VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
  `actor_id` VARCHAR(36) NOT NULL,
  `action_type` VARCHAR(100) NOT NULL,
  `resource_type` VARCHAR(50),
  `resource_id` VARCHAR(255),
  `ip_address` VARCHAR(45) NOT NULL,
  `outcome` VARCHAR(20),
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_audit_actor` (`actor_id`),
  FOREIGN KEY (`actor_id`) REFERENCES `users` (`id`)
);