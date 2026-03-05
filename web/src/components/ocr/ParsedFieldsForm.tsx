'use client';

import type { Medication } from '@/lib/api/types';

interface Props {
  medications: Partial<Medication>[];
  onChange: (index: number, field: keyof Medication, value: string) => void;
  onRemove: (index: number) => void;
}

const inputCls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-base focus:outline-none focus:border-blue-400';

export default function ParsedFieldsForm({ medications, onChange, onRemove }: Props) {
  return (
    <div className="flex flex-col gap-4">
      {medications.map((med, i) => (
        <div key={i} className="bg-white border-2 border-gray-200 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-lg font-bold text-gray-800">약물 {i + 1}</span>
            <button onClick={() => onRemove(i)}
              className="text-red-400 text-sm font-semibold border border-red-200 rounded-lg px-3 py-1">
              삭제
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-semibold text-gray-600 mb-1">약품명</label>
              <input value={med.drug_name ?? ''} onChange={(e) => onChange(i, 'drug_name', e.target.value)} className={inputCls} />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-600 mb-1">용량</label>
              <input value={med.dosage ?? ''} onChange={(e) => onChange(i, 'dosage', e.target.value)} className={inputCls} />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-600 mb-1">복용 횟수</label>
              <input value={med.frequency ?? ''} onChange={(e) => onChange(i, 'frequency', e.target.value)} className={inputCls} />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-600 mb-1">복용 방법</label>
              <input value={med.administration ?? ''} onChange={(e) => onChange(i, 'administration', e.target.value)} className={inputCls} />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-600 mb-1">투약 일수</label>
              <input type="number" value={med.duration_days ?? ''} onChange={(e) => onChange(i, 'duration_days', e.target.value)} className={inputCls} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
