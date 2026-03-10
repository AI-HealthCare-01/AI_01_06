const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

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

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  return res.json();
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

  // User
  getMe: () => request("/api/users/me"),
  updateMe: (data: Record<string, unknown>) =>
    request("/api/users/me", { method: "PATCH", body: JSON.stringify(data) }),

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
  createGuide: (prescriptionId: number) =>
    request("/api/guides", {
      method: "POST",
      body: JSON.stringify({ prescription_id: prescriptionId }),
    }),

  listGuides: () => request("/api/guides"),

  getGuide: (guideId: number) => request(`/api/guides/${guideId}`),

  // Medications
  getMedication: (id: number) => request(`/api/medications/${id}`),

  listMedications: (prescriptionId: number) =>
    request(`/api/prescriptions/${prescriptionId}/medications`),

  // Chat
  createThread: (prescriptionId?: number) =>
    request("/api/chat/threads", {
      method: "POST",
      body: JSON.stringify({ prescription_id: prescriptionId ?? null }),
    }),

  listThreads: () => request("/api/chat/threads"),

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
};

export async function streamChat(
  threadId: number,
  content: string,
  onChunk: (text: string) => void,
  onDone: (messageId: number) => void,
  onError: (message: string) => void,
) {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/chat/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ thread_id: threadId, content }),
  });

  if (!res.ok || !res.body) {
    onError("서버 연결에 실패했습니다.");
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
