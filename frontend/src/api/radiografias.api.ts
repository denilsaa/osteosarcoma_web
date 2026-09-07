import {
  apiRadiografias,
} from "./axios";


// ==========================================================
// TIPO DE ESTUDIO
// ==========================================================

export interface RadiographicStudyType {
  id: number;
  code: string;
  name: string;
}


// ==========================================================
// REGIÓN ANATÓMICA
// ==========================================================

export interface AnatomicalRegion {
  id: number;
  code: string;
  name: string;
}


// ==========================================================
// MIME
// ==========================================================

export interface RadiographicMime {
  code: string;
  mime_type: string;
  extension: string;
}


// ==========================================================
// ARCHIVO
// ==========================================================

export interface RadiographicFile {
  id_file: string;

  version: number;

  original_name: string;

  stored_name: string;

  storage_path: string;

  size_bytes: number;

  width_px: number | null;

  height_px: number | null;

  sha256: string;

  active: boolean;

  mime: RadiographicMime;

  uploaded_at: string;
}


// ==========================================================
// ESTUDIO RADIOGRÁFICO
// ==========================================================

export interface RadiographicStudy {
  id_study: string;

  case_uuid: string;

  registered_by_uuid: string;

  study_type: RadiographicStudyType;

  anatomical_region: AnatomicalRegion;

  study_date: string | null;

  observation: string | null;

  registered_at: string;

  files: RadiographicFile[];
}


// ==========================================================
// RESPUESTA
// ==========================================================

export interface CaseRadiographiesResponse {
  data: RadiographicStudy[];
  total: number;
}


// ==========================================================
// CONSULTAR POR CASO
// ==========================================================

export async function getCaseRadiographies(
  caseId: string,
): Promise<CaseRadiographiesResponse> {

  const response =
    await apiRadiografias
      .get<CaseRadiographiesResponse>(
        `/casos/${caseId}/radiografias`,
      );


  return response.data;
}