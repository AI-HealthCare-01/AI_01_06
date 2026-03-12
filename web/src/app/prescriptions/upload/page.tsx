"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

export default function PrescriptionUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    const res = await api.uploadPrescription(file);
    if (res.success && res.data) {
      const data = res.data as { id: number };
      router.push(`/prescriptions/${data.id}/ocr`);
    } else {
      setError(res.error || "업로드에 실패했습니다.");
      setUploading(false);
    }
  };

  return (
    <AppLayout>
      <h1 className="text-2xl font-bold mb-2">처방전 올리기</h1>
      <p className="mb-6" style={{ color: 'var(--color-text-muted)' }}>병원에서 받은 처방전을 넣어주세요</p>

      {/* Stepper */}
      <div className="flex items-center gap-2 mb-8">
        <div className="px-4 py-2 rounded-full text-sm font-medium text-white" style={{ background: 'var(--color-primary)' }}>처방전 올리기</div>
        <span style={{ color: 'var(--color-text-muted)' }}>→</span>
        <div className="px-4 py-2 rounded-full text-sm" style={{ background: 'var(--color-surface)', color: 'var(--color-text-muted)' }}>내용 확인</div>
        <span style={{ color: 'var(--color-text-muted)' }}>→</span>
        <div className="px-4 py-2 rounded-full text-sm" style={{ background: 'var(--color-surface)', color: 'var(--color-text-muted)' }}>가이드 생성</div>
      </div>

      {/* Upload area */}
      <div className="rounded-lg p-12 text-center mb-4" style={{ background: 'var(--color-surface)', border: '2px dashed var(--color-border)' }}>
        <div className="space-y-4">
          <p style={{ color: 'var(--color-text-muted)' }}>처방전 이미지를 업로드해주세요</p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => fileRef.current?.click()}
              className="px-6 py-3 rounded-lg text-white transition-colors" style={{ background: 'var(--color-text-muted)' }}
            >
              사진 선택
            </button>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>
      </div>

      {/* File info */}
      {file && (
        <div className="rounded-lg p-4 flex items-center justify-between mb-4" style={{ background: 'var(--color-card-bg)', border: '1px solid var(--color-border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded flex items-center justify-center" style={{ background: 'var(--color-primary-soft)', color: 'var(--color-primary)' }}>📄</div>
            <div>
              <p className="font-medium text-sm">{file.name}</p>
              <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
          <button onClick={() => setFile(null)} className="text-sm px-3 py-1 rounded transition-colors" style={{ color: 'var(--color-text-muted)', background: 'var(--color-surface)' }}>
            제거
          </button>
        </div>
      )}

      {/* Warnings */}
      <div className="alert-warning rounded-lg p-4 mb-6">
        <p className="font-bold text-sm mb-1">주의사항</p>
        <ul className="text-sm list-disc list-inside space-y-1">
          <li>처방전 전체가 선명하게 보이도록 촬영해주세요</li>
          <li>약물명과 용량이 잘 보이는지 확인해주세요</li>
          <li>개인 정보는 안전하게 암호화되어 저장됩니다</li>
        </ul>
      </div>

      {error && <p className="text-sm mb-4" style={{ color: 'var(--color-danger)' }}>{error}</p>}

      <div className="flex gap-4">
        <button onClick={() => router.back()} className="flex-1 py-3 rounded-lg btn-outline">취소</button>
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="flex-1 py-3 btn-primary"
        >
          {uploading ? "업로드 중..." : "다음 단계로 →"}
        </button>
      </div>
    </AppLayout>
  );
}
