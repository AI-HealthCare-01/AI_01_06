'use client';

import { useRef, useState } from 'react';

interface Props {
  onUpload: (file: File) => void;
  loading?: boolean;
}

export default function UploadForm({ onUpload, loading }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFile = (f: File) => {
    setPreview(URL.createObjectURL(f));
    onUpload(f);
  };

  return (
    <div className="flex flex-col gap-4">
      <div
        onClick={() => fileRef.current?.click()}
        onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 rounded-2xl p-8 flex flex-col items-center gap-3 cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors min-h-48"
      >
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={preview} alt="미리보기" className="max-h-48 rounded-xl object-contain" />
        ) : (
          <>
            <span className="text-5xl">📄</span>
            <p className="text-xl font-semibold text-gray-700">처방전 사진을 선택하세요</p>
            <p className="text-gray-400 text-sm">JPG, PNG, PDF 지원</p>
          </>
        )}
      </div>
      <input ref={fileRef} type="file" accept="image/*,.pdf" capture="environment" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
      {loading && <p className="text-center text-blue-500 text-lg font-semibold">OCR 분석 중...</p>}
    </div>
  );
}
