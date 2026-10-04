from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


TEST_CSV = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "03_particiones/test_v1.csv"
)

MODELS = {
    "baseline_v1": Path(
        "/modelos/"
        "osteosarcoma_efficientnet_b0_baseline_v1.pt"
    ),
    "finetuned_v1": Path(
        "/modelos/"
        "osteosarcoma_efficientnet_b0_finetuned_v1.pt"
    ),
}

OUTPUT_DIR = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "04_reportes/evaluacion_osteosarcoma"
)

IMAGENET_MEAN = [
    0.485,
    0.456,
    0.406,
]

IMAGENET_STD = [
    0.229,
    0.224,
    0.225,
]


class OsteosarcomaDataset(Dataset):

    def __init__(
        self,
        csv_path: Path,
    ):
        self.data = pd.read_csv(
            csv_path
        )

        self.transform = transforms.Compose(
            [
                transforms.Resize(
                    (224, 224)
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    IMAGENET_MEAN,
                    IMAGENET_STD,
                ),
            ]
        )

    def __len__(self):
        return len(
            self.data
        )

    def __getitem__(
        self,
        index,
    ):
        row = self.data.iloc[
            index
        ]

        image_path = Path(
            str(
                row["image_path"]
            )
        )

        with Image.open(
            image_path
        ) as image:
            image = image.convert(
                "RGB"
            )

        tensor = self.transform(
            image
        )

        label = int(
            row["osteosarcoma"]
        )

        return (
            tensor,
            label,
            index,
        )


def cargar_modelo(
    checkpoint_path: Path,
    device,
):
    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )

    model = models.efficientnet_b0(
        weights=None
    )

    in_features = (
        model.classifier[1]
        .in_features
    )

    model.classifier[1] = nn.Linear(
        in_features,
        2,
    )

    model.load_state_dict(
        checkpoint["state_dict"]
    )

    model.to(
        device
    )

    model.eval()

    threshold = float(
        checkpoint.get(
            "threshold",
            0.5,
        )
    )

    return (
        model,
        threshold,
        checkpoint,
    )


def inferir(
    model,
    loader,
    device,
):
    y_true = []
    y_prob = []
    indices = []

    with torch.no_grad():

        for (
            images,
            labels,
            batch_indices,
        ) in loader:

            images = images.to(
                device
            )

            logits = model(
                images
            )

            probabilities = (
                torch.softmax(
                    logits,
                    dim=1,
                )[:, 1]
            )

            y_true.extend(
                labels.tolist()
            )

            y_prob.extend(
                probabilities
                .cpu()
                .tolist()
            )

            indices.extend(
                batch_indices.tolist()
            )

    return (
        np.asarray(
            y_true,
            dtype=np.int64,
        ),
        np.asarray(
            y_prob,
            dtype=np.float64,
        ),
        np.asarray(
            indices,
            dtype=np.int64,
        ),
    )


