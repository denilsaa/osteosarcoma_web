from __future__ import annotations

import json
import os
import re
from pathlib import Path

from django.http import (
    FileResponse,
    JsonResponse,
)
from django.views.decorators.http import (
    require_http_methods,
)


REPORT_ROOT = Path(
    os.environ.get(
        "IA_TRAINING_REPORT_DIR",
        "/app/reportes/entrenamientos",
    )
)


EXPERIMENT_PATTERN = re.compile(
    r"^(EXP|BAL)-\d{2}$"
)


ALLOWED_EVIDENCE_FILES = {
    "curva_loss.png",
    "curva_metricas.png",
    "matriz_confusion_test.png",
    "curva_roc_test.png",
    "curva_pr_test.png",
}


ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get(
        "IA_CORS_ALLOWED_ORIGINS",
        (
            "http://localhost:5173,"
            "http://127.0.0.1:5173"
        ),
    ).split(",")
    if origin.strip()
}


def _add_cors(
    response,
    request,
):
    origin = request.headers.get(
        "Origin"
    )

    if origin in ALLOWED_ORIGINS:
        response[
            "Access-Control-Allow-Origin"
        ] = origin

        response[
            "Vary"
        ] = "Origin"

    response[
        "Access-Control-Allow-Methods"
    ] = "GET, OPTIONS"

    response[
        "Access-Control-Allow-Headers"
    ] = (
        "Content-Type, Authorization"
    )

    return response


def _options_response(
    request,
):
    response = JsonResponse(
        {},
        status=200,
    )

    return _add_cors(
        response,
        request,
    )


def _json_error(
    request,
    code: str,
    message: str,
    status: int,
):
    response = JsonResponse(
        {
            "error": {
                "code": code,
                "message": message,
            }
        },
        status=status,
    )

    return _add_cors(
        response,
        request,
    )


def _load_json(
    path: Path,
):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _experiment_stage(
    experiment_id: str,
) -> str | None:
    if experiment_id.startswith(
        "EXP-"
    ):
        return "01_configuracion"

    if experiment_id.startswith(
        "BAL-"
    ):
        return "02_balanceo"

    return None


def _experiment_directory(
    experiment_id: str,
) -> Path | None:
    if not EXPERIMENT_PATTERN.fullmatch(
        experiment_id
    ):
        return None

    stage = _experiment_stage(
        experiment_id
    )

    if stage is None:
        return None

    return (
        REPORT_ROOT
        / stage
        / experiment_id
    )


@require_http_methods(
    [
        "GET",
        "OPTIONS",
    ]
)
def training_dashboard(
    request,
):
    if request.method == "OPTIONS":
        return _options_response(
            request
        )

    panel_path = (
        REPORT_ROOT
        / "panel_entrenamientos.json"
    )

    if not panel_path.exists():
        return _json_error(
            request=request,
            code=(
                "TRAINING_REPORT_NOT_FOUND"
            ),
            message=(
                "No se encontró el panel "
                "de entrenamientos generado."
            ),
            status=404,
        )

    try:
        panel = _load_json(
            panel_path
        )

    except Exception:
        return _json_error(
            request=request,
            code=(
                "TRAINING_REPORT_INVALID"
            ),
            message=(
                "El archivo del panel "
                "de entrenamientos no es válido."
            ),
            status=500,
        )

    experiments = panel.get(
        "experimentos",
        [],
    )

    enriched_experiments = []

    for experiment in experiments:
        item = dict(
            experiment
        )

        experiment_id = str(
            item.get(
                "experiment_id",
                "",
            )
        )

        directory = (
            _experiment_directory(
                experiment_id
            )
        )

        evidence = []

        if (
            directory is not None
            and directory.exists()
        ):
            for filename in sorted(
                ALLOWED_EVIDENCE_FILES
            ):
                evidence_path = (
                    directory
                    / filename
                )

                if evidence_path.exists():
                    evidence.append(
                        {
                            "archivo": (
                                filename
                            ),
                            "url": (
                                "/entrenamientos/"
                                f"{experiment_id}/"
                                "evidencia/"
                                f"{filename}/"
                            ),
                        }
                    )

        item[
            "evidencias"
        ] = evidence

        enriched_experiments.append(
            item
        )

    panel[
        "experimentos"
    ] = enriched_experiments

    response = JsonResponse(
        {
            "data": panel
        },
        status=200,
    )

    return _add_cors(
        response,
        request,
    )


