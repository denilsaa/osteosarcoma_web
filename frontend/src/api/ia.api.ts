import { apiIA } from "./axios";


// ==========================================================
// PIPELINE DE INFERENCIA
// ==========================================================

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


export interface OsteosarcomaLocalizationCoordinates {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}


export interface OsteosarcomaLocalizationResult {
  evaluada: boolean;
  detectada: boolean;
  confianza: number | null;
  umbral: number;
  coordenadas_normalizadas:
    OsteosarcomaLocalizationCoordinates | null;
  mensaje: string;
}

export interface AiAnalysisPersistence {
  id_analisis: string;
  fecha_analisis: string;
}


export interface RadiographyAnalysisContext {
  radiografia_uuid: string;
  caso_uuid: string;
  solicitado_por_uuid?: string | null;
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
  localizacion_osteosarcoma?: OsteosarcomaLocalizationResult;

  persistencia?: AiAnalysisPersistence;
}


interface RadiographyValidationApiResponse {
  data: RadiographyValidationResponse;
}


export async function validateRadiography(
  file: File,
  context?: RadiographyAnalysisContext,
): Promise<RadiographyValidationResponse> {
  const formData = new FormData();

  formData.append(
    "file",
    file,
    file.name,
  );

  if (context) {
    formData.append(
      "radiografia_uuid",
      context.radiografia_uuid,
    );

    formData.append(
      "caso_uuid",
      context.caso_uuid,
    );

    if (context.solicitado_por_uuid) {
      formData.append(
        "solicitado_por_uuid",
        context.solicitado_por_uuid,
      );
    }
  }

  const response =
    await apiIA.post<RadiographyValidationApiResponse>(
      "/validaciones/radiografia/",
      formData,
    );

  return response.data.data;
}


interface LatestRadiographyAnalysisApiResponse {
  data: RadiographyValidationResponse | null;
}


export async function getLatestRadiographyAnalysis(
  radiographyUuid: string,
  caseUuid?: string,
): Promise<RadiographyValidationResponse | null> {
  const response =
    await apiIA.get<LatestRadiographyAnalysisApiResponse>(
      `/analisis/radiografia/${radiographyUuid}/ultimo/`,
      {
        params:
          caseUuid
            ? {
                caso_uuid: caseUuid,
              }
            : undefined,
      },
    );

  return response.data.data;
}


// ==========================================================
// ENTRENAMIENTOS IA
// ==========================================================

export interface TrainingEvidence {
  archivo: string;
  url: string;
}


export interface TrainingDatasetSummary {
  train_csv: string;
  validation_csv: string;
  test_csv: string;

  train_total: number;
  validation_total: number;
  test_total: number;
}


export interface TrainingExperiment {
  experiment_id: string;
  stage: string;

  optimizer: string;
  learning_rate: number;
  batch_size: number;

  epochs: number;
  best_epoch: number;

  balancing: string;
  threshold: number;

  validation_score: number;

  test_accuracy: number;
  test_precision: number;
  test_sensitivity: number;
  test_specificity: number;
  test_f1: number;
  test_roc_auc: number;
  test_pr_auc: number;

  test_fp: number;
  test_fn: number;

  fecha: string;
  responsable: string;
  modelo: string;

  evidencias: TrainingEvidence[];
}


export interface TrainingMetrics {
  threshold: number;

  accuracy: number;
  precision: number;

  sensitivity: number;
  recall: number;
  specificity: number;

  f1: number;
  roc_auc: number;
  pr_auc: number;

  true_negative: number;
  false_positive: number;
  false_negative: number;
  true_positive: number;

  confusion_matrix: number[][];

  loss?: number;
  selection_score?: number;
}


export interface SelectedTrainingConfiguration {
  criterio_seleccion: string;

  experiment_id: string;
  architecture: string;

  optimizer: string;
  learning_rate: number;

  batch_size: number;
  epochs: number;
  best_epoch: number;

  balancing: string;
  threshold: number;

  validation_metrics: TrainingMetrics;
  test_metrics: TrainingMetrics;

  saved_model: string;

  responsable: string;
  fecha: string;
}


export interface TrainingDashboard {
  dataset: TrainingDatasetSummary;

  architecture: string;
  image_size: number;

  responsable: string;
  fecha_generacion: string;

  experimentos: TrainingExperiment[];

  configuracion_seleccionada:
    SelectedTrainingConfiguration;
}


interface TrainingDashboardApiResponse {
  data: TrainingDashboard;
}


export interface TrainingHistoryItem
  extends TrainingMetrics {
  epoch: number;
  train_loss: number;
  val_loss: number;
}


export interface TrainingExperimentConfiguration {
  experiment_id: string;
  stage: string;

  dataset: TrainingDatasetSummary;

  architecture: string;
  image_size: number;

  optimizer: string;
  learning_rate: number;
  batch_size: number;

  epochs: number;
  best_epoch: number;

  balancing: string;

  balancing_info?: {
    class_counts?: number[];
    class_weights?: number[] | null;
  };

  augmentation_train_only?: boolean;

  training_strategy?: string;
  parent_model?: string;

  threshold_selected_from?: string;
  selected_threshold: number;

  selection_score?: number;

  responsable: string;
  fecha: string;

  saved_model: string;
}


export interface TrainingExperimentDetail {
  experiment_id: string;
  fase: string;

  configuracion:
    TrainingExperimentConfiguration | null;

  validation:
    TrainingMetrics | null;

  test:
    TrainingMetrics | null;

  historial:
    TrainingHistoryItem[] | null;

  resultado_completo?: unknown;

  evidencias: TrainingEvidence[];
}


interface TrainingExperimentApiResponse {
  data: TrainingExperimentDetail;
}


// ==========================================================
// PETICIONES ENTRENAMIENTOS
// ==========================================================

export async function getTrainingDashboard():
Promise<TrainingDashboard> {
  const response =
    await apiIA.get<TrainingDashboardApiResponse>(
      "/entrenamientos/",
    );

  return response.data.data;
}


export async function getTrainingExperiment(
  experimentId: string,
): Promise<TrainingExperimentDetail> {
  const response =
    await apiIA.get<TrainingExperimentApiResponse>(
      `/entrenamientos/${experimentId}/`,
    );

  return response.data.data;
}


// ==========================================================
// URL DE EVIDENCIAS
// ==========================================================

export function getTrainingEvidenceUrl(
  relativeUrl: string,
): string {
  const base =
    String(
      apiIA.defaults.baseURL ?? "",
    ).replace(
      /\/$/,
      "",
    );

  const relative =
    relativeUrl.replace(
      /^\//,
      "",
    );

  return `${base}/${relative}`;
}
