import {
  apiRadiografias,
} from "./axios";


// ==========================================================
// CATÁLOGOS
// ==========================================================

export interface RadiographicStudyType {
  id: number;
  code: string;
  name: string;
}


export interface AnatomicalRegion {
  id: number;
  code: string;
  name: string;
}


export interface RadiographicLaterality {
  id: number;
  code: string;
  name: string;
}


export interface RadiographyCatalogs {
  study_types:
    RadiographicStudyType[];

  anatomical_regions:
    AnatomicalRegion[];

  lateralities:
    RadiographicLaterality[];
}


interface RadiographyCatalogsResponse {
  data:
    RadiographyCatalogs;
}


// ==========================================================
// MIME
// ==========================================================

export interface RadiographicMime {
  code:
    string;

  mime_type:
    string;

  extension:
    string;
}


// ==========================================================
// VALIDACIÓN DE ARCHIVO
// ==========================================================

export type RadiographicValidationStatus =
  | "PENDIENTE"
  | "VALIDA"
  | "RECHAZADA";


export type RadiographicValidationResultCode =
  | "VALIDO"
  | "INVALIDO";


export interface RadiographicFileValidation {
  type_code:
    string;

  type_name:
    string;

  result_code:
    RadiographicValidationResultCode;

  result_name:
    string;

  detail:
    string | null;

  reason:
    string | null;

  correction:
    string | null;

  validated_at:
    string | null;
}


// ==========================================================
// ARCHIVO
// ==========================================================

export interface RadiographicFile {
  id_file:
    string;

  version:
    number;

  original_name:
    string;

  size_bytes:
    number;

  width_px:
    number | null;

  height_px:
    number | null;

  sha256:
    string;

  active:
    boolean;

  validation_status:
    RadiographicValidationStatus;

  validations:
    RadiographicFileValidation[];

  mime:
    RadiographicMime;

  uploaded_at:
    string;

  view_url:
    string;

  download_url:
    string;
}


// ==========================================================
// ESTUDIO
// ==========================================================

export interface RadiographicStudy {
  id_study:
    string;

  case_uuid:
    string;

  registered_by_uuid:
    string;

  study_type:
    RadiographicStudyType;

  anatomical_region:
    AnatomicalRegion;

  laterality:
    RadiographicLaterality | null;

  study_date:
    string | null;

  observation:
    string | null;

  registered_at:
    string;

  files:
    RadiographicFile[];
}


// ==========================================================
// RESPUESTAS
// ==========================================================

export interface CaseRadiographiesResponse {
  data:
    RadiographicStudy[];

  total:
    number;
}


export interface CreateRadiographyResponse {
  message:
    string;

  data:
    RadiographicStudy;
}


// ==========================================================
// REQUEST CREACIÓN
// ==========================================================

export interface CreateRadiographyRequest {
  study_type_id:
    number;

  anatomical_region_id:
    number;

  laterality_id:
    number;

  study_date:
    string | null;

  observation:
    string | null;

  file:
    File;
}


// ==========================================================
// OPCIONES DE CARGA
// ==========================================================

export interface CreateRadiographyOptions {
  onUploadProgress?:
    (
      progress:
        number,
    ) => void;
}


// ==========================================================
// CATÁLOGOS
// ==========================================================

export async function getRadiographyCatalogs():
  Promise<RadiographyCatalogs> {

  const response =
    await apiRadiografias
      .get<RadiographyCatalogsResponse>(
        "/radiografias/catalogos",
      );


  return response
    .data
    .data;
}


// ==========================================================
// LISTADO
// ==========================================================

export async function getCaseRadiographies(
  caseId:
    string,
): Promise<CaseRadiographiesResponse> {

  const response =
    await apiRadiografias
      .get<CaseRadiographiesResponse>(
        `/casos/${caseId}/radiografias`,
      );


  return response.data;
}


// ==========================================================
// REGISTRAR RADIOGRAFÍA
// ==========================================================

export async function createRadiography(
  caseId:
    string,

  data:
    CreateRadiographyRequest,

  options:
    CreateRadiographyOptions = {},
): Promise<CreateRadiographyResponse> {

  const formData =
    new FormData();


  formData.append(
    "study_type_id",
    String(
      data.study_type_id,
    ),
  );


  formData.append(
    "anatomical_region_id",
    String(
      data.anatomical_region_id,
    ),
  );


  formData.append(
    "laterality_id",
    String(
      data.laterality_id,
    ),
  );


  if (
    data.study_date
  ) {

    formData.append(
      "study_date",
      data.study_date,
    );

  }


  if (
    data.observation
    &&
    data.observation.trim()
  ) {

    formData.append(
      "observation",
      data.observation.trim(),
    );

  }


  formData.append(
    "file",
    data.file,
    data.file.name,
  );


  /*
   * No forzar Content-Type.
   *
   * El navegador genera automáticamente
   * multipart/form-data con su boundary.
   */
  const response =
    await apiRadiografias
      .post<CreateRadiographyResponse>(
        `/casos/${caseId}/radiografias`,
        formData,
        {
          onUploadProgress:
            (
              progressEvent,
            ) => {

              if (
                !options
                  .onUploadProgress
              ) {
                return;
              }


              const total =
                progressEvent.total;


              if (
                !total
                ||
                total <= 0
              ) {
                return;
              }


              const percentage =
                Math.min(
                  100,
                  Math.max(
                    0,
                    Math.round(
                      (
                        progressEvent.loaded
                        *
                        100
                      )
                      /
                      total,
                    ),
                  ),
                );


              options
                .onUploadProgress(
                  percentage,
                );

            },
        },
      );


  return response.data;
}


// ==========================================================
// VISUALIZAR ARCHIVO
// ==========================================================

export async function getRadiographicFileBlob(
  fileId:
    string,
): Promise<Blob> {

  const response =
    await apiRadiografias
      .get<Blob>(
        `/radiografias/archivos/${fileId}/ver`,
        {
          responseType:
            "blob",
        },
      );


  return response.data;
}


// ==========================================================
// DESCARGAR ARCHIVO
// ==========================================================

export async function downloadRadiographicFileBlob(
  fileId:
    string,
): Promise<Blob> {

  const response =
    await apiRadiografias
      .get<Blob>(
        `/radiografias/archivos/${fileId}/descargar`,
        {
          responseType:
            "blob",
        },
      );


  return response.data;
}