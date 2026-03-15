#!/usr/bin/env bash
# =============================================================================
# Sullivan 테스트 데이터 Seed 스크립트
# =============================================================================
#
# 사용법:
#   Docker Compose가 실행 중인 상태에서:
#      bash infra/db/seed_test_data.sh
#
#   DB 접속 정보는 infra/env/.local.env 에서 자동으로 읽습니다.
#   (.local.env는 .gitignore에 포함되어 git에 커밋되지 않습니다)
#
# 주의:
#   - 기존 test 계정(testp*, testg*)이 있으면 삭제 후 재생성합니다.
#   - 비밀번호는 아래 PW_HASH 변수의 bcrypt 원문입니다 (팀 내부 공유)
#   - 오늘의 복약 확인을 위해 스케줄 start_date/end_date가 오늘을 포함하도록 설정됩니다.
#
# 생성되는 데이터:
#   PATIENT 9명 (testp1~9@test.com) — 각각 다른 프로필 + 약 1~6개 처방전
#   GUARDIAN 3명 (testg1~3@test.com) — 각각 PATIENT 3명과 APPROVED 연동
#     testg1 → testp1, testp2, testp3
#     testg2 → testp4, testp5, testp6
#     testg3 → testp7, testp8, testp9
# =============================================================================

set -euo pipefail

# --- .local.env에서 DB 접속 정보를 읽음 (비밀번호 하드코딩 금지) ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../env/.local.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] $ENV_FILE 파일이 없습니다."
  echo "        infra/env/example.local.env 를 복사하여 .local.env 를 생성하세요."
  exit 1
fi

_val() { grep "^$1=" "$ENV_FILE" | cut -d'=' -f2-; }

DB_HOST="127.0.0.1"
DB_PORT=$(_val DB_EXPOSE_PORT)
DB_USER=$(_val MYSQL_USER)
DB_PASS=$(_val MYSQL_PASSWORD)
DB_NAME=$(_val MYSQL_DATABASE)

[ -z "$DB_PORT" ] && DB_PORT="3306"
[ -z "$DB_NAME" ] && DB_NAME="ai_health"

if [ -z "$DB_USER" ] || [ -z "$DB_PASS" ]; then
  echo "[ERROR] .local.env에 MYSQL_USER 또는 MYSQL_PASSWORD가 설정되지 않았습니다."
  exit 1
fi

echo "[INFO] .local.env 로드 완료 (USER=$DB_USER, DB=$DB_NAME, PORT=$DB_PORT)"

# --- MySQL 실행 함수 (docker exec으로 컨테이너 내부에서 실행) ---
MYSQL_CONTAINER="mysql"

if ! docker ps --format '{{.Names}}' | grep -qx "$MYSQL_CONTAINER"; then
  echo "[ERROR] Docker 컨테이너 '$MYSQL_CONTAINER'가 실행 중이 아닙니다."
  echo "        docker compose up -d 로 먼저 기동하세요."
  exit 1
fi

# 컨테이너 내부에 임시 인증 파일 생성 (ps에서 비밀번호 노출 방지)
docker exec "$MYSQL_CONTAINER" sh -c \
  "printf '[client]\nuser=%s\npassword=%s\ndefault-character-set=utf8mb4\n' '$DB_USER' '$DB_PASS' > /tmp/.seed_my.cnf && chmod 600 /tmp/.seed_my.cnf"
trap 'docker exec "$MYSQL_CONTAINER" rm -f /tmp/.seed_my.cnf 2>/dev/null' EXIT

run_sql() {
  docker exec -i "$MYSQL_CONTAINER" mysql \
    --defaults-extra-file=/tmp/.seed_my.cnf "$DB_NAME" <<< "$1"
}

# --- 연결 확인 ---
echo "[1/6] MySQL 연결 확인..."
run_sql "SELECT 1;" > /dev/null 2>&1 || { echo "[ERROR] MySQL 연결 실패"; exit 1; }
echo "  ✓ 연결 성공"

# --- 날짜 계산 ---
TODAY=$(date +%Y-%m-%d)
START_DATE=$(date -v-7d +%Y-%m-%d 2>/dev/null || date -d "7 days ago" +%Y-%m-%d)
END_DATE=$(date -v+23d +%Y-%m-%d 2>/dev/null || date -d "23 days from now" +%Y-%m-%d)

# bcrypt hash — 원문은 팀 내부 채널 참고
PW_HASH='$2b$12$5LC6ltOo40UXKfEsKGl9d.9jzPg0/WuTXWC4sJStTkY52p7KHlD06'

echo "[2/6] 기존 테스트 데이터 정리..."
run_sql "
SET FOREIGN_KEY_CHECKS = 0;

-- 기존 테스트 유저 ID 수집 후 관련 데이터 삭제
DELETE al FROM adherence_logs al
  INNER JOIN medication_schedules ms ON al.schedule_id = ms.id
  INNER JOIN medications m ON ms.medication_id = m.id
  INNER JOIN prescriptions p ON m.prescription_id = p.id
  INNER JOIN users u ON p.user_id = u.id
  WHERE u.email LIKE 'testp%@test.com' OR u.email LIKE 'testg%@test.com';

