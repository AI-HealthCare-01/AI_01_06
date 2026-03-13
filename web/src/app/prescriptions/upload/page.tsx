"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import { api } from "@/lib/api";

export default function PrescriptionUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] || null;
    setFile(selected);
    if (selected) {
      setPreview(URL.createObjectURL(selected));
    } else {
      setPreview(null);
    }
  };

  const handleRemove = () => {
    setFile(null);
    setPreview(null);
    setExpanded(false);
    if (fileRef.current) fileRef.current.value = "";
  };
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
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* 확대 오버레이 */}
      {expanded && preview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.85)' }}
          onClick={() => setExpanded(false)}
        >
          <img src={preview} alt="처방전 확대 보기" className="max-w-full max-h-full rounded-lg object-contain" />
          <button
            className="absolute top-4 right-4 px-4 py-2 rounded-lg text-base font-semibold"
            style={{ background: 'rgba(255,255,255,0.15)', color: '#fff' }}
            onClick={() => setExpanded(false)}
          >
            닫기
          </button>
        </div>
      )}

      {preview ? (
        <div className="mb-4">
          <div className="rounded-lg overflow-hidden" style={{ border: '2px solid var(--color-border)', maxHeight: '220px' }}>
            <img src={preview} alt="처방전 미리보기" className="w-full object-contain" style={{ maxHeight: '220px' }} />
          </div>
          <div className="flex gap-3 mt-3">
            <button
              onClick={() => setExpanded(true)}
              className="flex-1 py-3 rounded-lg text-base font-semibold btn-outline"
            >
              확대 보기
            </button>
            <button
              onClick={handleRemove}
              className="flex-1 py-3 rounded-lg text-base font-semibold text-white"
              style={{ background: 'var(--color-text-muted)' }}
            >
              다시 선택
            </button>
          </div>
        </div>
      ) : (
        <div
          className="rounded-lg p-12 text-center mb-4 cursor-pointer"
          style={{ background: 'var(--color-surface)', border: '2px dashed var(--color-border)' }}
          onClick={() => fileRef.current?.click()}
        >
          <div className="space-y-4">
            <p style={{ color: 'var(--color-text-muted)' }}>처방전 이미지를 업로드해주세요</p>
            <button
              className="px-6 py-3 rounded-lg text-white transition-colors"
              style={{ background: 'var(--color-text-muted)' }}
            >
              사진 선택
            </button>
          </div>
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
