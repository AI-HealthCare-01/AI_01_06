'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import { saveToken, removeToken } from '../auth/token';

export function useAuth() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      // TODO: API 연동
      const res = await apiClient.post<{ access_token: string }>(ENDPOINTS.LOGIN, { email, password });
      if (res.success && res.data) {
        saveToken(res.data.access_token);
        router.push('/dashboard');
      } else {
        setError(res.error?.message ?? '로그인에 실패했습니다.');
      }
    } catch {
      setError('로그인 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    removeToken();
    router.push('/login');
  };

  return { login, logout, loading, error };
}
