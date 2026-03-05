const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export const ENDPOINTS = {
  // Auth
  LOGIN: `${BASE_URL}/api/v1/auth/login`,
  SIGNUP: `${BASE_URL}/api/v1/auth/signup`,
  LOGOUT: `${BASE_URL}/api/v1/auth/logout`,
  SOCIAL_LOGIN: (provider: string) => `${BASE_URL}/api/v1/auth/social/${provider}`,

  // Users
  ME: `${BASE_URL}/api/v1/users/me`,
  PATIENT_PROFILE: `${BASE_URL}/api/v1/users/me/profile`,
  CAREGIVER_PATIENTS: `${BASE_URL}/api/v1/users/me/patients`,
  SEARCH_PATIENT: `${BASE_URL}/api/v1/users/search`,
  CAREGIVER_REQUEST: `${BASE_URL}/api/v1/users/caregiver/request`,

  // Prescriptions
  PRESCRIPTIONS: `${BASE_URL}/api/v1/prescriptions`,
  PRESCRIPTION: (id: string) => `${BASE_URL}/api/v1/prescriptions/${id}`,
  PRESCRIPTION_OCR: (id: string) => `${BASE_URL}/api/v1/prescriptions/${id}/ocr`,
  PRESCRIPTION_CONFIRM: (id: string) => `${BASE_URL}/api/v1/prescriptions/${id}/confirm`,

  // Medications
  MEDICATIONS: (prescriptionId: string) => `${BASE_URL}/api/v1/prescriptions/${prescriptionId}/medications`,

  // Guide
  GUIDE: (prescriptionId: string) => `${BASE_URL}/api/v1/prescriptions/${prescriptionId}/guide`,

  // Chat
  CHAT_SESSION: (prescriptionId: string) => `${BASE_URL}/api/v1/prescriptions/${prescriptionId}/chat`,
  CHAT_STREAM: (sessionId: string) => `${BASE_URL}/api/v1/chat/${sessionId}/stream`,

  // Notifications
  NOTIFICATIONS: `${BASE_URL}/api/v1/notifications`,
  NOTIFICATION_READ: (id: string) => `${BASE_URL}/api/v1/notifications/${id}/read`,

  // LLM
  LLM_PING: `${BASE_URL}/api/v1/llm/ping`,
} as const;
