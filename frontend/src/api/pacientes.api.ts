import {
  apiClinico,
} from "./axios";


// ==========================================================
// CATÁLOGOS
// ==========================================================

export interface CatalogItem {

  id: number;

  code: string;

  name: string;

}


export interface PatientCatalogs {

  sexes:
    CatalogItem[];

  document_types:
    CatalogItem[];

  contact_types:
    CatalogItem[];

}


interface PatientCatalogsResponse {

  data:
    PatientCatalogs;

}


// ==========================================================
// DOCUMENTO
// ==========================================================

export interface PatientDocument {

  id_document:
    string | null;

  document_type_id:
    number;

  document_type_code:
    string;

  document_type_name:
    string;

  document_number:
    string;

  complement:
    string | null;

  issued_in:
    string | null;

}


// ==========================================================
// CONTACTO
// ==========================================================

export interface PatientContact {

  id_contact:
    string | null;

  contact_type_id:
    number;

  contact_type_code:
    string;

  contact_type_name:
    string;

  value:
    string;

  primary:
    boolean;

}


// ==========================================================
// SEXO
// ==========================================================

export interface PatientSex {

  id?: number;

  code: string;

  name: string;

}


// ==========================================================
// PACIENTE RESUMEN
// ==========================================================

export interface PatientSummary {

  id_patient:
    string;

  full_name:
    string;

  birth_date:
    string;

  sex:
    PatientSex;

  active:
    boolean;

  primary_document:
    PatientDocument | null;

  primary_contact:
    PatientContact | null;

  clinical_cases_count:
    number;

  registration_date:
    string | null;

}


// ==========================================================
// PACIENTE DETALLE
// ==========================================================

export interface PatientDetail {

  id_patient:
    string;

  first_names:
    string;

  paternal_surname:
    string;

  maternal_surname:
    string | null;

  full_name:
    string;

  birth_date:
    string;

  sex:
    PatientSex;

  active:
    boolean;

  registration_date:
    string | null;

  documents:
    PatientDocument[];

  contacts:
    PatientContact[];

  clinical_cases_count:
    number;

}


// ==========================================================
// PAGINACIÓN
// ==========================================================

export interface PatientPagination {

  page:
    number;

  page_size:
    number;

  total:
    number;

  total_pages:
    number;

}


export interface PatientListResponse {

  data:
    PatientSummary[];

  pagination:
    PatientPagination;

}


// ==========================================================
// FILTROS
// ==========================================================

export interface PatientFilters {

  search?: string;

  sex_code?: string;

  active?: boolean;

  document_type_code?: string;

  page?: number;

  page_size?: number;

}


// ==========================================================
// REGISTRO
// ==========================================================

export interface CreatePatientRequest {

  first_names:
    string;

  paternal_surname:
    string;

  maternal_surname?:
    string | null;

  birth_date:
    string;

  sex_id:
    number;

  document_type_id:
    number;

  document_number:
    string;

  complement?:
    string | null;

  issued_in?:
    string | null;

  contact_type_id?:
    number | null;

  contact_value?:
    string | null;

}


export interface CreatePatientResponse {

  message:
    string;

  data:
    PatientDetail;

}


// ==========================================================
// EDICIÓN
// ==========================================================

export interface UpdatePatientRequest {

  first_names?:
    string;

  paternal_surname?:
    string;

  maternal_surname?:
    string | null;

  birth_date?:
    string;

  sex_id?:
    number;

  active?:
    boolean;

  reason:
    string;

}


export interface PatientChange {

  field:
    string;

  old_value:
    string | null;

  new_value:
    string | null;

}


export interface UpdatePatientResponse {

  message:
    string;

  data:
    PatientDetail;

  changes:
    PatientChange[];

  reason:
    string;

}


// ==========================================================
// DUPLICADOS
// ==========================================================

export interface PossibleDuplicateFilters {

  document_type_id?:
    number;

  document_number?:
    string;

  first_names?:
    string;

  paternal_surname?:
    string;

  maternal_surname?:
    string;

  birth_date?:
    string;

}


export interface PossibleDuplicateResponse {

  data:
    PatientSummary[];

  meta: {

    has_possible_duplicates:
      boolean;

    total:
      number;

  };

}


// ==========================================================
// OBTENER CATÁLOGOS
// ==========================================================

export async function getPatientCatalogs():
  Promise<PatientCatalogs> {

  const response =
    await apiClinico
      .get<PatientCatalogsResponse>(
        "/pacientes/catalogos/",
      );


  return response.data.data;

}


// ==========================================================
// LISTAR PACIENTES
// ==========================================================

export async function listPatients(
  filters:
    PatientFilters = {},
): Promise<PatientListResponse> {

  const params:
    Record<
      string,
      string | number | boolean
    > = {};


  if (
    filters.search
      ?.trim()
  ) {

    params.search =
      filters.search.trim();

  }


  if (
    filters.sex_code
  ) {

    params.sex_code =
      filters.sex_code;

  }


  if (
    filters.active !==
      undefined
  ) {

    params.active =
      filters.active;

  }


  if (
    filters
      .document_type_code
  ) {

    params
      .document_type_code =
        filters
          .document_type_code;

  }


  params.page =
    filters.page ?? 1;


  params.page_size =
    filters.page_size ?? 10;


  const response =
    await apiClinico
      .get<PatientListResponse>(
        "/pacientes/",
        {
          params,
        },
      );


  return response.data;

}


// ==========================================================
// OBTENER PACIENTE
// ==========================================================

export async function getPatient(
  idPatient: string,
): Promise<PatientDetail> {

  const response =
    await apiClinico
      .get<{
        data: PatientDetail;
      }>(
        `/pacientes/${idPatient}/`,
      );


  return response.data.data;

}


// ==========================================================
// REGISTRAR PACIENTE
// ==========================================================

export async function createPatient(
  data:
    CreatePatientRequest,
): Promise<CreatePatientResponse> {

  const response =
    await apiClinico
      .post<CreatePatientResponse>(
        "/pacientes/registrar/",
        data,
      );


  return response.data;

}


// ==========================================================
// EDITAR PACIENTE
// ==========================================================

export async function updatePatient(
  idPatient: string,
  data:
    UpdatePatientRequest,
): Promise<UpdatePatientResponse> {

  const response =
    await apiClinico
      .patch<UpdatePatientResponse>(
        `/pacientes/${idPatient}/editar/`,
        data,
      );


  return response.data;

}


// ==========================================================
// BUSCAR POSIBLES DUPLICADOS
// ==========================================================

export async function findPossibleDuplicates(
  filters:
    PossibleDuplicateFilters,
): Promise<PossibleDuplicateResponse> {

  const response =
    await apiClinico
      .get<PossibleDuplicateResponse>(
        "/pacientes/posibles-duplicados/",
        {
          params:
            filters,
        },
      );


  return response.data;

}