DELETE ms FROM medication_schedules ms
  INNER JOIN medications m ON ms.medication_id = m.id
  INNER JOIN prescriptions p ON m.prescription_id = p.id
  INNER JOIN users u ON p.user_id = u.id
  WHERE u.email LIKE 'testp%@test.com' OR u.email LIKE 'testg%@test.com';

DELETE g FROM guides g
  INNER JOIN users u ON g.user_id = u.id
  WHERE u.email LIKE 'testp%@test.com' OR u.email LIKE 'testg%@test.com';

DELETE m FROM medications m
  INNER JOIN prescriptions p ON m.prescription_id = p.id
  INNER JOIN users u ON p.user_id = u.id
  WHERE u.email LIKE 'testp%@test.com' OR u.email LIKE 'testg%@test.com';

DELETE FROM prescriptions WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'testp%@test.com' OR email LIKE 'testg%@test.com');

DELETE FROM caregiver_patient_mappings WHERE caregiver_id IN (SELECT id FROM users WHERE email LIKE 'testg%@test.com')
  OR patient_id IN (SELECT id FROM users WHERE email LIKE 'testp%@test.com');

DELETE FROM auth_providers WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'testp%@test.com' OR email LIKE 'testg%@test.com');
DELETE FROM terms_consents WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'testp%@test.com' OR email LIKE 'testg%@test.com');
DELETE FROM patient_profiles WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'testp%@test.com' OR email LIKE 'testg%@test.com');
DELETE FROM users WHERE email LIKE 'testp%@test.com' OR email LIKE 'testg%@test.com';

SET FOREIGN_KEY_CHECKS = 1;
"
echo "  ✓ 정리 완료"

echo "[3/6] 사용자 계정 생성..."
run_sql "
-- ===== PATIENT 9명 =====
INSERT INTO users (email, nickname, password_hash, name, role, birth_date, gender, phone, font_size_mode, failed_login_attempts, created_at, updated_at) VALUES
  ('testp1@test.com', '테환자일', '${PW_HASH}', '김건강', 'PATIENT', '1990-05-15', 'MALE',   '010-1111-0001', NULL,    0, NOW(), NOW()),
  ('testp2@test.com', '테환자이', '${PW_HASH}', '이복약', 'PATIENT', '1985-11-22', 'FEMALE', '010-1111-0002', 'LARGE', 0, NOW(), NOW()),
  ('testp3@test.com', '테환자삼', '${PW_HASH}', '박처방', 'PATIENT', '2000-03-08', 'MALE',   '010-1111-0003', NULL,    0, NOW(), NOW()),
  ('testp4@test.com', '테환자사', '${PW_HASH}', '최영양', 'PATIENT', '1978-07-30', 'FEMALE', '010-1111-0004', 'LARGE', 0, NOW(), NOW()),
  ('testp5@test.com', '테환자오', '${PW_HASH}', '정운동', 'PATIENT', '1955-01-12', 'MALE',   '010-1111-0005', 'LARGE', 0, NOW(), NOW()),
  ('testp6@test.com', '테환자육', '${PW_HASH}', '강미소', 'PATIENT', '1998-09-25', 'FEMALE', '010-1111-0006', NULL,    0, NOW(), NOW()),
  ('testp7@test.com', '테환자칠', '${PW_HASH}', '조활력', 'PATIENT', '1945-12-03', 'MALE',   '010-1111-0007', 'LARGE', 0, NOW(), NOW()),
  ('testp8@test.com', '테환자팔', '${PW_HASH}', '윤평화', 'PATIENT', '2005-06-18', 'FEMALE', '010-1111-0008', NULL,    0, NOW(), NOW()),
  ('testp9@test.com', '테환자구', '${PW_HASH}', '한든든', 'PATIENT', '1968-04-01', NULL,     '010-1111-0009', NULL,    0, NOW(), NOW());

-- ===== GUARDIAN 3명 =====
INSERT INTO users (email, nickname, password_hash, name, role, birth_date, gender, phone, font_size_mode, failed_login_attempts, created_at, updated_at) VALUES
  ('testg1@test.com', '테보호일', '${PW_HASH}', '김보호', 'GUARDIAN', '1965-02-20', 'MALE',   '010-2222-0001', NULL,    0, NOW(), NOW()),
  ('testg2@test.com', '테보호이', '${PW_HASH}', '이돌봄', 'GUARDIAN', '1970-08-14', 'FEMALE', '010-2222-0002', 'LARGE', 0, NOW(), NOW()),
  ('testg3@test.com', '테보호삼', '${PW_HASH}', '박사랑', 'GUARDIAN', '1980-11-30', 'FEMALE', '010-2222-0003', NULL,    0, NOW(), NOW());
"
echo "  ✓ 계정 생성 완료 (PATIENT 9, GUARDIAN 3)"

