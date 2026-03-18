const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export interface GuideItem {
  id: number;
  prescription_id: number;
  status: string;
  prescription_info: {
    hospital_name: string;
    doctor_name: string;
    prescription_date: string;
    diagnosis: string;
  };
  created_at: string;
}

export interface TodayScheduleItem {
  id: number;
  medication_id: number;
  medication_name: string;
  dosage: string | null;
  frequency: string | null;
  time_of_day: "MORNING" | "NOON" | "EVENING" | "BEDTIME";
  today_status: "TAKEN" | "MISSED" | "SKIPPED" | null;
  today_log_id: number | null;
}

interface ApiResponse<T = unknown> {
  success: boolean;
  data: T | null;
  error: string | null;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function setRefreshToken(token: string) {
  localStorage.setItem("refresh_token", token);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  if (typeof window !== "undefined") {
    sessionStorage.removeItem("activePatient");
  }
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (typeof window !== "undefined") {
    try {
      const activePatient = sessionStorage.getItem("activePatient");
      if (activePatient) {
        const { id } = JSON.parse(activePatient);
        headers["X-Acting-For"] = String(id);
      }
    } catch {
      // sessionStorage 손상 시 무시
    }
  }

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    // 대리 모드 중 403 → 매핑 해제 감지 → proxy-revoked 이벤트 발행
    if (res.status === 403 && headers["X-Acting-For"] && typeof window !== "undefined") {
      sessionStorage.removeItem("activePatient");
      window.dispatchEvent(new CustomEvent("proxy-revoked"));
    }
    try {
      const body = await res.json();
      return {
        success: false,
        data: null,
        error: body.detail || body.error || `요청에 실패했습니다. (${res.status})`,
      };
    } catch {
      return { success: false, data: null, error: `서버 오류가 발생했습니다. (${res.status})` };
    }
  }

  try {
    return await res.json();
  } catch {
    return { success: false, data: null, error: "응답을 처리할 수 없습니다." };
  }
}

