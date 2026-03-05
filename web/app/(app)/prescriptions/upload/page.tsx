'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api/client';
import { ENDPOINTS } from '@/lib/api/endpoints';
import ErrorBox from '@/components/common/ErrorBox';

export default function PrescriptionUploadPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleSubmit = async () => {
    if (!file) { setError('처방전 이미지를 선택해 주세요.'); return; }
    setLoading(true);
    setError(null);
    try {
      // TODO: API 연동 - 처방전 생성 후 OCR 처리
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.postForm<{ id: string }>(ENDPOINTS.PRESCRIPTIONS, formData);
      if (res.success && res.data) {
        router.push(`/prescriptions/${res.data.id}/ocr`);
      } else {
        setError(res.error?.message ?? '업로드에 실패했습니다.');
      }
    } catch {
      setError('업로드 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-screen-sm mx-auto px-4 py-8">
      <h1 className="text-3xl font-extrabold text-gray-900 mb-2">처방전 업로드</h1>
      <p className="text-gray-500 text-lg mb-8">처방전 사진을 업로드하면 AI가 복약 가이드를 만들어 드립니다.</p>

      {error && <div className="mb-4"><ErrorBox message={error} /></div>}

      {/* 업로드 영역 */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => fileRef.current?.click()}
        className="border-2 border-dashed border-gray-300 rounded-2xl p-8 flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors min-h-64"
      >
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={preview} alt="처방전 미리보기" className="max-h-64 rounded-xl object-contain" />
        ) : (
          <>
            <span className="text-6xl">📄</span>
            <p className="text-xl font-semibold text-gray-700">여기를 눌러 사진을 선택하세요</p>
            <p className="text-gray-400 text-base">또는 사진을 이 영역으로 끌어다 놓으세요</p>
            <p className="text-gray-400 text-sm">JPG, PNG, PDF 지원</p>
          </>
        )}
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*,.pdf"
        capture="environment"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />

      {/* 카메라 촬영 버튼 */}
      <div className="flex gap-3 mt-4">
        <button
          onClick={() => { if (fileRef.current) { fileRef.current.accept = 'image/*'; fileRef.current.capture = 'environment'; fileRef.current.click(); } }}
          className="flex-1 py-4 rounded-xl border-2 border-gray-300 text-lg font-semibold text-gray-700 flex items-center justify-center gap-2"
        >
          📷 카메라 촬영
        </button>
        <button
          onClick={() => { if (fileRef.current) { fileRef.current.removeAttribute('capture'); fileRef.current.click(); } }}
          className="flex-1 py-4 rounded-xl border-2 border-gray-300 text-lg font-semibold text-gray-700 flex items-center justify-center gap-2"
        >
          🖼️ 파일 선택
        </button>
      </div>

      {preview && (
        <button
          onClick={() => { setPreview(null); setFile(null); }}
          className="w-full mt-3 py-3 rounded-xl border-2 border-red-200 text-red-500 text-base font-semibold"
        >
          다시 선택
        </button>
      )}

      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className="w-full mt-6 py-5 rounded-xl text-xl font-bold text-white disabled:opacity-40"
        style={{ backgroundColor: '#4a90e2' }}
      >
        {loading ? 'AI 분석 중...' : 'AI 복약 가이드 생성하기'}
      </button>

      <p className="text-center text-gray-400 text-sm mt-4">
        처방전 이미지는 복약 가이드 생성 목적으로만 사용됩니다.
      </p>
    </div>
  );
}
