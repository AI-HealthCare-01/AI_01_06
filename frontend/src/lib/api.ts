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

  getGuide: (guideId: number) => request(`/api/guides/${guideId}`),

  // Medications
  getMedication: (id: number) => request(`/api/medications/${id}`),

  listMedications: (prescriptionId: number) =>
    request(`/api/prescriptions/${prescriptionId}/medications`),
};