echo "[4/6] 프로필 · 약관 · 인증제공자 생성..."
run_sql "
-- 유저 ID 변수 설정
SET @p1 = (SELECT id FROM users WHERE email='testp1@test.com');
SET @p2 = (SELECT id FROM users WHERE email='testp2@test.com');
SET @p3 = (SELECT id FROM users WHERE email='testp3@test.com');
SET @p4 = (SELECT id FROM users WHERE email='testp4@test.com');
SET @p5 = (SELECT id FROM users WHERE email='testp5@test.com');
SET @p6 = (SELECT id FROM users WHERE email='testp6@test.com');
SET @p7 = (SELECT id FROM users WHERE email='testp7@test.com');
SET @p8 = (SELECT id FROM users WHERE email='testp8@test.com');
SET @p9 = (SELECT id FROM users WHERE email='testp9@test.com');
SET @g1 = (SELECT id FROM users WHERE email='testg1@test.com');
SET @g2 = (SELECT id FROM users WHERE email='testg2@test.com');
SET @g3 = (SELECT id FROM users WHERE email='testg3@test.com');

-- ===== patient_profiles (다양한 케이스) =====
-- p1: 건강한 청년 (알레르기·질환 없음)
INSERT INTO patient_profiles (user_id, height_cm, weight_kg, has_allergy, allergy_details, has_disease, disease_details, updated_at) VALUES
  (@p1, 175.50, 72.00, FALSE, NULL, FALSE, NULL, NOW());
-- p2: 여성, 알레르기 있음
INSERT INTO patient_profiles (user_id, height_cm, weight_kg, has_allergy, allergy_details, has_disease, disease_details, updated_at) VALUES
  (@p2, 162.00, 55.30, TRUE, '페니실린 알레르기, 땅콩 알레르기', FALSE, NULL, NOW());
-- p3: 키·몸무게만 입력 (최소 정보)
INSERT INTO patient_profiles (user_id, height_cm, weight_kg, has_allergy, allergy_details, has_disease, disease_details, updated_at) VALUES
  (@p3, 180.00, 78.50, FALSE, NULL, FALSE, NULL, NOW());
-- p4: 만성질환 있음
INSERT INTO patient_profiles (user_id, height_cm, weight_kg, has_allergy, allergy_details, has_disease, disease_details, updated_at) VALUES
  (@p4, 158.00, 63.00, FALSE, NULL, TRUE, '고혈압, 제2형 당뇨', NOW());
-- p5: 고령 + 알레르기 + 질환 모두 있음
INSERT INTO patient_profiles (user_id, height_cm, weight_kg, has_allergy, allergy_details, has_disease, disease_details, updated_at) VALUES
  (@p5, 168.00, 65.00, TRUE, '아스피린 과민반응', TRUE, '관상동맥질환, 골관절염, 전립선비대증', NOW());
-- p6: 젊은 여성, 알레르기만
INSERT INTO patient_profiles (user_id, height_cm, weight_kg, has_allergy, allergy_details, has_disease, disease_details, updated_at) VALUES
  (@p6, 165.00, 50.00, TRUE, '설파제 알레르기', FALSE, NULL, NOW());
-- p7: 고령 + 복합 질환
INSERT INTO patient_profiles (user_id, height_cm, weight_kg, has_allergy, allergy_details, has_disease, disease_details, updated_at) VALUES
  (@p7, 170.00, 58.00, TRUE, '조영제 알레르기', TRUE, '만성폐쇄성폐질환(COPD), 심방세동, 골다공증', NOW());
-- p8: 청소년, 프로필 미입력 (NULL)
-- (patient_profiles 레코드 없음)
-- p9: 성별 미입력, 질환만
INSERT INTO patient_profiles (user_id, height_cm, weight_kg, has_allergy, allergy_details, has_disease, disease_details, updated_at) VALUES
  (@p9, NULL, NULL, FALSE, NULL, TRUE, '위식도역류질환(GERD)', NOW());

-- ===== terms_consents =====
INSERT INTO terms_consents (user_id, terms_of_service, privacy_policy, marketing_consent, agreed_at) VALUES
  (@p1, TRUE, TRUE, FALSE, NOW()), (@p2, TRUE, TRUE, TRUE, NOW()),  (@p3, TRUE, TRUE, FALSE, NOW()),
  (@p4, TRUE, TRUE, TRUE, NOW()),  (@p5, TRUE, TRUE, FALSE, NOW()), (@p6, TRUE, TRUE, TRUE, NOW()),
  (@p7, TRUE, TRUE, FALSE, NOW()), (@p8, TRUE, TRUE, FALSE, NOW()), (@p9, TRUE, TRUE, TRUE, NOW()),
  (@g1, TRUE, TRUE, FALSE, NOW()), (@g2, TRUE, TRUE, TRUE, NOW()),  (@g3, TRUE, TRUE, FALSE, NOW());

-- ===== auth_providers (LOCAL) =====
INSERT INTO auth_providers (user_id, provider, provider_user_id, created_at) VALUES
  (@p1, 'LOCAL', @p1, NOW()), (@p2, 'LOCAL', @p2, NOW()), (@p3, 'LOCAL', @p3, NOW()),
  (@p4, 'LOCAL', @p4, NOW()), (@p5, 'LOCAL', @p5, NOW()), (@p6, 'LOCAL', @p6, NOW()),
  (@p7, 'LOCAL', @p7, NOW()), (@p8, 'LOCAL', @p8, NOW()), (@p9, 'LOCAL', @p9, NOW()),
  (@g1, 'LOCAL', @g1, NOW()), (@g2, 'LOCAL', @g2, NOW()), (@g3, 'LOCAL', @g3, NOW());