export const api = {
  // Auth
  signup: (data: Record<string, unknown>) =>
    request("/api/auth/signup", { method: "POST", body: JSON.stringify(data) }),

  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () => request("/api/auth/logout", { method: "POST" }),

  // Kakao Auth
  getKakaoUrl: () =>
    request<{ url: string; state: string }>("/api/auth/kakao/url"),

  kakaoCallback: (code: string, state: string) =>
    request<{
      status: "login" | "new_user";
      access_token?: string;
      refresh_token?: string;
      token_type?: string;
      registration_token?: string;
      kakao_profile?: { email: string; nickname: string };
    }>("/api/auth/kakao/callback", {
      method: "POST",
      body: JSON.stringify({ code, state }),
    }),

  kakaoRegister: (data: {
    registration_token: string;
    email: string;
    name: string;
    nickname: string;
    role: string;
    birth_date?: string | null;
    gender?: string | null;
    phone?: string | null;
    terms_of_service: boolean;
    privacy_policy: boolean;
    marketing_consent: boolean;
  }) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>(
      "/api/auth/kakao/register",
      { method: "POST", body: JSON.stringify(data) }
    ),

  // Google Auth
  getGoogleUrl: () =>
    request<{ url: string; state: string }>("/api/auth/google/url"),

  googleCallback: (code: string, state: string) =>
    request<{
      status: "login" | "new_user";
      access_token?: string;
      refresh_token?: string;
      token_type?: string;
      registration_token?: string;
      google_profile?: { email: string; nickname: string; name: string };
    }>("/api/auth/google/callback", {
      method: "POST",
      body: JSON.stringify({ code, state }),
    }),

  googleRegister: (data: {
    registration_token: string;
    email: string;
    name: string;
    nickname: string;
    role: string;
    birth_date?: string | null;
    gender?: string | null;
    phone?: string | null;
    terms_of_service: boolean;
    privacy_policy: boolean;
    marketing_consent: boolean;
  }) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>(
      "/api/auth/google/register",
      { method: "POST", body: JSON.stringify(data) }
    ),

  // User
  getMe: () => request("/api/users/me"),
  updateMe: (data: Record<string, unknown>) =>
    request("/api/users/me", { method: "PATCH", body: JSON.stringify(data) }),
  deleteMe: (data: { password?: string; confirm_email?: string }) =>
    request("/api/users/me", { method: "DELETE", body: JSON.stringify(data) }),

  // Prescriptions
  uploadPrescription: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request("/api/prescriptions", { method: "POST", body: formData });
  },

  listPrescriptions: () => request("/api/prescriptions"),

  getPrescription: (id: number) => request(`/api/prescriptions/${id}`),

  // OCR
  getOcr: (prescriptionId: number) =>
    request(`/api/prescriptions/${prescriptionId}/ocr`),

  updateOcr: (prescriptionId: number, data: object) =>
    request(`/api/prescriptions/${prescriptionId}/ocr`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // Guides
  createGuide: (prescriptionId: number, force = false) =>
    request("/api/guides", {
      method: "POST",
      body: JSON.stringify({ prescription_id: prescriptionId, force }),
    }),

  listGuides: () => request<GuideItem[]>("/api/guides"),

  getGuide: (guideId: number) => request(`/api/guides/${guideId}`),

  deleteGuide: (guideId: number) =>
    request(`/api/guides/${guideId}`, { method: "DELETE" }),

  // Schedules
  listTodaySchedules: () =>
    request<TodayScheduleItem[]>("/api/schedules/today"),

  logAdherence: (scheduleId: number, status: "TAKEN" | "MISSED" | "SKIPPED") =>
    request(`/api/schedules/${scheduleId}/log`, {
      method: "POST",
      body: JSON.stringify({
        target_date: new Date().toISOString().split("T")[0],
        status,
      }),
    }),

  // Medications
  getMedication: (id: number) => request(`/api/medications/${id}`),

  listMedications: (prescriptionId: number) =>
    request(`/api/prescriptions/${prescriptionId}/medications`),

  // Caregivers
  createInvite: () =>
    request<{ token: string; invite_url: string }>("/api/caregivers/invite", { method: "POST" }),

  validateInvite: (token: string) =>
    request<{ inviter_name: string; inviter_nickname: string; inviter_role: string }>(
      `/api/caregivers/invite/${token}`
    ),

  acceptInvite: (token: string) =>
    request<{ id: number; status: string }>(`/api/caregivers/invite/${token}/accept`, { method: "POST" }),

  listPatients: () =>
    request<{ mapping_id: number; id: number; nickname: string; name: string }[]>("/api/caregivers/patients"),

  listMyCaregivers: () =>
    request<{ mapping_id: number; id: number; nickname: string; name: string }[]>("/api/caregivers/my-caregivers"),

  revokeMapping: (mappingId: number) =>
    request(`/api/caregivers/${mappingId}`, { method: "DELETE" }),

  // Chat
  createThread: (prescriptionId?: number) =>
    request("/api/chat/threads", {
      method: "POST",
      body: JSON.stringify({ prescription_id: prescriptionId ?? null }),
    }),

  listThreads: (page = 1, pageSize = 10, status = "all") =>
    request(`/api/chat/threads?page=${page}&page_size=${pageSize}&status=${status}`),

  getThread: (threadId: number) =>
    request(`/api/chat/threads/${threadId}`),

  reactivateThread: (threadId: number) =>
    request(`/api/chat/threads/${threadId}/reactivate`, { method: "PATCH" }),

  getMessages: (threadId: number) =>
    request(`/api/chat/threads/${threadId}/messages`),

  endThread: (threadId: number) =>
    request(`/api/chat/threads/${threadId}/end`, { method: "PATCH" }),

  sendFeedback: (data: {
    thread_id?: number;
    message_id?: number;
    feedback_type: string;
    reason?: string;
    reason_text?: string;
  }) =>
    request("/api/chat/feedback", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Notifications
  getNotificationSettings: () =>
    request("/api/notifications/settings"),

  updateNotificationSettings: (data: Record<string, unknown>) =>
    request("/api/notifications/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  listNotifications: (isRead?: boolean) => {
    const params = isRead !== undefined ? `?is_read=${isRead}` : "";
    return request(`/api/notifications${params}`);
  },

  getUnreadCount: () =>
    request<{ count: number }>("/api/notifications/unread-count"),

  markNotificationRead: (id: number) =>
    request(`/api/notifications/${id}/read`, { method: "PATCH" }),

  readAllNotifications: () =>
    request("/api/notifications/read-all", { method: "POST" }),
};

export function subscribeNotifications(
  onCount: (count: number) => void,
  onError: (message: string) => void,
): AbortController {
  const controller = new AbortController();

  const connect = async () => {
    const token = getToken();
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/api/notifications/stream`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        onError(`SSE 연결 실패 (${res.status})`);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "unread_count") {
              onCount(event.count);
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      onError("SSE 연결이 끊어졌습니다.");
    }

    // 자동 재연결 (5초 후, abort되지 않은 경우만)
    if (!controller.signal.aborted) {
      setTimeout(connect, 5000);
    }
  };

  connect();
  return controller;
}

export async function streamChat(
  threadId: number,
  content: string,
  onChunk: (text: string) => void,
  onDone: (messageId: number) => void,
  onError: (message: string) => void,
) {
  const token = getToken();
  const streamHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  if (typeof window !== "undefined") {
    try {
      const ap = sessionStorage.getItem("activePatient");
      if (ap) {
        const { id } = JSON.parse(ap);
        streamHeaders["X-Acting-For"] = String(id);
      }
    } catch {
      // sessionStorage 손상 시 무시
    }
  }
  const res = await fetch(`${API_BASE}/api/chat/messages`, {
    method: "POST",
    headers: streamHeaders,
    body: JSON.stringify({ thread_id: threadId, content }),
  });

  if (!res.ok || !res.body) {
    let errorMsg = `서버 연결에 실패했습니다. (${res.status})`;
    try {
      const body = await res.json();
      errorMsg = body.detail || body.error || errorMsg;
    } catch {
      // non-JSON response
    }
    onError(errorMsg);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const jsonStr = line.slice(6);
      try {
        const event = JSON.parse(jsonStr);
        if (event.type === "chunk") {
          onChunk(event.content);
        } else if (event.type === "done") {
          onDone(event.message_id);
        } else if (event.type === "error") {
          onError(event.message);
        }
      } catch {
        // ignore parse errors
      }
    }
  }
}
