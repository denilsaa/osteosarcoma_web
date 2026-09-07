import {
  apiClinico,
} from "./axios";


// ==========================================================
// ESTADO DEL CASO
// ==========================================================

export interface ClinicalCaseStatus {
  id: number;
  code: string;
  name: string;
}


// ==========================================================
// PRIORIDAD DEL CASO
// ==========================================================

export interface ClinicalCasePriority {
  id: number;
  code: string;
  name: string;
  level: number;
}


// ==========================================================
// CASO CLÍNICO
// ==========================================================

export interface ClinicalCase {
  id_case: string;

  patient_id: string;

  code: string;

  status: ClinicalCaseStatus;

  priority: ClinicalCasePriority;

  responsible_oncologist_uuid:
    string | null;

  opening_date:
    string;

  closing_date:
    string | null;

  consultation_reason:
    string;

  general_observation:
    string | null;
}


// ==========================================================
// RESPUESTA
// ==========================================================

export interface PatientClinicalCasesResponse {
  data: ClinicalCase[];
  total: number;
}


// ==========================================================
// OBTENER CASOS DE UN PACIENTE
// ==========================================================

export async function getPatientClinicalCases(
  patientId: string,
): Promise<PatientClinicalCasesResponse> {

  const response =
    await apiClinico
      .get<PatientClinicalCasesResponse>(
        `/pacientes/${patientId}/casos/`,
      );


  return response.data;
}