-- ===== caregiver_patient_mappings (APPROVED) =====
INSERT INTO caregiver_patient_mappings (caregiver_id, patient_id, status, requested_at, accepted_at) VALUES
  (@g1, @p1, 'APPROVED', NOW(), NOW()), (@g1, @p2, 'APPROVED', NOW(), NOW()), (@g1, @p3, 'APPROVED', NOW(), NOW()),
  (@g2, @p4, 'APPROVED', NOW(), NOW()), (@g2, @p5, 'APPROVED', NOW(), NOW()), (@g2, @p6, 'APPROVED', NOW(), NOW()),
  (@g3, @p7, 'APPROVED', NOW(), NOW()), (@g3, @p8, 'APPROVED', NOW(), NOW()), (@g3, @p9, 'APPROVED', NOW(), NOW());
"
echo "  ✓ 프로필·약관·인증·보호자 연동 완료"

echo "[5/6] 처방전 · 약물 · 복약 가이드 생성..."
run_sql "
SET @p1 = (SELECT id FROM users WHERE email='testp1@test.com');
SET @p2 = (SELECT id FROM users WHERE email='testp2@test.com');
SET @p3 = (SELECT id FROM users WHERE email='testp3@test.com');
SET @p4 = (SELECT id FROM users WHERE email='testp4@test.com');
SET @p5 = (SELECT id FROM users WHERE email='testp5@test.com');
SET @p6 = (SELECT id FROM users WHERE email='testp6@test.com');
SET @p7 = (SELECT id FROM users WHERE email='testp7@test.com');
SET @p8 = (SELECT id FROM users WHERE email='testp8@test.com');
SET @p9 = (SELECT id FROM users WHERE email='testp9@test.com');

-- ===== 처방전 (각 환자 1개씩) =====
-- p1: 약 1개 (감기)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p1, '/uploads/test/rx_p1.jpg', '서울내과의원', '김의사', '${TODAY}', '급성 상기도 감염', 'confirmed', NOW());
SET @rx1 = LAST_INSERT_ID();

-- p2: 약 2개 (고혈압)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p2, '/uploads/test/rx_p2.jpg', '강남세브란스병원', '이의사', '${TODAY}', '본태성 고혈압', 'confirmed', NOW());
SET @rx2 = LAST_INSERT_ID();

-- p3: 약 3개 (위장관)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p3, '/uploads/test/rx_p3.jpg', '연세소화기내과', '박의사', '${TODAY}', '기능성 소화불량', 'confirmed', NOW());
SET @rx3 = LAST_INSERT_ID();

-- p4: 약 4개 (당뇨+고혈압)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p4, '/uploads/test/rx_p4.jpg', '삼성서울병원', '최의사', '${TODAY}', '제2형 당뇨, 고혈압', 'confirmed', NOW());
SET @rx4 = LAST_INSERT_ID();

-- p5: 약 5개 (복합 만성질환)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p5, '/uploads/test/rx_p5.jpg', '서울아산병원', '정의사', '${TODAY}', '관상동맥질환, 골관절염', 'confirmed', NOW());
SET @rx5 = LAST_INSERT_ID();

-- p6: 약 2개 (피부)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p6, '/uploads/test/rx_p6.jpg', '미소피부과', '강의사', '${TODAY}', '아토피 피부염', 'confirmed', NOW());
SET @rx6 = LAST_INSERT_ID();

-- p7: 약 6개 (고령 복합 - 스크롤 테스트용)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p7, '/uploads/test/rx_p7.jpg', '서울대학교병원', '조의사', '${TODAY}', 'COPD, 심방세동, 골다공증', 'confirmed', NOW());
SET @rx7 = LAST_INSERT_ID();

-- p8: 약 1개 (경미)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p8, '/uploads/test/rx_p8.jpg', '우리동네의원', '윤의사', '${TODAY}', '긴장형 두통', 'confirmed', NOW());
SET @rx8 = LAST_INSERT_ID();

-- p9: 약 3개 (위장관)
INSERT INTO prescriptions (user_id, image_path, hospital_name, doctor_name, prescription_date, diagnosis, ocr_status, created_at)
  VALUES (@p9, '/uploads/test/rx_p9.jpg', '한강내과', '한의사', '${TODAY}', '위식도역류질환', 'confirmed', NOW());
SET @rx9 = LAST_INSERT_ID();

-- ===== 약물 데이터 =====
-- p1: 1개
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx1, '타이레놀정 500mg', '500mg', '1일 3회', '5일', '식후 30분 복용');

-- p2: 2개
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx2, '아모디핀정 5mg', '5mg', '1일 1회', '30일', '아침 식후 복용'),
  (@rx2, '로사르탄정 50mg', '50mg', '1일 1회', '30일', '아침 식후 복용');

-- p3: 3개
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx3, '가스모틴정 5mg', '5mg', '1일 3회', '14일', '식전 30분 복용'),
  (@rx3, '판토프라졸정 40mg', '40mg', '1일 1회', '14일', '아침 식전 복용'),
  (@rx3, '트리메부틴정 100mg', '100mg', '1일 3회', '14일', '식후 복용');

