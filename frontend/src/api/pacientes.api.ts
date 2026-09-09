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
// DEPARTAMENTOS DE BOLIVIA
// ==========================================================

export type BoliviaDepartmentCode =
  | "LP"
  | "CB"
  | "SC"
  | "OR"
  | "PT"
  | "CH"
  | "TJ"
  | "BE"
  | "PD";


export interface BoliviaDepartment {
  code: BoliviaDepartmentCode;

  name: string;
}


export const BOLIVIA_DEPARTMENTS:
  BoliviaDepartment[] = [
    {
      code: "LP",
      name: "La Paz",
    },
    {
      code: "CB",
      name: "Cochabamba",
    },
    {
      code: "SC",
      name: "Santa Cruz",
    },
    {
      code: "OR",
      name: "Oruro",
    },
    {
      code: "PT",
      name: "Potosí",
    },
    {
      code: "CH",
      name: "Chuquisaca",
    },
    {
      code: "TJ",
      name: "Tarija",
    },
    {
      code: "BE",
      name: "Beni",
    },
    {
      code: "PD",
      name: "Pando",
    },
  ];


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
    BoliviaDepartmentCode | string | null;
}


// ==========================================================
// CONTACTO DEL PACIENTE
// ==========================================================

export interface PatientContact {
  id_contact:
    string | null;

  contact_type_id:
    number;

  contact_type_code:
    "CELULAR"
    | "TELEFONO"
    | "CORREO"
    | string;

  contact_type_name:
    string;

  value:
    string;

  primary:
    boolean;
}


// ==========================================================
// CONTACTO DE EMERGENCIA
// ==========================================================

export interface PatientEmergencyContact {
  id_emergency_contact:
    string | null;

  full_name:
    string;

  relationship:
    string;

  phone:
    string;

  email:
    string | null;

  primary:
    boolean;

  registration_date:
    string | null;
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

  emergency_contacts:
    PatientEmergencyContact[];

  primary_emergency_contact:
    PatientEmergencyContact | null;

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
  // -------------------------------------------------------
  // DATOS PERSONALES
  // -------------------------------------------------------

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

  // -------------------------------------------------------
  // DOCUMENTO
  // -------------------------------------------------------

  document_type_id:
    number;

  document_number:
    string;

  complement?:
    string | null;

  issued_in:
    BoliviaDepartmentCode;

  // -------------------------------------------------------
  // CONTACTOS DEL PACIENTE
  // -------------------------------------------------------

  mobile_phone?:
    string | null;

  landline_phone?:
    string | null;

  email?:
    string | null;

  // -------------------------------------------------------
  // CONTACTO DE EMERGENCIA
  // -------------------------------------------------------

  emergency_contact_name?:
    string | null;

  emergency_relationship?:
    string | null;

  emergency_phone?:
    string | null;

  emergency_email?:
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

  const params:
    Record<
      string,
      string | number
    > = {};


  if (
    filters.document_type_id
  ) {

    params.document_type_id =
      filters.document_type_id;
  }


  if (
    filters.document_number
      ?.trim()
  ) {

    params.document_number =
      filters.document_number.trim();
  }


  if (
    filters.first_names
      ?.trim()
  ) {

    params.first_names =
      filters.first_names.trim();
  }


  if (
    filters.paternal_surname
      ?.trim()
  ) {

    params.paternal_surname =
      filters.paternal_surname.trim();
  }


  if (
    filters.maternal_surname
      ?.trim()
  ) {

    params.maternal_surname =
      filters.maternal_surname.trim();
  }


  if (
    filters.birth_date
  ) {

    params.birth_date =
      filters.birth_date;
  }


  const response =
    await apiClinico
      .get<PossibleDuplicateResponse>(
        "/pacientes/posibles-duplicados/",
        {
          params,
        },
      );


  return response.data;
}