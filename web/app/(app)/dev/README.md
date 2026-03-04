# Dev Test Page

접속 경로: `http://localhost:3000/dev`

개발 중 화면 이동 및 기능 연결을 빠르게 확인하기 위한 테스트 메뉴 페이지입니다.

## 구성

### prescription id 입력창
- 챗봇/한방에 버튼의 동적 경로(`[id]`)에 사용할 처방 ID를 지정합니다.
- 기본값: `1`
- 비어있거나 숫자가 아니면 `1`로 fallback → `WARN: invalid id, fallback to 1` 로그 출력

### 버튼 목록

| 버튼 | 동작 | 로그 |
|------|------|------|
| OCR 업로드 | `/prescriptions/upload` 이동 | `CLICK` + `NAV` |
| 챗봇 연결 | `/prescriptions/{id}/chat` 이동 | `CLICK` + `NAV` |
| 회원가입 (로컬) | `/signup` 이동 | `CLICK` + `NAV` |
| 회원가입 (구글) | 이동 없음 (OAuth 미연동) | `CLICK` + `INFO: OAuth not implemented` |
| 회원가입 (카카오) | 이동 없음 (OAuth 미연동) | `CLICK` + `INFO: OAuth not implemented` |
| 한방에 테스트 | 아래 자동 시나리오 실행 | 각 단계별 로그 |

### 한방에 테스트 시나리오
1. `START: one-click test (id={id})`
2. `/prescriptions/{id}/ocr` 로 이동 → `NAV` 로그
3. 800ms 대기 → `WAIT: 800ms` 로그
4. `/prescriptions/{id}/chat` 로 이동 → `NAV` 로그
5. `DONE`

- 진행 중 버튼은 disabled + "테스트 진행 중..." 문구로 변경
- `setTimeout` ref로 관리 → 연타/unmount 시 타이머 자동 clear

### LOG 영역
- 모든 버튼 클릭/이동/경고를 `[HH:MM:SS] 메시지` 형태로 기록
- 새 로그는 아래로 쌓이며 최대 50줄 유지 (초과 시 앞에서 제거)
- 로그 없으면 "아직 로그 없음" 표시