-- p4: 4개
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx4, '메트포르민정 500mg', '500mg', '1일 2회', '30일', '아침·저녁 식후 복용'),
  (@rx4, '글리메피리드정 2mg', '2mg', '1일 1회', '30일', '아침 식전 복용'),
  (@rx4, '텔미사르탄정 40mg', '40mg', '1일 1회', '30일', '아침 식후 복용'),
  (@rx4, '로수바스타틴정 10mg', '10mg', '1일 1회', '30일', '저녁 식후 복용');

-- p5: 5개
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx5, '클로피도그렐정 75mg', '75mg', '1일 1회', '30일', '아침 식후 복용'),
  (@rx5, '이소소르비드정 10mg', '10mg', '1일 3회', '30일', '식후 복용'),
  (@rx5, '셀레콕시브캡슐 200mg', '200mg', '1일 1회', '14일', '식후 복용'),
  (@rx5, '레바미피드정 100mg', '100mg', '1일 3회', '14일', '식후 복용'),
  (@rx5, '타나민정 40mg', '40mg', '1일 3회', '30일', '식후 복용');

-- p6: 2개
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx6, '세티리진정 10mg', '10mg', '1일 1회', '14일', '저녁 취침 전 복용'),
  (@rx6, '프로토픽연고 0.1%', '적당량', '1일 2회', '14일', '환부에 얇게 도포');

-- p7: 6개 (스크롤 테스트)
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx7, '스피리바캡슐 18mcg', '18mcg', '1일 1회', '30일', '아침 흡입'),
  (@rx7, '심비코트터부헤일러', '1회 2흡입', '1일 2회', '30일', '아침·저녁 흡입 후 양치'),
  (@rx7, '와파린정 2mg', '2mg', '1일 1회', '30일', '저녁 일정한 시간 복용'),
  (@rx7, '디곡신정 0.125mg', '0.125mg', '1일 1회', '30일', '아침 식전 복용'),
  (@rx7, '포사맥스정 70mg', '70mg', '주 1회', '12주', '기상 직후 공복, 물 200ml와 함께'),
  (@rx7, '칼시트리올캡슐 0.25mcg', '0.25mcg', '1일 1회', '30일', '아침 식후 복용');

-- p8: 1개
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx8, '이부프로펜정 200mg', '200mg', '1일 3회 (필요시)', '5일', '식후 복용, 통증 시');

-- p9: 3개
INSERT INTO medications (prescription_id, name, dosage, frequency, duration, instructions) VALUES
  (@rx9, '에소메프라졸정 20mg', '20mg', '1일 1회', '28일', '아침 식전 복용'),
  (@rx9, '돔페리돈정 10mg', '10mg', '1일 3회', '14일', '식전 15~30분 복용'),
  (@rx9, '알마겔현탁액', '15ml', '1일 3회', '14일', '식후 1시간·취침 전 복용');
"
echo "  ✓ 처방전·약물 생성 완료"

echo "[6/6] 복약 스케줄 생성 (오늘의 복약 표시용)..."
run_sql "
SET @p1 = (SELECT id FROM users WHERE email='testp1@test.com');
SET @p2 = (SELECT id FROM users WHERE email='testp2@test.com');
SET @p3 = (SELECT id FROM users WHERE email='testp3@test.com');
SET @p4 = (SELECT id FROM users WHERE email='testp4@test.com');
SET @p5 = (SELECT id FROM users WHERE email='testp5@test.com');
SET @p6 = (SELECT id FROM users WHERE email='testp6@test.com');
SET @p7 = (SELECT id FROM users WHERE email='testp7@test.com');
SET @p8 = (SELECT id FROM users WHERE email='testp8@test.com');
SET @p9 = (SELECT id FROM users WHERE email='testp9@test.com');

-- 처방전 ID 조회
SET @rx1 = (SELECT id FROM prescriptions WHERE user_id=@p1 ORDER BY id DESC LIMIT 1);
SET @rx2 = (SELECT id FROM prescriptions WHERE user_id=@p2 ORDER BY id DESC LIMIT 1);
SET @rx3 = (SELECT id FROM prescriptions WHERE user_id=@p3 ORDER BY id DESC LIMIT 1);
SET @rx4 = (SELECT id FROM prescriptions WHERE user_id=@p4 ORDER BY id DESC LIMIT 1);
SET @rx5 = (SELECT id FROM prescriptions WHERE user_id=@p5 ORDER BY id DESC LIMIT 1);
SET @rx6 = (SELECT id FROM prescriptions WHERE user_id=@p6 ORDER BY id DESC LIMIT 1);
SET @rx7 = (SELECT id FROM prescriptions WHERE user_id=@p7 ORDER BY id DESC LIMIT 1);
SET @rx8 = (SELECT id FROM prescriptions WHERE user_id=@p8 ORDER BY id DESC LIMIT 1);
SET @rx9 = (SELECT id FROM prescriptions WHERE user_id=@p9 ORDER BY id DESC LIMIT 1);

-- medication_schedules 생성
-- p1: 타이레놀 → 아침·점심·저녁
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, t.time_of_day, '${START_DATE}', '${END_DATE}'
  FROM medications m
  CROSS JOIN (SELECT 'MORNING' AS time_of_day UNION SELECT 'NOON' UNION SELECT 'EVENING') t
  WHERE m.prescription_id = @rx1;

