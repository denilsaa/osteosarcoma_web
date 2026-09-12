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
// CATÁLOGOS CLÍNICOS
// ==========================================================

export interface ClinicalCatalogItem {
  id: number;

  code: string;

  name: string;

  description?:
    string | null;
}


export interface ClinicalIntensityLevel {
  id: number;

  code: string;

  name: string;

  level: number;
}


export interface ClinicalCaseCatalogs {
  statuses:
    ClinicalCaseStatus[];

  priorities:
    ClinicalCasePriority[];

  antecedent_types:
    ClinicalCatalogItem[];

  symptoms:
    ClinicalCatalogItem[];

  intensity_levels:
    ClinicalIntensityLevel[];

  signs:
    ClinicalCatalogItem[];
}


interface ClinicalCaseCatalogsResponse {
  data:
    ClinicalCaseCatalogs;
}


// ==========================================================
// ANTECEDENTES
// ==========================================================

export interface ClinicalAntecedent {
  id_antecedent:
    string;

  type: {
    id:
      number;

    code:
      string;

    name:
      string;
  };

  description:
    string;

  author_uuid:
    string | null;

  registered_at:
    string;

  active:
    boolean;
}


export interface ClinicalAntecedentListResponse {
  data:
    ClinicalAntecedent[];

  total:
    number;
}


export interface CreateClinicalAntecedentRequest {
  antecedent_type_id:
    number;

  description:
    string;
}


// ==========================================================
// SÍNTOMAS
// ==========================================================

export interface ClinicalSymptom {
  id_case_symptom:
    string;

  symptom: {
    id:
      number;

    code:
      string;

    name:
      string;
  };

  intensity:
    {
      id:
        number;

      code:
        string;

      name:
        string;

      level:
        number;
    }
    | null;

  start_date:
    string | null;

  observation:
    string | null;

  author_uuid:
    string | null;

  registered_at:
    string;
}


export interface ClinicalSymptomListResponse {
  data:
    ClinicalSymptom[];

  total:
    number;
}


export interface CreateClinicalSymptomRequest {
  symptom_id:
    number;

  intensity_id?:
    number | null;

  start_date?:
    string | null;

  observation?:
    string | null;
}


// ==========================================================
// SIGNOS
// ==========================================================

export interface ClinicalSign {
  id_case_sign:
    string;

  sign: {
    id:
      number;

    code:
      string;

    name:
      string;
  };

  finding_description:
    string | null;

  author_uuid:
    string;

  observed_at:
    string;
}


export interface ClinicalSignListResponse {
  data:
    ClinicalSign[];

  total:
    number;
}


export interface CreateClinicalSignRequest {
  sign_id:
    number;

  finding_description?:
    string | null;
}


// ==========================================================
// OBSERVACIONES
// ==========================================================

export interface ClinicalObservation {
  id_observation:
    string;

  content:
    string;

  author_uuid:
    string;

  registered_at:
    string;

  active:
    boolean;
}


export interface ClinicalObservationListResponse {
  data:
    ClinicalObservation[];

  total:
    number;
}


export interface CreateClinicalObservationRequest {
  content:
    string;
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
// CREAR CASO
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


// ==========================================================
// ANTECEDENTES
// ==========================================================

export async function getClinicalAntecedents(
  caseId:
    string,
): Promise<ClinicalAntecedentListResponse> {

  const response =
    await apiClinico
      .get<ClinicalAntecedentListResponse>(
        `/casos/${caseId}/antecedentes/`,
      );


  return response.data;
}


export async function createClinicalAntecedent(
  caseId:
    string,

  data:
    CreateClinicalAntecedentRequest,
): Promise<ClinicalAntecedent> {

  const response =
    await apiClinico
      .post<{
        message:
          string;

        data:
          ClinicalAntecedent;
      }>(
        `/casos/${caseId}/antecedentes/`,
        data,
      );


  return response.data.data;
}


// ==========================================================
// SÍNTOMAS
// ==========================================================

export async function getClinicalSymptoms(
  caseId:
    string,
): Promise<ClinicalSymptomListResponse> {

  const response =
    await apiClinico
      .get<ClinicalSymptomListResponse>(
        `/casos/${caseId}/sintomas/`,
      );


  return response.data;
}


export async function createClinicalSymptom(
  caseId:
    string,

  data:
    CreateClinicalSymptomRequest,
): Promise<ClinicalSymptom> {

  const response =
    await apiClinico
      .post<{
        message:
          string;

        data:
          ClinicalSymptom;
      }>(
        `/casos/${caseId}/sintomas/`,
        data,
      );


  return response.data.data;
}


// ==========================================================
// SIGNOS
// ==========================================================

export async function getClinicalSigns(
  caseId:
    string,
): Promise<ClinicalSignListResponse> {

  const response =
    await apiClinico
      .get<ClinicalSignListResponse>(
        `/casos/${caseId}/signos/`,
      );


  return response.data;
}


export async function createClinicalSign(
  caseId:
    string,

  data:
    CreateClinicalSignRequest,
): Promise<ClinicalSign> {

  const response =
    await apiClinico
      .post<{
        message:
          string;

        data:
          ClinicalSign;
      }>(
        `/casos/${caseId}/signos/`,
        data,
      );


  return response.data.data;
}


// ==========================================================
// OBSERVACIONES
// ==========================================================

export async function getClinicalObservations(
  caseId:
    string,
): Promise<ClinicalObservationListResponse> {

  const response =
    await apiClinico
      .get<ClinicalObservationListResponse>(
        `/casos/${caseId}/observaciones/`,
      );


  return response.data;
}


export async function createClinicalObservation(
  caseId:
    string,

  data:
    CreateClinicalObservationRequest,
): Promise<ClinicalObservation> {

  const response =
    await apiClinico
      .post<{
        message:
          string;

        data:
          ClinicalObservation;
      }>(
        `/casos/${caseId}/observaciones/`,
        data,
      );


  return response.data.data;
}