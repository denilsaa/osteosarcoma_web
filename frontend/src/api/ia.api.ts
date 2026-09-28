import { apiIA } from "./axios";

export interface RadiographyValidationResponse {
  es_radiografia: boolean;
  confianza: number;
  probabilidad_radiografia: number;
  probabilidad_no_radiografia: number;
  umbral: number;
  arquitectura: string;
  familia_modelo: string;
  mensaje: string;
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