-- p2: 아모디핀 → 아침, 로사르탄 → 아침
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'MORNING', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx2;

-- p3: 가스모틴 → 아침·점심·저녁, 판토프라졸 → 아침, 트리메부틴 → 아침·점심·저녁
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, t.time_of_day, '${START_DATE}', '${END_DATE}'
  FROM medications m
  CROSS JOIN (SELECT 'MORNING' AS time_of_day UNION SELECT 'NOON' UNION SELECT 'EVENING') t
  WHERE m.prescription_id = @rx3 AND m.name IN ('가스모틴정 5mg', '트리메부틴정 100mg');
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'MORNING', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx3 AND m.name = '판토프라졸정 40mg';

-- p4: 메트포르민 → 아침·저녁, 글리메피리드 → 아침, 텔미사르탄 → 아침, 로수바스타틴 → 저녁
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, t.time_of_day, '${START_DATE}', '${END_DATE}'
  FROM medications m
  CROSS JOIN (SELECT 'MORNING' AS time_of_day UNION SELECT 'EVENING') t
  WHERE m.prescription_id = @rx4 AND m.name = '메트포르민정 500mg';
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'MORNING', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx4 AND m.name IN ('글리메피리드정 2mg', '텔미사르탄정 40mg');
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'EVENING', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx4 AND m.name = '로수바스타틴정 10mg';

-- p5: 클로피도그렐 → 아침, 이소소르비드/레바미피드/타나민 → 아침·점심·저녁, 셀레콕시브 → 아침
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'MORNING', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx5 AND m.name IN ('클로피도그렐정 75mg', '셀레콕시브캡슐 200mg');
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, t.time_of_day, '${START_DATE}', '${END_DATE}'
  FROM medications m
  CROSS JOIN (SELECT 'MORNING' AS time_of_day UNION SELECT 'NOON' UNION SELECT 'EVENING') t
  WHERE m.prescription_id = @rx5 AND m.name IN ('이소소르비드정 10mg', '레바미피드정 100mg', '타나민정 40mg');

-- p6: 세티리진 → 취침, 프로토픽 → 아침·저녁
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'BEDTIME', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx6 AND m.name = '세티리진정 10mg';
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, t.time_of_day, '${START_DATE}', '${END_DATE}'
  FROM medications m
  CROSS JOIN (SELECT 'MORNING' AS time_of_day UNION SELECT 'EVENING') t
  WHERE m.prescription_id = @rx6 AND m.name LIKE '프로토픽%';

-- p7: 스피리바 → 아침, 심비코트 → 아침·저녁, 와파린 → 저녁, 디곡신 → 아침, 포사맥스 → 아침(주1회이지만 스케줄용), 칼시트리올 → 아침
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'MORNING', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx7 AND m.name IN ('스피리바캡슐 18mcg', '디곡신정 0.125mg', '포사맥스정 70mg', '칼시트리올캡슐 0.25mcg');
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, t.time_of_day, '${START_DATE}', '${END_DATE}'
  FROM medications m
  CROSS JOIN (SELECT 'MORNING' AS time_of_day UNION SELECT 'EVENING') t
  WHERE m.prescription_id = @rx7 AND m.name LIKE '심비코트%';
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'EVENING', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx7 AND m.name = '와파린정 2mg';

-- p8: 이부프로펜 → 아침·점심·저녁 (필요시)
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, t.time_of_day, '${START_DATE}', '${END_DATE}'
  FROM medications m
  CROSS JOIN (SELECT 'MORNING' AS time_of_day UNION SELECT 'NOON' UNION SELECT 'EVENING') t
  WHERE m.prescription_id = @rx8;

-- p9: 에소메프라졸 → 아침, 돔페리돈/알마겔 → 아침·점심·저녁
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, 'MORNING', '${START_DATE}', '${END_DATE}'
  FROM medications m WHERE m.prescription_id = @rx9 AND m.name = '에소메프라졸정 20mg';
INSERT INTO medication_schedules (medication_id, time_of_day, start_date, end_date)
  SELECT m.id, t.time_of_day, '${START_DATE}', '${END_DATE}'
  FROM medications m
  CROSS JOIN (SELECT 'MORNING' AS time_of_day UNION SELECT 'NOON' UNION SELECT 'EVENING') t
  WHERE m.prescription_id = @rx9 AND m.name IN ('돔페리돈정 10mg', '알마겔현탁액');

-- ===== 복약 가이드 생성 (completed 상태) =====
INSERT INTO guides (user_id, prescription_id, content, status, created_at) VALUES
(@p1, @rx1, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','타이레놀정 500mg','dosage','500mg','frequency','1일 3회','duration','5일','instructions','식후 30분 복용','effect','해열·진통','precautions','간 질환 시 용량 조절 필요')
  ),
  'warnings', JSON_OBJECT('drug_interactions','알코올과 병용 시 간독성 증가','side_effects','장기 복용 시 간기능 이상','alcohol','복용 중 음주 금지'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('충분한 수분 섭취'), 'exercise', JSON_ARRAY('충분한 휴식'))
), 'completed', NOW()),