def calcular_metricas(
    y_true,
    y_prob,
    threshold,
):
    y_pred = (
        y_prob >= threshold
    ).astype(
        np.int64
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    tn, fp, fn, tp = (
        matrix.ravel()
    )

    sensitivity = (
        tp / (tp + fn)
        if tp + fn > 0
        else 0.0
    )

    specificity = (
        tn / (tn + fp)
        if tn + fp > 0
        else 0.0
    )

    return {
        "threshold": float(
            threshold
        ),
        "accuracy": float(
            accuracy_score(
                y_true,
                y_pred,
            )
        ),
        "precision": float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "sensitivity": float(
            sensitivity
        ),
        "specificity": float(
            specificity
        ),
        "f1": float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "roc_auc": float(
            roc_auc_score(
                y_true,
                y_prob,
            )
        ),
        "pr_auc": float(
            average_precision_score(
                y_true,
                y_prob,
            )
        ),
        "true_negative": int(
            tn
        ),
        "false_positive": int(
            fp
        ),
        "false_negative": int(
            fn
        ),
        "true_positive": int(
            tp
        ),
        "confusion_matrix": (
            matrix.tolist()
        ),
    }


def guardar_confusion_matrix(
    matrix,
    output_path,
    title,
):
    figure = plt.figure(
        figsize=(6, 5)
    )

    axis = figure.add_subplot(
        1,
        1,
        1,
    )

    image = axis.imshow(
        matrix,
        cmap="Blues",
    )

    figure.colorbar(
        image,
        ax=axis,
    )

    axis.set_xticks(
        [0, 1]
    )

    axis.set_yticks(
        [0, 1]
    )

    axis.set_xticklabels(
        [
            "No osteosarcoma",
            "Osteosarcoma",
        ]
    )

    axis.set_yticklabels(
        [
            "No osteosarcoma",
            "Osteosarcoma",
        ]
    )

    axis.set_xlabel(
        "Predicción"
    )

    axis.set_ylabel(
        "Real"
    )

    axis.set_title(
        title
    )

    for row in range(2):
        for column in range(2):

            axis.text(
                column,
                row,
                str(
                    matrix[
                        row,
                        column,
                    ]
                ),
                ha="center",
                va="center",
                fontsize=14,
            )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )


def guardar_curva_roc(
    y_true,
    y_prob,
    output_path,
    auc,
):
    fpr, tpr, _ = roc_curve(
        y_true,
        y_prob,
    )

    figure = plt.figure(
        figsize=(6, 5)
    )

    axis = figure.add_subplot(
        1,
        1,
        1,
    )

    axis.plot(
        fpr,
        tpr,
        label=(
            f"AUC = {auc:.4f}"
        ),
    )

    axis.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
    )

    axis.set_xlabel(
        "Tasa de falsos positivos"
    )

    axis.set_ylabel(
        "Sensibilidad"
    )

    axis.set_title(
        "Curva ROC"
    )

    axis.legend()

    axis.grid(
        alpha=0.25
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )


def guardar_curva_pr(
    y_true,
    y_prob,
    output_path,
    pr_auc,
):
    precision, recall, _ = (
        precision_recall_curve(
            y_true,
            y_prob,
        )
    )

    figure = plt.figure(
        figsize=(6, 5)
    )

    axis = figure.add_subplot(
        1,
        1,
        1,
    )

    axis.plot(
        recall,
        precision,
        label=(
            f"AP = {pr_auc:.4f}"
        ),
    )

    axis.set_xlabel(
        "Recall / Sensibilidad"
    )

    axis.set_ylabel(
        "Precisión"
    )

    axis.set_title(
        "Curva Precision-Recall"
    )

    axis.legend()

    axis.grid(
        alpha=0.25
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )


def guardar_errores(
    data,
    indices,
    y_true,
    y_prob,
    threshold,
    output_path,
):
    y_pred = (
        y_prob >= threshold
    ).astype(
        np.int64
    )

    records = []

    for position in range(
        len(y_true)
    ):
        real = int(
            y_true[position]
        )

        predicted = int(
            y_pred[position]
        )

        if real == predicted:
            continue

        dataset_index = int(
            indices[position]
        )

        row = data.iloc[
            dataset_index
        ]

        error_type = (
            "FP"
            if real == 0
            and predicted == 1
            else "FN"
        )

        records.append(
            {
                "image_id": str(
                    row["image_id"]
                ),
                "image_path": str(
                    row["image_path"]
                ),
                "anatomy": str(
                    row.get(
                        "anatomy",
                        "",
                    )
                ),
                "diagnosis": str(
                    row.get(
                        "diagnosis",
                        "",
                    )
                ),
                "real": real,
                "predicted": predicted,
                "probability_osteosarcoma": float(
                    y_prob[
                        position
                    ]
                ),
                "error_type": (
                    error_type
                ),
            }
        )

    pd.DataFrame(
        records
    ).to_csv(
        output_path,
        index=False,
    )


