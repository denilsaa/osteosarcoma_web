from __future__ import annotations

import argparse
import json
from datetime import datetime

import pandas as pd
import torch

from ejecutar_experimentos_osteosarcoma import (
    OUTPUT_ROOT,
    TRAIN_CSV,
    VALIDATION_CSV,
    TEST_CSV,
    TumorDataset,
    crear_transforms,
    json_save,
    result_to_row,
    run_experiment,
    save_comparison_plot,
    seed_everything,
)


SEED = 42


def timestamp() -> str:
    return (
        datetime.now()
        .astimezone()
        .isoformat()
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta exclusivamente la "
            "comparación de técnicas de "
            "balanceo para osteosarcoma."
        )
    )

    parser.add_argument(
        "--responsable",
        default=(
            "Denilson Asis "
            "Saavedra Mamani"
        ),
    )

    args = parser.parse_args()

    seed_everything(
        SEED
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print()
    print(
        "=" * 80
    )
    print(
        " FASE B - COMPARACIÓN "
        "DE BALANCEO"
    )
    print(
        "=" * 80
    )

    print(
        "Dispositivo:",
        device,
    )

    if device.type == "cuda":
        print(
            "GPU:",
            torch.cuda.get_device_name(
                0
            ),
        )

    # ========================================================
    # LEER MEJOR CONFIGURACIÓN DE FASE A
    # ========================================================

    best_config_path = (
        OUTPUT_ROOT
        / "mejor_configuracion_validation.json"
    )

    if not best_config_path.exists():
        raise FileNotFoundError(
            "No existe la mejor configuración "
            "de la Fase A: "
            f"{best_config_path}"
        )

    best_config = json.loads(
        best_config_path.read_text(
            encoding="utf-8"
        )
    )

    print()
    print(
        "Configuración seleccionada "
        "en Fase A:"
    )

    print(
        json.dumps(
            best_config,
            indent=2,
            ensure_ascii=False,
        )
    )

    # ========================================================
    # DATASETS
    # ========================================================

    (
        train_transform,
        eval_transform,
    ) = crear_transforms()

    datasets = {
        "train": TumorDataset(
            TRAIN_CSV,
            train_transform,
        ),
        "validation": TumorDataset(
            VALIDATION_CSV,
            eval_transform,
        ),
        "test": TumorDataset(
            TEST_CSV,
            eval_transform,
        ),
    }

    # ========================================================
    # CONFIGURACIONES DE BALANCEO
    # ========================================================

    base = {
        "optimizer": (
            best_config[
                "optimizer"
            ]
        ),
        "learning_rate": (
            best_config[
                "learning_rate"
            ]
        ),
        "batch_size": (
            best_config[
                "batch_size"
            ]
        ),
        "epochs": (
            best_config[
                "epochs"
            ]
        ),
    }

    balance_configs = [
        {
            "id": "BAL-01",
            **base,
            "balancing": "none",
        },
        {
            "id": "BAL-02",
            **base,
            "balancing": "weighted_loss",
        },
        {
            "id": "BAL-03",
            **base,
            "balancing": "weighted_sampler",
        },
    ]

    results = []

    # ========================================================
    # EJECUTAR BALANCEOS
    # ========================================================

    for config in balance_configs:
        seed_everything(
            SEED
        )

        result = run_experiment(
            config=config,
            datasets=datasets,
            device=device,
            responsable=(
                args.responsable
            ),
            stage="02_balanceo",
        )

        results.append(
            result
        )

    # ========================================================
    # COMPARACIÓN
    # ========================================================

    rows = [
        result_to_row(
            result
        )
        for result in results
    ]

    dataframe = pd.DataFrame(
        rows
    )

    dataframe.to_csv(
        OUTPUT_ROOT
        / "comparacion_balanceo.csv",
        index=False,
    )

    json_save(
        OUTPUT_ROOT
        / "comparacion_balanceo.json",
        rows,
    )

    save_comparison_plot(
        dataframe,
        OUTPUT_ROOT
        / "comparacion_balanceo.png",
        (
            "Comparación de "
            "técnicas de balanceo"
        ),
    )

    # ========================================================
    # SELECCIÓN FINAL
    # SOLO MEDIANTE VALIDATION
    # ========================================================

    best_final = max(
        results,
        key=lambda result: (
            result[
                "validation"
            ][
                "selection_score"
            ]
        ),
    )

    final_selection = {
        "criterio_seleccion": (
            "selection_score calculado "
            "exclusivamente sobre validation"
        ),

        "experiment_id": (
            best_final[
                "experiment_id"
            ]
        ),

        "architecture": (
            "efficientnet_b0"
        ),

        "optimizer": (
            best_final[
                "optimizer"
            ]
        ),

        "learning_rate": (
            best_final[
                "learning_rate"
            ]
        ),

        "batch_size": (
            best_final[
                "batch_size"
            ]
        ),

        "epochs": (
            best_final[
                "epochs"
            ]
        ),

        "best_epoch": (
            best_final[
                "best_epoch"
            ]
        ),

        "balancing": (
            best_final[
                "balancing"
            ]
        ),

        "threshold": (
            best_final[
                "selected_threshold"
            ]
        ),

        "validation_metrics": (
            best_final[
                "validation"
            ]
        ),

        "test_metrics": (
            best_final[
                "test"
            ]
        ),

        "saved_model": (
            best_final[
                "saved_model"
            ]
        ),

        "responsable": (
            args.responsable
        ),

        "fecha": timestamp(),
    }

    json_save(
        OUTPUT_ROOT
        / "configuracion_seleccionada.json",
        final_selection,
    )

    # ========================================================
    # GENERAR PANEL DE TODOS LOS ENTRENAMIENTOS
    # ========================================================

    config_csv = (
        OUTPUT_ROOT
        / "comparacion_configuracion.csv"
    )

    if config_csv.exists():
        config_dataframe = (
            pd.read_csv(
                config_csv
            )
        )

        panel_dataframe = pd.concat(
            [
                config_dataframe,
                dataframe,
            ],
            ignore_index=True,
        )
    else:
        panel_dataframe = (
            dataframe.copy()
        )

    panel_dataframe.to_csv(
        OUTPUT_ROOT
        / "panel_entrenamientos.csv",
        index=False,
    )

    panel_records = (
        panel_dataframe
        .where(
            pd.notnull(
                panel_dataframe
            ),
            None,
        )
        .to_dict(
            orient="records"
        )
    )

    json_save(
        OUTPUT_ROOT
        / "panel_entrenamientos.json",
        {
            "dataset": {
                "train_csv": (
                    str(TRAIN_CSV)
                ),
                "validation_csv": (
                    str(
                        VALIDATION_CSV
                    )
                ),
                "test_csv": (
                    str(TEST_CSV)
                ),
                "train_total": len(
                    datasets[
                        "train"
                    ]
                ),
                "validation_total": len(
                    datasets[
                        "validation"
                    ]
                ),
                "test_total": len(
                    datasets[
                        "test"
                    ]
                ),
            },

            "architecture": (
                "efficientnet_b0"
            ),

            "image_size": 224,

            "responsable": (
                args.responsable
            ),

            "fecha_generacion": (
                timestamp()
            ),

            "experimentos": (
                panel_records
            ),

            "configuracion_seleccionada": (
                final_selection
            ),
        },
    )

    # ========================================================
    # MOSTRAR RESUMEN
    # ========================================================

    print()
    print(
        "=" * 80
    )

    print(
        " COMPARACIÓN DE BALANCEO "
        "TERMINADA"
    )

    print(
        "=" * 80
    )

    print()

    print(
        dataframe[
            [
                "experiment_id",
                "balancing",
                "test_sensitivity",
                "test_specificity",
                "test_f1",
                "test_roc_auc",
                "test_fp",
                "test_fn",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "CONFIGURACIÓN FINAL "
        "SELECCIONADA:"
    )

    print(
        json.dumps(
            final_selection,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(
        "Resultados:",
        OUTPUT_ROOT,
    )


if __name__ == "__main__":
    main()
