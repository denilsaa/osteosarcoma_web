/**
 * Funciones auxiliares del módulo de radiografías clínicas.
 * Extraídas sin cambiar su comportamiento durante la optimización 4A.4.
 * No realizan solicitudes de red ni modifican información clínica.
 */
import type {
  RadiographicFile,
  RadiographicStudy,
} from "../../api/radiografias.api";

export function formatDate(
  value?:
    string | null,
): string {

  if (!value) {
    return "?";
  }

  const date =
    new Date(
      `${value.substring(0, 10)}T00:00:00`,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "es-BO",
    {
      day:
        "2-digit",

      month:
        "2-digit",

      year:
        "numeric",
    },
  ).format(
    date,
  );
}


export function formatDateTime(
  value?:
    string | null,
): string {

  if (!value) {
    return "?";
  }

  const date =
    new Date(
      value,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "es-BO",
    {
      day:
        "2-digit",

      month:
        "2-digit",

      year:
        "numeric",

      hour:
        "2-digit",

      minute:
        "2-digit",
    },
  ).format(
    date,
  );
}


export function formatBytes(
  value:
    number,
): string {

  if (
    value < 1024
  ) {
    return `${value} B`;
  }

  if (
    value
    <
    1024 * 1024
  ) {
    return (
      `${(
        value
        /
        1024
      ).toFixed(1)} KB`
    );
  }

  return (
    `${(
      value
      /
      (
        1024
        *
        1024
      )
    ).toFixed(2)} MB`
  );
}


export function formatPercentage(
  value?:
    number | null,
): string {

  if (
    value === undefined
    ||
    value === null
    ||
    Number.isNaN(value)
  ) {
    return "—";
  }

  return `${(
    value * 100
  ).toFixed(2)} %`;
}


export function getErrorMessage(
  error:
    unknown,
): string {

  if (
    typeof error ===
    "object"
    &&
    error !== null
    &&
    "response" in error
  ) {

    const response =
      (
        error as {
          response?: {
            data?: {
              message?:
                string;

              detail?:
                string;

              error?:
                string
                |
                {
                  message?:
                    string;
                };

              errors?:
                Record<
                  string,
                  string[]
                >;
            };
          };
        }
      )
        .response;

    if (
      typeof response
        ?.data
        ?.error
      ===
      "object"
      &&
      response
        ?.data
        ?.error
        ?.message
    ) {

      return response
        .data
        .error
        .message;
    }

    if (
      typeof response
        ?.data
        ?.error
      ===
      "string"
    ) {

      return response
        .data
        .error;
    }

    if (
      response
        ?.data
        ?.message
    ) {

      return response
        .data
        .message;
    }

    if (
      typeof response
        ?.data
        ?.detail
      ===
      "string"
    ) {

      return response
        .data
        .detail;
    }

    const errors =
      response
        ?.data
        ?.errors;

    if (errors) {

      const first =
        Object
          .values(
            errors,
          )
          .flat()
          .find(
            Boolean,
          );

      if (first) {
        return first;
      }
    }
  }

  return (
    "No fue posible completar la operación."
  );
}


export function getValidationStatusClass(
  file:
    RadiographicFile,
): string {

  switch (
    file.validation_status
  ) {

    case "VALIDA":
      return "case-radiographies-status--valid";

    case "RECHAZADA":
      return "case-radiographies-status--rejected";

    default:
      return "case-radiographies-status--pending";
  }
}


export function getPrimaryRadiographicFile(
  study: RadiographicStudy,
): RadiographicFile | null {

  return (
    study.files.find(
      (file) =>
        file.active,
    )
    ??
    study.files[0]
    ??
    null
  );
}



const RADIOGRAPHY_FILE_EXTENSIONS =
  [
    "jpg",
    "jpeg",
    "png",
    "dcm",
  ] as const;


export function getLocalRadiographyExtension(
  file?: File | null,
): string {

  if (!file) {
    return "";
  }

  return (
    file
      .name
      .split(".")
      .pop()
      ?.toLowerCase()
    ??
    ""
  );
}


export function isAcceptedLocalRadiographyFile(
  file?: File | null,
): boolean {

  return RADIOGRAPHY_FILE_EXTENSIONS.includes(
    getLocalRadiographyExtension(
      file,
    ) as typeof RADIOGRAPHY_FILE_EXTENSIONS[number],
  );
}


export function isLocalRadiographyPreviewable(
  file?: File | null,
): boolean {

  const extension =
    getLocalRadiographyExtension(
      file,
    );

  return [
    "jpg",
    "jpeg",
    "png",
  ].includes(
    extension,
  );
}


export function getLocalRadiographyFormatLabel(
  file?: File | null,
): string {

  const extension =
    getLocalRadiographyExtension(
      file,
    );

  switch (extension) {
    case "jpg":
    case "jpeg":
      return "JPEG";

    case "png":
      return "PNG";

    case "dcm":
      return "DICOM";

    default:
      return extension
        ? extension.toUpperCase()
        : "Archivo";
  }
}


export function isRadiographicFilePreviewable(
  file?: RadiographicFile | null,
): boolean {

  return Boolean(
    file
    &&
    file.validation_status === "VALIDA"
    &&
    file.mime.code !== "DICOM",
  );
}


export function getShortValidationLabel(
  file?: RadiographicFile | null,
): string {

  if (!file) {
    return "Sin archivo";
  }

  switch (file.validation_status) {
    case "VALIDA":
      return "Válida";

    case "RECHAZADA":
      return "Rechazada";

    default:
      return "Pendiente";
  }
}