def main():

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print()
    print(
        "=" * 72
    )

    print(
        "EVALUACIÓN DEFINITIVA "
        "OSTEOSARCOMA"
    )

    print(
        "=" * 72
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

    dataset = OsteosarcomaDataset(
        TEST_CSV
    )

    loader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=False,
        num_workers=0,
        pin_memory=(
            device.type == "cuda"
        ),
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    comparison = {}

    for (
        model_name,
        model_path,
    ) in MODELS.items():

        print()
        print(
            "=" * 72
        )

        print(
            "MODELO:",
            model_name,
        )

        print(
            "=" * 72
        )

        model_output = (
            OUTPUT_DIR
            / model_name
        )

        model_output.mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            model,
            threshold,
            checkpoint,
        ) = cargar_modelo(
            model_path,
            device,
        )

        (
            y_true,
            y_prob,
            indices,
        ) = inferir(
            model,
            loader,
            device,
        )

        metrics = calcular_metricas(
            y_true,
            y_prob,
            threshold,
        )

        comparison[
            model_name
        ] = metrics

        metrics_path = (
            model_output
            / "metricas_test.json"
        )

        metrics_path.write_text(
            json.dumps(
                metrics,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        matrix = np.asarray(
            metrics[
                "confusion_matrix"
            ]
        )

        guardar_confusion_matrix(
            matrix,
            model_output
            / "matriz_confusion.png",
            (
                "Matriz de confusión - "
                + model_name
            ),
        )

        guardar_curva_roc(
            y_true,
            y_prob,
            model_output
            / "curva_roc.png",
            metrics[
                "roc_auc"
            ],
        )

        guardar_curva_pr(
            y_true,
            y_prob,
            model_output
            / "curva_pr.png",
            metrics[
                "pr_auc"
            ],
        )

        guardar_errores(
            dataset.data,
            indices,
            y_true,
            y_prob,
            threshold,
            model_output
            / "errores_fp_fn.csv",
        )

        np.savez(
            model_output
            / "predicciones_test.npz",
            y_true=y_true,
            y_prob=y_prob,
            indices=indices,
            threshold=np.asarray(
                [threshold]
            ),
        )

        print(
            json.dumps(
                metrics,
                indent=2,
                ensure_ascii=False,
            )
        )

    comparison_path = (
        OUTPUT_DIR
        / "comparacion_modelos.json"
    )

    comparison_path.write_text(
        json.dumps(
            comparison,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    rows = []

    for (
        name,
        metrics,
    ) in comparison.items():

        rows.append(
            {
                "modelo": name,
                "accuracy": (
                    metrics[
                        "accuracy"
                    ]
                ),
                "precision": (
                    metrics[
                        "precision"
                    ]
                ),
                "sensitivity": (
                    metrics[
                        "sensitivity"
                    ]
                ),
                "specificity": (
                    metrics[
                        "specificity"
                    ]
                ),
                "f1": (
                    metrics[
                        "f1"
                    ]
                ),
                "roc_auc": (
                    metrics[
                        "roc_auc"
                    ]
                ),
                "pr_auc": (
                    metrics[
                        "pr_auc"
                    ]
                ),
                "fp": (
                    metrics[
                        "false_positive"
                    ]
                ),
                "fn": (
                    metrics[
                        "false_negative"
                    ]
                ),
            }
        )

    comparison_csv = pd.DataFrame(
        rows
    )

    comparison_csv.to_csv(
        OUTPUT_DIR
        / "comparacion_modelos.csv",
        index=False,
    )

    print()
    print(
        "=" * 72
    )

    print(
        "EVALUACIÓN TERMINADA"
    )

    print(
        "=" * 72
    )

    print(
        "Resultados:",
        OUTPUT_DIR,
    )


if __name__ == "__main__":
    main()
