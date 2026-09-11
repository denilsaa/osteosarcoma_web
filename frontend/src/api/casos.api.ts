import {
  apiClinico,
} from "./axios";


// ==========================================================
// ESTADO
// ==========================================================

export interface ClinicalCaseStatus {
  id: number;

  code: string;

  name: string;
}


// ==========================================================
// PRIORIDAD
// ==========================================================

export interface ClinicalCasePriority {
  id: number;

  code: string;

  name: string;

  level: number;
}


// ==========================================================
// CASO
// ==========================================================

export interface ClinicalCase {
  id_case: string;

  patient_id: string;

  patient_name:
    string | null;

  code: string;

  status:
    ClinicalCaseStatus;

  priority:
    ClinicalCasePriority;

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
// PAGINACIÓN
// ==========================================================

export interface ClinicalCasePagination {
  page: number;

  page_size: number;

  total: number;

  total_pages: number;
}


// ==========================================================
// LISTADO
// ==========================================================

export interface ClinicalCaseListResponse {
  data:
    ClinicalCase[];

  pagination:
    ClinicalCasePagination;
}


// ==========================================================
// CASOS DEL PACIENTE
// ==========================================================

export interface PatientClinicalCasesResponse {
  data:
    ClinicalCase[];

  total:
    number;
}


// ==========================================================
// CATÁLOGOS
// ==========================================================

export interface ClinicalCaseCatalogs {
  statuses:
    ClinicalCaseStatus[];

  priorities:
    ClinicalCasePriority[];
}


interface ClinicalCaseCatalogsResponse {
  data:
    ClinicalCaseCatalogs;
}


// ==========================================================
// FILTROS
// ==========================================================

export interface ClinicalCaseFilters {
  search?:
    string;

  status_code?:
    string;

  priority_code?:
    string;

  patient_id?:
    string;

  responsible_oncologist_uuid?:
    string;

  opening_date?:
    string;

  page?:
    number;

  page_size?:
    number;
}


// ==========================================================
// CREAR
// ==========================================================

export interface CreateClinicalCaseRequest {
  priority_id:
    number;

  responsible_oncologist_uuid?:
    string | null;

  consultation_reason:
    string;

  general_observation?:
    string | null;
}


export interface CreateClinicalCaseResponse {
  message:
    string;

  data:
    ClinicalCase;
}


// ==========================================================
// CATÁLOGOS
// ==========================================================

export async function getClinicalCaseCatalogs():
  Promise<ClinicalCaseCatalogs> {

  const response =
    await apiClinico
      .get<ClinicalCaseCatalogsResponse>(
        "/casos/catalogos/",
      );


  return response.data.data;
}


// ==========================================================
// LISTADO GENERAL
// ==========================================================

export async function listClinicalCases(
  filters:
    ClinicalCaseFilters = {},
): Promise<ClinicalCaseListResponse> {

  const params:
    Record<
      string,
      string | number
    > = {};


  if (
    filters.search
      ?.trim()
  ) {

    params.search =
      filters.search.trim();

  }


  if (
    filters.status_code
  ) {

    params.status_code =
      filters.status_code;

  }


  if (
    filters.priority_code
  ) {

    params.priority_code =
      filters.priority_code;

  }


  if (
    filters.patient_id
  ) {

    params.patient_id =
      filters.patient_id;

  }


  if (
    filters.responsible_oncologist_uuid
  ) {

    params.responsible_oncologist_uuid =
      filters.responsible_oncologist_uuid;

  }


  if (
    filters.opening_date
  ) {

    params.opening_date =
      filters.opening_date;

  }


  params.page =
    filters.page
    ??
    1;


  params.page_size =
    filters.page_size
    ??
    10;


  const response =
    await apiClinico
      .get<ClinicalCaseListResponse>(
        "/casos/",
        {
          params,
        },
      );


  return response.data;
}


// ==========================================================
// DETALLE
// ==========================================================

export async function getClinicalCase(
  caseId:
    string,
): Promise<ClinicalCase> {

  const response =
    await apiClinico
      .get<{
        data:
          ClinicalCase;
      }>(
        `/casos/${caseId}/`,
      );


  return response.data.data;
}


// ==========================================================
// CASOS DE PACIENTE
// ==========================================================

export async function getPatientClinicalCases(
  patientId:
    string,
): Promise<PatientClinicalCasesResponse> {

  const response =
    await apiClinico
      .get<PatientClinicalCasesResponse>(
        `/pacientes/${patientId}/casos/`,
      );


  return response.data;
}


// ==========================================================
// CREAR CASO PARA PACIENTE
// ==========================================================

export async function createClinicalCase(
  patientId:
    string,

  data:
    CreateClinicalCaseRequest,
): Promise<CreateClinicalCaseResponse> {

  const response =
    await apiClinico
      .post<CreateClinicalCaseResponse>(
        `/pacientes/${patientId}/casos/`,
        data,
      );


  return response.data;
}