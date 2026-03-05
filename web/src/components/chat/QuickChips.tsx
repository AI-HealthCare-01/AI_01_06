'use client';

const CHIPS = [
  '이 약 부작용이 뭔가요?',
  '식전에 먹어야 하나요?',
  '다른 약과 같이 먹어도 되나요?',
  '술을 마셔도 되나요?',
  '약을 빠뜨렸을 때 어떻게 하나요?',
];

interface Props {
  onSelect: (text: string) => void;
  disabled?: boolean;
}

export default function QuickChips({ onSelect, disabled }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 px-4 scrollbar-hide">
      {CHIPS.map((chip) => (
        <button
          key={chip}
          onClick={() => onSelect(chip)}
          disabled={disabled}
          className="shrink-0 border-2 border-gray-300 rounded-full px-4 py-2 text-base font-medium text-gray-700 bg-white hover:border-blue-400 hover:bg-blue-50 transition-colors disabled:opacity-40 whitespace-nowrap"
        >
          {chip}
        </button>
      ))}
    </div>
  );
}
