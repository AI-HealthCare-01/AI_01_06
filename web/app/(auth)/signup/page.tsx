import Link from 'next/link';

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl border-2 border-gray-200 p-8 shadow-sm">
        <Link href="/" className="block text-center text-3xl font-extrabold mb-8" style={{ color: '#4a90e2' }}>
          설리반
        </Link>

        <h1 className="text-2xl font-bold text-gray-900 mb-2 text-center">회원가입</h1>
        <p className="text-center text-gray-500 text-lg mb-8">어떤 목적으로 이용하시나요?</p>

        <div className="flex flex-col gap-5">
          <Link
            href="/signup/patient"
            className="flex flex-col items-center gap-2 border-2 border-gray-200 rounded-2xl p-8 hover:border-blue-400 hover:bg-blue-50 transition-colors"
          >
            <span className="text-5xl">🧑‍⚕️</span>
            <span className="text-2xl font-bold text-gray-900">환자</span>
            <span className="text-gray-500 text-base text-center">
              처방전을 등록하고 복약 가이드를 받고 싶어요
            </span>
          </Link>

          <Link
            href="/signup/caregiver"
            className="flex flex-col items-center gap-2 border-2 border-gray-200 rounded-2xl p-8 hover:border-blue-400 hover:bg-blue-50 transition-colors"
          >
            <span className="text-5xl">👨‍👩‍👧</span>
            <span className="text-2xl font-bold text-gray-900">보호자</span>
            <span className="text-gray-500 text-base text-center">
              가족의 복약 상태를 관리하고 싶어요
            </span>
          </Link>
        </div>

        <div className="mt-6 text-center text-lg text-gray-500">
          이미 계정이 있으신가요?{' '}
          <Link href="/login" className="font-bold" style={{ color: '#4a90e2' }}>
            로그인
          </Link>
        </div>
      </div>
    </div>
  );
}