(@p2, @rx2, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','아모디핀정 5mg','dosage','5mg','frequency','1일 1회','duration','30일','instructions','아침 식후','effect','칼슘채널차단제, 혈압 강하','precautions','어지러움 주의'),
    JSON_OBJECT('name','로사르탄정 50mg','dosage','50mg','frequency','1일 1회','duration','30일','instructions','아침 식후','effect','ARB 계열, 혈압 강하','precautions','고칼륨혈증 주의')
  ),
  'warnings', JSON_OBJECT('drug_interactions','칼륨 보충제 병용 주의','side_effects','두통, 어지러움','alcohol','음주 시 혈압 급강하 위험'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('저염식 권장','칼륨 풍부 식품 적당량'), 'exercise', JSON_ARRAY('규칙적 유산소 운동 30분'))
), 'completed', NOW()),

(@p3, @rx3, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','가스모틴정 5mg','dosage','5mg','frequency','1일 3회','duration','14일','instructions','식전 30분','effect','위장관 운동 촉진','precautions','식전 복용 준수'),
    JSON_OBJECT('name','판토프라졸정 40mg','dosage','40mg','frequency','1일 1회','duration','14일','instructions','아침 식전','effect','프로톤펌프억제제, 위산 분비 억제','precautions','장기 복용 시 마그네슘 수치 확인'),
    JSON_OBJECT('name','트리메부틴정 100mg','dosage','100mg','frequency','1일 3회','duration','14일','instructions','식후','effect','위장관 운동 조절','precautions','졸음 유발 가능')
  ),
  'warnings', JSON_OBJECT('drug_interactions','특이 상호작용 없음','side_effects','변비, 설사, 두통','alcohol','위장 자극 증가'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('소량씩 자주 식사','맵고 기름진 음식 자제'), 'exercise', JSON_ARRAY('식후 가벼운 산책'))
), 'completed', NOW()),

(@p4, @rx4, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','메트포르민정 500mg','dosage','500mg','frequency','1일 2회','duration','30일','instructions','아침·저녁 식후','effect','인슐린 감수성 개선','precautions','유산산증 주의, 조영제 검사 전 중단'),
    JSON_OBJECT('name','글리메피리드정 2mg','dosage','2mg','frequency','1일 1회','duration','30일','instructions','아침 식전','effect','인슐린 분비 촉진','precautions','저혈당 주의'),
    JSON_OBJECT('name','텔미사르탄정 40mg','dosage','40mg','frequency','1일 1회','duration','30일','instructions','아침 식후','effect','혈압 강하, 신장 보호','precautions','임신 시 금기'),
    JSON_OBJECT('name','로수바스타틴정 10mg','dosage','10mg','frequency','1일 1회','duration','30일','instructions','저녁 식후','effect','콜레스테롤 감소','precautions','근육통 발생 시 즉시 보고')
  ),
  'warnings', JSON_OBJECT('drug_interactions','메트포르민+조영제 주의','side_effects','소화불량, 근육통, 저혈당','alcohol','저혈당 및 유산산증 위험 증가'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('저탄수화물식','식이섬유 충분히'), 'exercise', JSON_ARRAY('식후 30분 걷기','주 150분 중강도 운동'))
), 'completed', NOW()),

(@p5, @rx5, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','클로피도그렐정 75mg','dosage','75mg','frequency','1일 1회','duration','30일','instructions','아침 식후','effect','항혈소판제','precautions','출혈 위험 증가'),
    JSON_OBJECT('name','이소소르비드정 10mg','dosage','10mg','frequency','1일 3회','duration','30일','instructions','식후','effect','혈관 확장, 협심증 예방','precautions','두통 발생 가능'),
    JSON_OBJECT('name','셀레콕시브캡슐 200mg','dosage','200mg','frequency','1일 1회','duration','14일','instructions','식후','effect','COX-2 선택적 소염진통','precautions','심혈관 위험 증가 가능'),
    JSON_OBJECT('name','레바미피드정 100mg','dosage','100mg','frequency','1일 3회','duration','14일','instructions','식후','effect','위점막 보호','precautions','특이 부작용 드묾'),
    JSON_OBJECT('name','타나민정 40mg','dosage','40mg','frequency','1일 3회','duration','30일','instructions','식후','effect','혈액순환 개선','precautions','출혈 경향 증가 가능')
  ),
  'warnings', JSON_OBJECT('drug_interactions','클로피도그렐+셀레콕시브 출혈 위험','side_effects','출혈, 두통, 소화불량','alcohol','출혈 위험 현저히 증가'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('비타민K 일정량 유지','오메가3 풍부 식품'), 'exercise', JSON_ARRAY('무리한 운동 자제','규칙적 가벼운 산책'))
), 'completed', NOW()),

(@p6, @rx6, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','세티리진정 10mg','dosage','10mg','frequency','1일 1회','duration','14일','instructions','취침 전','effect','항히스타민제, 가려움 완화','precautions','졸음 유발'),
    JSON_OBJECT('name','프로토픽연고 0.1%','dosage','적당량','frequency','1일 2회','duration','14일','instructions','환부 도포','effect','면역조절, 피부염 완화','precautions','도포 후 자외선 차단 필수')
  ),
  'warnings', JSON_OBJECT('drug_interactions','특이 상호작용 없음','side_effects','졸음, 도포 부위 작열감','alcohol','졸음 증가'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('항염증 식품 섭취','가공식품 자제'), 'exercise', JSON_ARRAY('땀이 과도한 운동 자제'))
), 'completed', NOW()),

