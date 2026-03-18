"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api, clearTokens, isLoggedIn, setRefreshToken, setToken } from "./api";

export interface User {
  id: number;
  email: string;
  nickname: string;
  name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User | string>;
  logout: () => void;
  refreshUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async (): Promise<User | null> => {
    if (!isLoggedIn()) {
      setUser(null);
      setLoading(false);
      return null;
    }
    const res = await api.getMe();
    if (res.success && res.data) {
      const u = res.data as User;
      setUser(u);
      setLoading(false);
      return u;
    }
    clearTokens();
    setUser(null);
    setLoading(false);
    return null;
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string): Promise<User | string> => {
    const res = await api.login(email, password);
    if (res.success && res.data) {
      setToken(res.data.access_token);
      setRefreshToken(res.data.refresh_token);
      const u = await refreshUser();
      if (u) return u;
      return "사용자 정보를 불러올 수 없습니다.";
    }
    return res.error || "로그인에 실패했습니다.";
  };

  const logout = () => {
    api.logout();
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
