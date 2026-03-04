'use client';

import Link from 'next/link';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DevTestPage() {
  const router = useRouter();
  const [prescriptionId, setPrescriptionId] = useState('1');
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const addLog = useCallback((msg: string) => {
    const t = new Date().toLocaleTimeString('ko-KR', { hour12: false });
    setLogs((prev) => [...prev, `[${t}] ${msg}`].slice(-50));
  }, []);

  const resolveId = useCallback(
    (raw: string): string => {
      const trimmed = raw.trim();
      if (!trimmed || !/^\d+$/.test(trimmed)) {
        addLog('WARN: invalid id, fallback to 1');
        return '1';
      }
      return trimmed;
    },
    [addLog],
  );

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const handleOneClick = async () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    const id = resolveId(prescriptionId);
    setRunning(true);
    addLog(`START: one-click test (id=${id})`);
    router.push(`/prescriptions/${id}/ocr`);
    addLog(`NAV: /prescriptions/${id}/ocr`);
    await new Promise<void>((r) => {
      timerRef.current = setTimeout(r, 800);
    });
    addLog('WAIT: 800ms');
    router.push(`/prescriptions/${id}/chat`);
    addLog(`NAV: /prescriptions/${id}/chat`);
    addLog('DONE');
    setRunning(false);
  };

  return (
    <div style={styles.page}>
      <div style={styles.phone}>
        <div style={styles.header}>
          <div style={styles.title}>Dev Test</div>
          <div style={styles.subTitle}>기능 연결 확인용 테스트 메뉴</div>
        </div>

        <div style={styles.content}>
          <div style={styles.fieldRow}>
            <label style={styles.label}>prescription id</label>
            <input
              value={prescriptionId}
              onChange={(e) => setPrescriptionId(e.target.value)}
              style={styles.input}
              placeholder="예: 1"
              inputMode="numeric"
            />
          </div>

          <div style={styles.btnList}>
            {/* OCR 업로드 */}
            <Link
              href="/prescriptions/upload"
              style={styles.btn}
              onClick={() => {
                addLog('CLICK: OCR 업로드');
                addLog('NAV: /prescriptions/upload 로 이동');
              }}
            >
              <div style={styles.btnLabel}>OCR 업로드</div>
              <div style={styles.btnNote}>업로드 화면으로 이동</div>
            </Link>

            {/* 챗봇 연결 */}
            <Link
              href={`/prescriptions/${resolveId(prescriptionId)}/chat`}
              style={styles.btn}
              onClick={() => {
                const id = resolveId(prescriptionId);
                addLog('CLICK: 챗봇 연결');
                addLog(`NAV: /prescriptions/${id}/chat 로 이동`);
              }}
            >
              <div style={styles.btnLabel}>챗봇 연결</div>
              <div style={styles.btnNote}>처방 id={prescriptionId} 기준 챗봇 화면</div>
            </Link>

            {/* 회원가입 로컬 */}
            <Link
              href="/signup"
              style={styles.btn}
              onClick={() => {
                addLog('CLICK: 회원가입(로컬)');
                addLog('NAV: /signup 로 이동');
              }}
            >
              <div style={styles.btnLabel}>회원가입 (로컬)</div>
              <div style={styles.btnNote}>로컬 회원가입 UI로 이동</div>
            </Link>

            {/* 회원가입 구글 */}
            <button
              style={styles.btn}
              onClick={() => {
                addLog('CLICK: 회원가입(구글)');
                addLog('INFO: OAuth not implemented');
              }}
            >
              <div style={styles.btnLabel}>회원가입 (구글)</div>
              <div style={styles.btnNote}>OAuth 연결 전 — 이동 없음</div>
            </button>

            {/* 회원가입 카카오 */}
            <button
              style={styles.btn}
              onClick={() => {
                addLog('CLICK: 회원가입(카카오)');
                addLog('INFO: OAuth not implemented');
              }}
            >
              <div style={styles.btnLabel}>회원가입 (카카오)</div>
              <div style={styles.btnNote}>OAuth 연결 전 — 이동 없음</div>
            </button>

            {/* 한방에 테스트 */}
            <button
              style={{ ...styles.btn, ...styles.btnPrimary, ...(running ? styles.btnDisabled : {}) }}
              disabled={running}
              onClick={handleOneClick}
            >
              <div style={styles.btnLabel}>{running ? '테스트 진행 중...' : '한방에 테스트'}</div>
              <div style={styles.btnNote}>OCR → 챗봇 화면을 자동으로 이동하며 확인</div>
            </button>
          </div>

          <div style={styles.logBox}>
            <div style={styles.logTitle}>LOG</div>
            {logs.length === 0 ? (
              <div style={styles.logEmpty}>아직 로그 없음</div>
            ) : (
              <ul style={styles.logList}>
                {logs.map((l, i) => (
                  <li key={i} style={styles.logItem}>{l}</li>
                ))}
              </ul>
            )}
          </div>

          <div style={styles.footer}>
            접속 경로: <code>/dev</code> (개발용)
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    background: '#0b0b0f',
  },
  phone: {
    width: 360,
    maxWidth: '100%',
    borderRadius: 28,
    border: '1px solid rgba(255,255,255,0.12)',
    background: '#12121a',
    boxShadow: '0 10px 40px rgba(0,0,0,0.45)',
    overflow: 'hidden',
  },
  header: {
    padding: '18px 18px 10px',
    background: 'linear-gradient(90deg, rgba(120,78,255,0.25), rgba(255,255,255,0))',
    borderBottom: '1px solid rgba(255,255,255,0.10)',
  },
  title: { fontSize: 22, fontWeight: 800, color: 'white' },
  subTitle: { marginTop: 6, fontSize: 13, color: 'rgba(255,255,255,0.7)' },
  content: { padding: 18, display: 'flex', flexDirection: 'column', gap: 14 },
  fieldRow: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 12, color: 'rgba(255,255,255,0.7)' },
  input: {
    height: 40,
    borderRadius: 12,
    border: '1px solid rgba(255,255,255,0.14)',
    background: 'rgba(255,255,255,0.06)',
    color: 'white',
    padding: '0 12px',
    outline: 'none',
  },
  btnList: { display: 'flex', flexDirection: 'column', gap: 10 },
  btn: {
    width: '100%',
    textDecoration: 'none',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    gap: 4,
    padding: '14px 14px',
    borderRadius: 14,
    border: '1px solid rgba(255,255,255,0.14)',
    background: 'rgba(255,255,255,0.05)',
    color: 'white',
    cursor: 'pointer',
  },
  btnPrimary: {
    background: 'rgba(120,78,255,0.18)',
    border: '1px solid rgba(120,78,255,0.35)',
  },
  btnDisabled: { opacity: 0.4, cursor: 'not-allowed' },
  btnLabel: { fontSize: 15, fontWeight: 700 },
  btnNote: { fontSize: 12, color: 'rgba(255,255,255,0.7)' },
  logBox: {
    marginTop: 4,
    padding: 12,
    borderRadius: 14,
    border: '1px solid rgba(255,255,255,0.10)',
    background: 'rgba(255,255,255,0.03)',
  },
  logTitle: { fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.8)', marginBottom: 8 },
  logEmpty: { fontSize: 12, color: 'rgba(255,255,255,0.55)' },
  logList: { margin: 0, paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 4 },
  logItem: { fontSize: 12, color: 'rgba(255,255,255,0.8)' },
  footer: { fontSize: 12, color: 'rgba(255,255,255,0.6)', paddingTop: 4 },
};
