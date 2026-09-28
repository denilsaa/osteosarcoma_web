import { apiIA } from "./axios";

export interface RadiographyModelResult {
  confianza: number;
  probabilidad_radiografia: number;
  probabilidad_no_radiografia: number;
  umbral: number;
  arquitectura: string;
  version: string;
}

export interface AnatomyModelResult {
  confianza: number;
  probabilidad_admitida: number;
  probabilidad_no_admitida: number;
  umbral: number;
  arquitectura: string;
  version: string;
  huesos_admitidos: string[];
}

export interface OsteosarcomaModelResult {
  sospechoso: boolean;
  confianza: number;
  probabilidad_osteosarcoma: number;
  probabilidad_no_osteosarcoma: number;
  umbral: number;
  arquitectura: string;
  version: string;
}

export interface RadiographyValidationResponse {
  es_radiografia: boolean;

  anatomia_evaluada: boolean;
  anatomia_admitida: boolean | null;

  analisis_osteosarcoma_evaluado: boolean;
  osteosarcoma_sospechoso: boolean | null;

  puede_continuar: boolean;
  etapa_rechazo: string | null;

  confianza: number;
  probabilidad_radiografia: number;
  probabilidad_no_radiografia: number;
  umbral: number;
  arquitectura: string;
  familia_modelo: string;

  mensaje: string;

  validacion_radiografia?: RadiographyModelResult;
  validacion_anatomica?: AnatomyModelResult;
  analisis_osteosarcoma?: OsteosarcomaModelResult;
}

interface RadiographyValidationApiResponse {
  data: RadiographyValidationResponse;
}

export async function validateRadiography(
  file: File,
): Promise<RadiographyValidationResponse> {
  const formData = new FormData();

  formData.append(
    "file",
    file,
    file.name,
  );

  const response =
    await apiIA.post<RadiographyValidationApiResponse>(
      "/validaciones/radiografia/",
      formData,
    );

  return response.data.data;
}
