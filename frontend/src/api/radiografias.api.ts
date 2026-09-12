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
   * IMPORTANTE:
   *
   * NO colocar:
   *
   * Content-Type: multipart/form-data
   *
   * ni application/json.
   *
   * El navegador genera automáticamente:
   *
   * multipart/form-data;
   * boundary=--------------------xxxx
   *
   * Si nosotros forzamos el Content-Type,
   * Laravel puede no recibir correctamente
   * el archivo.
   */
  const response =
    await apiRadiografias
      .post<CreateRadiographyResponse>(
        `/casos/${caseId}/radiografias`,
        formData,
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