@require_http_methods(
    [
        "GET",
        "OPTIONS",
    ]
)
def training_experiment_detail(
    request,
    experiment_id: str,
):
    if request.method == "OPTIONS":
        return _options_response(
            request
        )

    directory = (
        _experiment_directory(
            experiment_id
        )
    )

    if directory is None:
        return _json_error(
            request=request,
            code=(
                "TRAINING_EXPERIMENT_INVALID"
            ),
            message=(
                "El identificador del "
                "experimento no es válido."
            ),
            status=400,
        )

    if not directory.exists():
        return _json_error(
            request=request,
            code=(
                "TRAINING_EXPERIMENT_NOT_FOUND"
            ),
            message=(
                "No se encontró el "
                "experimento solicitado."
            ),
            status=404,
        )

    files = {
        "configuracion": (
            "configuracion.json"
        ),
        "validation": (
            "metricas_validation.json"
        ),
        "test": (
            "metricas_test.json"
        ),
        "historial": (
            "historial.json"
        ),
        "resultado_completo": (
            "resultado_completo.json"
        ),
    }

    result = {
        "experiment_id": (
            experiment_id
        ),
        "fase": (
            _experiment_stage(
                experiment_id
            )
        ),
    }

    try:
        for key, filename in (
            files.items()
        ):
            path = (
                directory
                / filename
            )

            result[key] = (
                _load_json(path)
                if path.exists()
                else None
            )

    except Exception:
        return _json_error(
            request=request,
            code=(
                "TRAINING_EXPERIMENT_INVALID"
            ),
            message=(
                "No fue posible leer "
                "los resultados del experimento."
            ),
            status=500,
        )

    result[
        "evidencias"
    ] = [
        {
            "archivo": filename,
            "url": (
                "/entrenamientos/"
                f"{experiment_id}/"
                "evidencia/"
                f"{filename}/"
            ),
        }
        for filename
        in sorted(
            ALLOWED_EVIDENCE_FILES
        )
        if (
            directory
            / filename
        ).exists()
    ]

    response = JsonResponse(
        {
            "data": result
        },
        status=200,
    )

    return _add_cors(
        response,
        request,
    )


@require_http_methods(
    [
        "GET",
        "OPTIONS",
    ]
)
def training_evidence(
    request,
    experiment_id: str,
    filename: str,
):
    if request.method == "OPTIONS":
        return _options_response(
            request
        )

    if (
        filename
        not in ALLOWED_EVIDENCE_FILES
    ):
        return _json_error(
            request=request,
            code=(
                "TRAINING_EVIDENCE_INVALID"
            ),
            message=(
                "El archivo de evidencia "
                "solicitado no está permitido."
            ),
            status=400,
        )

    directory = (
        _experiment_directory(
            experiment_id
        )
    )

    if directory is None:
        return _json_error(
            request=request,
            code=(
                "TRAINING_EXPERIMENT_INVALID"
            ),
            message=(
                "El identificador del "
                "experimento no es válido."
            ),
            status=400,
        )

    path = (
        directory
        / filename
    )

    if not path.exists():
        return _json_error(
            request=request,
            code=(
                "TRAINING_EVIDENCE_NOT_FOUND"
            ),
            message=(
                "No se encontró la evidencia "
                "solicitada."
            ),
            status=404,
        )

    response = FileResponse(
        path.open(
            "rb"
        ),
        content_type="image/png",
    )

    response[
        "Content-Disposition"
    ] = (
        'inline; '
        f'filename="{filename}"'
    )

    return _add_cors(
        response,
        request,
    )
