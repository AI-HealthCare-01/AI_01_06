# API Specification Summary

이 문서는 전체 API 엔드포인트의 구조와 목적을 요약한 내용입니다.

## COMMON 도메인
- **표준 응답 래퍼**
  - 모든 API 공통 응답 (success, data, error)

## AUTH 도메인
- **회원가입** (`POST` /api/auth/signup)
  - 인증 필요: N / 역할: ALL
- **로그인** (`POST` /api/auth/login)
  - 인증 필요: N / 역할: ALL
- **토큰 재발급** (`POST` /api/auth/refresh)
  - 인증 필요: N / 역할: ALL
- **로그아웃** (`POST` /api/auth/logout)
  - 인증 필요: Y / 역할: ALL

## USER 도메인
- **내 정보 조회** (`GET` /api/users/me)
  - 인증 필요: Y / 역할: ALL
- **내 정보 수정** (`PATCH` /api/users/me)
  - 인증 필요: Y / 역할: ALL
- **접근성 설정 변경** (`PATCH` /api/users/me/accessibility)
  - 인증 필요: Y / 역할: ALL
- **회원 탈퇴** (`DELETE` /api/users/me)
  - 인증 필요: Y / 역할: ALL

## PRESCRIPTION 도메인
- **처방전 업로드** (`POST` /api/prescriptions)
  - 인증 필요: Y / 역할: PATIENT
- **처방전 목록 조회** (`GET` /api/prescriptions)
  - 인증 필요: Y / 역할: PATIENT
- **처방전 상세 조회** (`GET` /api/prescriptions/{prescription_id})
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER
- **처방전 삭제** (`DELETE` /api/prescriptions/{prescription_id})
  - 인증 필요: Y / 역할: PATIENT

## OCR 도메인
- **OCR 결과 조회** (`GET` /api/prescriptions/{prescription_id}/ocr)
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER
- **OCR 수정** (`PUT` /api/prescriptions/{prescription_id}/ocr)
  - 인증 필요: Y / 역할: PATIENT

## MEDICATION 도메인
- **약 목록 조회** (`GET` /api/prescriptions/{prescription_id}/medications)
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER
- **약 상세 조회** (`GET` /api/medications/{medication_id})
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER

## GUIDE 도메인
- **복약 가이드 생성** (`POST` /api/guides)
  - 인증 필요: Y / 역할: PATIENT
- **복약 가이드 조회** (`GET` /api/guides/{guide_id})
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER
- **가이드 PDF 다운로드** (`GET` /api/guides/{guide_id}/pdf)
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER

## SCHEDULE 도메인
- **스케줄 생성** (`POST` /api/schedules)
  - 인증 필요: Y / 역할: PATIENT
- **스케줄 조회(상위)** (`GET` /api/schedules)
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER
- **스케줄 인스턴스 조회(일)** (`GET` /api/schedule-instances)
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER
- **인스턴스 상세 조회** (`GET` /api/schedule-instances/{instance_id})
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER
- **스케줄 수정(상위)** (`PATCH` /api/schedules/{schedule_id})
  - 인증 필요: Y / 역할: PATIENT
- **스케줄 삭제(상위)** (`DELETE` /api/schedules/{schedule_id})
  - 인증 필요: Y / 역할: PATIENT

## ADHERENCE 도메인
- **복약 완료 체크** (`POST` /api/adherence)
  - 인증 필요: Y / 역할: PATIENT
- **복약 스킵 체크** (`POST` /api/adherence/skip)
  - 인증 필요: Y / 역할: PATIENT
- **이행 기록 조회** (`GET` /api/adherence)
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER
- **이행 통계 조회** (`GET` /api/adherence/stat)
  - 인증 필요: Y / 역할: PATIENT/CAREGIVER

## CAREGIVER 도메인
- **연결 요청** (`POST` /api/caregivers/requests)
  - 인증 필요: Y / 역할: CAREGIVER
- **연결 요청 목록(환자)** (`GET` /api/caregivers/requests/inbox)
  - 인증 필요: Y / 역할: PATIENT
- **연결 승인(환자)** (`PATCH` /api/caregivers/requests/{request_id}/approve)
  - 인증 필요: Y / 역할: PATIENT
- **연결 거절(환자)** (`PATCH` /api/caregivers/requests/{request_id}/reject)
  - 인증 필요: Y / 역할: PATIENT
- **연결된 환자 목록(보호자)** (`GET` /api/caregivers/patients)
  - 인증 필요: Y / 역할: CAREGIVER
- **연결 해제(보호자)** (`DELETE` /api/caregivers/patients/{mapping_id})
  - 인증 필요: Y / 역할: CAREGIVER

## CHAT 도메인
- **대화방 목록** (`GET` /api/chat/threads)
  - 인증 필요: Y / 역할: ALL
- **대화방 생성** (`POST` /api/chat/threads)
  - 인증 필요: Y / 역할: ALL
- **메시지 전송** (`POST` /api/chat/messages)
  - 인증 필요: Y / 역할: ALL
- **메시지 목록 조회** (`GET` /api/chat/threads/{thread_id}/messages)
  - 인증 필요: Y / 역할: ALL
- **메시지 피드백** (`POST` /api/chat/feedback)
  - 인증 필요: Y / 역할: ALL

## NOTIFICATION 도메인
- **알림 목록 조회** (`GET` /api/notifications)
  - 인증 필요: Y / 역할: ALL
- **알림 읽음 처리** (`PATCH` /api/notifications/{notification_id}/read)
  - 인증 필요: Y / 역할: ALL
- **전체 읽음 처리** (`PATCH` /api/notifications/read-all)
  - 인증 필요: Y / 역할: ALL

## AUDIT 도메인
- **감사 로그 조회** (`GET` /api/admin/audit)
  - 인증 필요: Y / 역할: ADMIN