(@p7, @rx7, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','스피리바캡슐 18mcg','dosage','18mcg','frequency','1일 1회','duration','30일','instructions','아침 흡입','effect','기관지 확장','precautions','흡입 후 입 헹굼'),
    JSON_OBJECT('name','심비코트터부헤일러','dosage','1회 2흡입','frequency','1일 2회','duration','30일','instructions','아침·저녁 흡입','effect','기관지 확장+스테로이드','precautions','흡입 후 반드시 양치'),
    JSON_OBJECT('name','와파린정 2mg','dosage','2mg','frequency','1일 1회','duration','30일','instructions','저녁 일정 시간','effect','항응고제','precautions','INR 정기 모니터링, 비타민K 식품 일정'),
    JSON_OBJECT('name','디곡신정 0.125mg','dosage','0.125mg','frequency','1일 1회','duration','30일','instructions','아침 식전','effect','심박수 조절','precautions','독성 증상(오심, 시야 이상) 즉시 보고'),
    JSON_OBJECT('name','포사맥스정 70mg','dosage','70mg','frequency','주 1회','duration','12주','instructions','기상 직후 공복','effect','골밀도 증가','precautions','복용 후 30분 눕지 않기'),
    JSON_OBJECT('name','칼시트리올캡슐 0.25mcg','dosage','0.25mcg','frequency','1일 1회','duration','30일','instructions','아침 식후','effect','칼슘 흡수 촉진','precautions','고칼슘혈증 주의')
  ),
  'warnings', JSON_OBJECT('drug_interactions','와파린+다수 약물 상호작용 주의, 디곡신 독성 모니터링','side_effects','출혈, 구강 칸디다증, 오심','alcohol','와파린 효과 변동, 출혈 위험'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('비타민K 함유 식품 일정량 유지','칼슘·비타민D 충분히'), 'exercise', JSON_ARRAY('호흡 재활 운동','낙상 예방 운동'))
), 'completed', NOW()),

(@p8, @rx8, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','이부프로펜정 200mg','dosage','200mg','frequency','1일 3회 필요시','duration','5일','instructions','식후 복용','effect','소염진통','precautions','공복 복용 금지, 위장 자극')
  ),
  'warnings', JSON_OBJECT('drug_interactions','아스피린 병용 주의','side_effects','위장 장애, 두통','alcohol','위장 출혈 위험'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('충분한 수분'), 'exercise', JSON_ARRAY('스트레칭','눈 휴식')))
, 'completed', NOW()),

(@p9, @rx9, JSON_OBJECT(
  'medication_guides', JSON_ARRAY(
    JSON_OBJECT('name','에소메프라졸정 20mg','dosage','20mg','frequency','1일 1회','duration','28일','instructions','아침 식전','effect','위산 분비 억제','precautions','장기 복용 시 골밀도 저하'),
    JSON_OBJECT('name','돔페리돈정 10mg','dosage','10mg','frequency','1일 3회','duration','14일','instructions','식전 15~30분','effect','위장관 운동 촉진','precautions','심장 부정맥 주의'),
    JSON_OBJECT('name','알마겔현탁액','dosage','15ml','frequency','1일 3회','duration','14일','instructions','식후 1시간','effect','제산제, 위점막 보호','precautions','다른 약과 2시간 간격')
  ),
  'warnings', JSON_OBJECT('drug_interactions','알마겔이 다른 약물 흡수 방해 가능','side_effects','변비, 두통','alcohol','위산 역류 악화'),
  'lifestyle', JSON_OBJECT('diet', JSON_ARRAY('야식 금지','식사 후 2시간 내 눕지 않기'), 'exercise', JSON_ARRAY('복부 압박 운동 자제','식후 가벼운 산책'))
), 'completed', NOW());
"
echo "  ✓ 스케줄·가이드 생성 완료"

echo ""
echo "============================================="
echo " Seed 완료!"
echo "============================================="
echo ""
echo " PATIENT 계정"
echo "  testp1@test.com (김건강) — 약 1개, 건강한 청년"
echo "  testp2@test.com (이복약) — 약 2개, 고혈압, 알레르기, LARGE 폰트"
echo "  testp3@test.com (박처방) — 약 3개, 소화불량"
echo "  testp4@test.com (최영양) — 약 4개, 당뇨+고혈압, LARGE 폰트"
echo "  testp5@test.com (정운동) — 약 5개, 고령+복합질환, LARGE 폰트"
echo "  testp6@test.com (강미소) — 약 2개, 아토피, 젊은 여성"
echo "  testp7@test.com (조활력) — 약 6개(스크롤), 고령+복합질환, LARGE 폰트"
echo "  testp8@test.com (윤평화) — 약 1개, 청소년, 프로필 미입력"
echo "  testp9@test.com (한든든) — 약 3개, GERD, 성별·키·체중 미입력"
echo ""
echo " GUARDIAN 계정"
echo "  testg1@test.com (김보호) → testp1, testp2, testp3"
echo "  testg2@test.com (이돌봄) → testp4, testp5, testp6"
echo "  testg3@test.com (박사랑) → testp7, testp8, testp9"
echo "============================================="
