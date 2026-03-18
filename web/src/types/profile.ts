export interface PatientProfile {
  height_cm: number | null;
  weight_kg: number | null;
  has_allergy: boolean;
  allergy_details: string | null;
  has_disease: boolean;
  disease_details: string | null;
}
