export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T | null;
  error: { message: string; code?: string } | null;
}

export interface User {
  id: string;
  email: string;
  name: string;
  nickname: string;
  role: 'PATIENT' | 'GUARDIAN';
  gender: 'M' | 'F';
  birthdate: string;
  phone_number?: string;
}

export interface PatientProfile {
  user_id: string;
  height_cm?: number;
  weight_kg?: number;
  has_allergies: boolean;
  allergy_details?: string;
  has_diseases: boolean;
  disease_details?: string;
}

export interface Prescription {
  id: string;
  patient_id: string;
  hospital_name?: string;
  doctor_name?: string;
  prescription_date?: string;
  diagnosis?: string;
  verification_status: 'DRAFT' | 'CONFIRMED';
  created_at: string;
}

export interface Medication {
  id: string;
  prescription_id: string;
  drug_name: string;
  dosage?: string;
  frequency?: string;
  administration?: string;
  duration_days?: number;
}

export interface MedicationGuide {
  id: string;
  prescription_id: string;
  guide_markdown: string;
  precautions?: string;
  lifestyle_advice?: string;
  generated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  sender_type: 'USER' | 'AI';
  message_text: string;
  created_at: string;
}

export interface Notification {
  id: string;
  type: string;
  title?: string;
  body?: string;
  is_read: boolean;
  created_at: string;
}

export interface MedicationSchedule {
  id: string;
  medication_id: string;
  time_of_day: 'MORNING' | 'NOON' | 'EVENING' | 'BEDTIME';
  specific_time?: string;
  start_date?: string;
  end_date?: string;
}
