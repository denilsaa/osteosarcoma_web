from __future__ import annotations

import argparse
import copy
import json
import random
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

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
from torch.utils.data import (
    DataLoader,
    Dataset,
    WeightedRandomSampler,
)

from torchvision import (
    models,
    transforms,
)


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

SEED = 42

TRAIN_CSV = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "03_particiones/train_v1.csv"
)

VALIDATION_CSV = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "03_particiones/validation_v1.csv"
)

TEST_CSV = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "03_particiones/test_v1.csv"
)

BASELINE_PATH = Path(
    "/modelos/"
    "osteosarcoma_efficientnet_b0_baseline_v1.pt"
)

OUTPUT_ROOT = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "04_reportes/"
    "experimentos_osteosarcoma"
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

CLASSES = [
    "no_osteosarcoma",
    "osteosarcoma",
]


# ============================================================
# EXPERIMENTOS DE HIPERPARÁMETROS
# ============================================================

CONFIG_EXPERIMENTS = [
    {
        "id": "EXP-01",
        "optimizer": "adamw",
        "learning_rate": 1e-4,
        "batch_size": 32,
        "epochs": 5,
        "balancing": "none",
    },
    {
        "id": "EXP-02",
        "optimizer": "adamw",
        "learning_rate": 5e-5,
        "batch_size": 32,
        "epochs": 5,
        "balancing": "none",
    },
    {
        "id": "EXP-03",
        "optimizer": "adamw",
        "learning_rate": 1e-4,
        "batch_size": 16,
        "epochs": 5,
        "balancing": "none",
    },
    {
        "id": "EXP-04",
        "optimizer": "adam",
        "learning_rate": 1e-4,
        "batch_size": 32,
        "epochs": 5,
        "balancing": "none",
    },
    {
        "id": "EXP-05",
        "optimizer": "sgd",
        "learning_rate": 1e-3,
        "batch_size": 32,
        "epochs": 5,
        "balancing": "none",
    },
    {
        "id": "EXP-06",
        "optimizer": "adamw",
        "learning_rate": 1e-4,
        "batch_size": 32,
        "epochs": 3,
        "balancing": "none",
    },
]


# ============================================================
# UTILIDADES
# ============================================================

def seed_everything(
    seed: int,
) -> None:

    random.seed(seed)

    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(
            seed
        )


def timestamp() -> str:

    return (
        datetime.now()
        .astimezone()
        .isoformat()
    )


def json_save(
    path: Path,
    data,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================
# DATASET
# ============================================================

class TumorDataset(Dataset):

    def __init__(
        self,
        csv_path: Path,
        transform,
    ):
        self.data = pd.read_csv(
            csv_path
        )

        self.transform = transform

    def __len__(self):
        return len(
            self.data
        )

    def __getitem__(
        self,
        index: int,
    ):

        row = self.data.iloc[
            index
        ]

        image_path = Path(
            str(
                row[
                    "image_path"
                ]
            )
        )

        with Image.open(
            image_path
        ) as image:

            image = image.convert(
                "RGB"
            )

        image = self.transform(
            image
        )

        label = int(
            row[
                "osteosarcoma"
            ]
        )

        return (
            image,
            label,
            index,
        )


def crear_transforms():

    train_transform = (
        transforms.Compose(
            [
                transforms.Resize(
                    (224, 224)
                ),

                transforms.RandomRotation(
                    degrees=7
                ),

                transforms.RandomAffine(
                    degrees=0,
                    translate=(
                        0.03,
                        0.03,
                    ),
                    scale=(
                        0.97,
                        1.03,
                    ),
                ),

                transforms.ColorJitter(
                    brightness=0.08,
                    contrast=0.08,
                ),

                transforms.ToTensor(),

                transforms.Normalize(
                    IMAGENET_MEAN,
                    IMAGENET_STD,
                ),
            ]
        )
    )

    eval_transform = (
        transforms.Compose(
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
    )

    return (
        train_transform,
        eval_transform,
    )


# ============================================================
# MODELO
# ============================================================

def cargar_modelo_base(
    device,
):

    checkpoint = torch.load(
        BASELINE_PATH,
        map_location="cpu",
        weights_only=False,
    )

    model = (
        models.efficientnet_b0(
            weights=None
        )
    )

    in_features = (
        model.classifier[1]
        .in_features
    )

    model.classifier[1] = (
        nn.Linear(
            in_features,
            2,
        )
    )

    model.load_state_dict(
        checkpoint[
            "state_dict"
        ]
    )

    # Congelar todo.
    for parameter in (
        model.parameters()
    ):
        parameter.requires_grad = (
            False
        )

    # Clasificador entrenable.
    for parameter in (
        model.classifier
        .parameters()
    ):
        parameter.requires_grad = (
            True
        )

    # Últimos 3 bloques EfficientNet.
    blocks = list(
        model.features.children()
    )

    for block in blocks[-3:]:

        for parameter in (
            block.parameters()
        ):
            parameter.requires_grad = (
                True
            )

    model.to(
        device
    )

    return model


# ============================================================
# MÉTRICAS
# ============================================================

def calculate_metrics(
    y_true,
    y_prob,
    threshold,
):

    y_true = np.asarray(
        y_true,
        dtype=np.int64,
    )

    y_prob = np.asarray(
        y_prob,
        dtype=np.float64,
    )

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

    try:
        roc_auc = float(
            roc_auc_score(
                y_true,
                y_prob,
            )
        )
    except ValueError:
        roc_auc = 0.0

    try:
        pr_auc = float(
            average_precision_score(
                y_true,
                y_prob,
            )
        )
    except ValueError:
        pr_auc = 0.0

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

        "recall": float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
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

        "roc_auc": (
            roc_auc
        ),

        "pr_auc": (
            pr_auc
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


def selection_score(
    metrics: dict,
) -> float:

    # Se conserva la lógica utilizada
    # durante el Fine-tuning V1.
    return float(
        metrics[
            "sensitivity"
        ] * 0.50
        +
        metrics[
            "specificity"
        ] * 0.20
        +
        metrics[
            "f1"
        ] * 0.20
        +
        metrics[
            "roc_auc"
        ] * 0.10
    )


def select_threshold(
    y_true,
    y_prob,
):

    best_threshold = 0.50

    best_metrics = None

    best_score = -1.0

    for threshold in np.arange(
        0.05,
        0.951,
        0.01,
    ):

        metrics = (
            calculate_metrics(
                y_true,
                y_prob,
                float(
                    threshold
                ),
            )
        )

        score = (
            selection_score(
                metrics
            )
        )

        if score > best_score:

            best_score = score

            best_threshold = float(
                threshold
            )

            best_metrics = (
                metrics
            )

    return (
        best_threshold,
        best_metrics,
        best_score,
    )


# ============================================================
# INFERENCIA
# ============================================================

def collect_predictions(
    model,
    loader,
    device,
    criterion,
):

    model.eval()

    y_true = []
    y_prob = []
    indices = []

    total_loss = 0.0
    total_items = 0

    with torch.no_grad():

        for (
            images,
            labels,
            batch_indices,
        ) in loader:

            images = images.to(
                device,
                non_blocking=True,
            )

            labels = labels.to(
                device,
                non_blocking=True,
            )

            with torch.amp.autocast(
                device_type=(
                    device.type
                ),
                enabled=(
                    device.type
                    == "cuda"
                ),
            ):

                logits = model(
                    images
                )

                loss = criterion(
                    logits,
                    labels,
                )

            probabilities = (
                torch.softmax(
                    logits,
                    dim=1,
                )[:, 1]
            )

            y_true.extend(
                labels
                .cpu()
                .tolist()
            )

            y_prob.extend(
                probabilities
                .float()
                .cpu()
                .tolist()
            )

            indices.extend(
                batch_indices
                .cpu()
                .tolist()
            )

            batch_size = (
                labels.size(0)
            )

            total_loss += (
                loss.item()
                * batch_size
            )

            total_items += (
                batch_size
            )

    return (
        y_true,
        y_prob,
        indices,
        (
            total_loss
            / max(
                total_items,
                1,
            )
        ),
    )


# ============================================================
# BALANCEO
# ============================================================

def obtener_class_counts(
    dataset,
):

    labels = (
        dataset.data[
            "osteosarcoma"
        ]
        .astype(int)
        .to_numpy()
    )

    counts = np.bincount(
        labels,
        minlength=2,
    )

    return (
        labels,
        counts,
    )


def crear_criterion(
    balancing,
    train_dataset,
    device,
):

    labels, counts = (
        obtener_class_counts(
            train_dataset
        )
    )

    if balancing == "weighted_loss":

        total = float(
            counts.sum()
        )

        weights = (
            total
            / (
                2.0
                * counts.astype(
                    np.float64
                )
            )
        )

        weights_tensor = torch.tensor(
            weights,
            dtype=torch.float32,
            device=device,
        )

        return (
            nn.CrossEntropyLoss(
                weight=(
                    weights_tensor
                )
            ),
            {
                "class_counts": (
                    counts.tolist()
                ),
                "class_weights": (
                    weights.tolist()
                ),
            },
        )

    return (
        nn.CrossEntropyLoss(),
        {
            "class_counts": (
                counts.tolist()
            ),
            "class_weights": None,
        },
    )


def crear_sampler(
    balancing,
    train_dataset,
):

    if balancing != (
        "weighted_sampler"
    ):
        return None

    labels, counts = (
        obtener_class_counts(
            train_dataset
        )
    )

    class_weights = (
        1.0
        / counts.astype(
            np.float64
        )
    )

    sample_weights = (
        class_weights[
            labels
        ]
    )

    return WeightedRandomSampler(
        weights=torch.tensor(
            sample_weights,
            dtype=torch.double,
        ),
        num_samples=len(
            sample_weights
        ),
        replacement=True,
    )


# ============================================================
# OPTIMIZADORES
# ============================================================

def crear_optimizer(
    name,
    parameters,
    learning_rate,
):

    name = str(
        name
    ).lower()

    if name == "adamw":

        return torch.optim.AdamW(
            parameters,
            lr=learning_rate,
            weight_decay=1e-4,
        )

    if name == "adam":

        return torch.optim.Adam(
            parameters,
            lr=learning_rate,
            weight_decay=1e-4,
        )

    if name == "sgd":

        return torch.optim.SGD(
            parameters,
            lr=learning_rate,
            momentum=0.9,
            weight_decay=1e-4,
        )

    raise ValueError(
        f"Optimizador no soportado: "
        f"{name}"
    )


# ============================================================
# GRÁFICAS
# ============================================================

def save_loss_curve(
    history,
    output_path,
):

    epochs = [
        item[
            "epoch"
        ]
        for item in history
    ]

    train_loss = [
        item[
            "train_loss"
        ]
        for item in history
    ]

    val_loss = [
        item[
            "val_loss"
        ]
        for item in history
    ]

    figure = plt.figure(
        figsize=(7, 5)
    )

    axis = figure.add_subplot(
        1,
        1,
        1,
    )

    axis.plot(
        epochs,
        train_loss,
        marker="o",
        label="Train",
    )

    axis.plot(
        epochs,
        val_loss,
        marker="o",
        label="Validation",
    )

    axis.set_xlabel(
        "Época"
    )

    axis.set_ylabel(
        "Loss"
    )

    axis.set_title(
        "Curva de pérdida"
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


def save_metric_curve(
    history,
    output_path,
):

    epochs = [
        item[
            "epoch"
        ]
        for item in history
    ]

    figure = plt.figure(
        figsize=(8, 5)
    )

    axis = figure.add_subplot(
        1,
        1,
        1,
    )

    for key, label in [
        (
            "sensitivity",
            "Sensibilidad",
        ),
        (
            "specificity",
            "Especificidad",
        ),
        (
            "f1",
            "F1",
        ),
        (
            "roc_auc",
            "ROC-AUC",
        ),
    ]:

        values = [
            item[
                key
            ]
            for item in history
        ]

        axis.plot(
            epochs,
            values,
            marker="o",
            label=label,
        )

    axis.set_xlabel(
        "Época"
    )

    axis.set_ylabel(
        "Métrica"
    )

    axis.set_ylim(
        0,
        1.02,
    )

    axis.set_title(
        "Métricas de validación"
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


def save_confusion_matrix(
    matrix,
    output_path,
):

    matrix = np.asarray(
        matrix
    )

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
        "Matriz de confusión - TEST"
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


def save_roc_curve(
    y_true,
    y_prob,
    output_path,
):

    fpr, tpr, _ = roc_curve(
        y_true,
        y_prob,
    )

    auc = roc_auc_score(
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
        "Curva ROC - TEST"
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


def save_pr_curve(
    y_true,
    y_prob,
    output_path,
):

    precision, recall, _ = (
        precision_recall_curve(
            y_true,
            y_prob,
        )
    )

    ap = (
        average_precision_score(
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
            f"AP = {ap:.4f}"
        ),
    )

    axis.set_xlabel(
        "Recall / Sensibilidad"
    )

    axis.set_ylabel(
        "Precisión"
    )

    axis.set_title(
        "Precision-Recall - TEST"
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


# ============================================================
# ENTRENAMIENTO DE UN EXPERIMENTO
# ============================================================

def run_experiment(
    config,
    datasets,
    device,
    responsable,
    stage,
):

    experiment_id = str(
        config[
            "id"
        ]
    )

    output_dir = (
        OUTPUT_ROOT
        / stage
        / experiment_id
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "=" * 80
    )

    print(
        experiment_id
    )

    print(
        "=" * 80
    )

    print(
        json.dumps(
            config,
            indent=2,
            ensure_ascii=False,
        )
    )

    train_dataset = (
        datasets[
            "train"
        ]
    )

    val_dataset = (
        datasets[
            "validation"
        ]
    )

    test_dataset = (
        datasets[
            "test"
        ]
    )

    sampler = crear_sampler(
        config[
            "balancing"
        ],
        train_dataset,
    )

    train_loader = (
        DataLoader(
            train_dataset,
            batch_size=(
                config[
                    "batch_size"
                ]
            ),
            shuffle=(
                sampler is None
            ),
            sampler=sampler,
            num_workers=0,
            pin_memory=(
                device.type
                == "cuda"
            ),
        )
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=(
            config[
                "batch_size"
            ]
        ),
        shuffle=False,
        num_workers=0,
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=(
            config[
                "batch_size"
            ]
        ),
        shuffle=False,
        num_workers=0,
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    model = cargar_modelo_base(
        device
    )

    trainable_parameters = [
        parameter
        for parameter
        in model.parameters()
        if parameter.requires_grad
    ]

    optimizer = crear_optimizer(
        config[
            "optimizer"
        ],
        trainable_parameters,
        config[
            "learning_rate"
        ],
    )

    (
        criterion,
        balancing_info,
    ) = crear_criterion(
        config[
            "balancing"
        ],
        train_dataset,
        device,
    )

    scaler = torch.amp.GradScaler(
        device.type,
        enabled=(
            device.type
            == "cuda"
        ),
    )

    best_state = None
    best_epoch = 0
    best_validation_score = -1.0

    history = []

    for epoch in range(
        1,
        int(
            config[
                "epochs"
            ]
        ) + 1,
    ):

        model.train()

        running_loss = 0.0

        processed = 0

        for (
            images,
            labels,
            _,
        ) in train_loader:

            images = images.to(
                device,
                non_blocking=True,
            )

            labels = labels.to(
                device,
                non_blocking=True,
            )

            optimizer.zero_grad(
                set_to_none=True
            )

            with torch.amp.autocast(
                device_type=(
                    device.type
                ),
                enabled=(
                    device.type
                    == "cuda"
                ),
            ):

                logits = model(
                    images
                )

                loss = criterion(
                    logits,
                    labels,
                )

            scaler.scale(
                loss
            ).backward()

            scaler.step(
                optimizer
            )

            scaler.update()

            batch_size = (
                labels.size(0)
            )

            running_loss += (
                loss.item()
                * batch_size
            )

            processed += (
                batch_size
            )

        train_loss = (
            running_loss
            / max(
                processed,
                1,
            )
        )

        (
            val_true,
            val_prob,
            _,
            val_loss,
        ) = collect_predictions(
            model,
            val_loader,
            device,
            criterion,
        )

        (
            threshold,
            val_metrics,
            val_score,
        ) = select_threshold(
            val_true,
            val_prob,
        )

        history_item = {
            "epoch": epoch,

            "train_loss": float(
                train_loss
            ),

            "val_loss": float(
                val_loss
            ),

            **val_metrics,

            "selection_score": float(
                val_score
            ),
        }

        history.append(
            history_item
        )

        print(
            f"Epoch "
            f"{epoch}/"
            f"{config['epochs']} | "
            f"train={train_loss:.4f} | "
            f"val={val_loss:.4f} | "
            f"sens="
            f"{val_metrics['sensitivity']:.4f} | "
            f"spec="
            f"{val_metrics['specificity']:.4f} | "
            f"f1="
            f"{val_metrics['f1']:.4f} | "
            f"auc="
            f"{val_metrics['roc_auc']:.4f} | "
            f"thr="
            f"{threshold:.2f}"
        )

        if (
            val_score
            > best_validation_score
        ):

            best_validation_score = (
                val_score
            )

            best_epoch = epoch

            best_state = (
                copy.deepcopy(
                    model.state_dict()
                )
            )

    if best_state is None:

        raise RuntimeError(
            "No se obtuvo un modelo."
        )

    model.load_state_dict(
        best_state
    )

    model.to(
        device
    )

    (
        val_true,
        val_prob,
        val_indices,
        val_loss,
    ) = collect_predictions(
        model,
        val_loader,
        device,
        criterion,
    )

    (
        selected_threshold,
        validation_metrics,
        validation_score,
    ) = select_threshold(
        val_true,
        val_prob,
    )

    validation_metrics[
        "loss"
    ] = float(
        val_loss
    )

    validation_metrics[
        "selection_score"
    ] = float(
        validation_score
    )

    (
        test_true,
        test_prob,
        test_indices,
        test_loss,
    ) = collect_predictions(
        model,
        test_loader,
        device,
        criterion,
    )

    test_metrics = calculate_metrics(
        test_true,
        test_prob,
        selected_threshold,
    )

    test_metrics[
        "loss"
    ] = float(
        test_loss
    )

    # ========================================================
    # GUARDAR MODELO
    # ========================================================

    model_path = (
        output_dir
        / (
            experiment_id
            + ".pt"
        )
    )

    checkpoint = {
        "architecture": (
            "efficientnet_b0"
        ),

        "family": (
            "EfficientNet"
        ),

        "experiment_id": (
            experiment_id
        ),

        "classes": (
            CLASSES
        ),

        "state_dict": {
            key: (
                value
                .detach()
                .cpu()
            )
            for key, value
            in model
            .state_dict()
            .items()
        },

        "image_size": 224,

        "threshold": float(
            selected_threshold
        ),

        "seed": SEED,

        "best_epoch": (
            best_epoch
        ),

        "optimizer": (
            config[
                "optimizer"
            ]
        ),

        "learning_rate": (
            config[
                "learning_rate"
            ]
        ),

        "batch_size": (
            config[
                "batch_size"
            ]
        ),

        "epochs": (
            config[
                "epochs"
            ]
        ),

        "balancing": (
            config[
                "balancing"
            ]
        ),

        "training_strategy": (
            "finetune_last_3_blocks"
        ),

        "parent_model": (
            BASELINE_PATH.name
        ),

        "responsable": (
            responsable
        ),

        "fecha": timestamp(),

        "validation_metrics": (
            validation_metrics
        ),

        "test_metrics": (
            test_metrics
        ),
    }

    torch.save(
        checkpoint,
        model_path,
    )

    # ========================================================
    # CONFIGURACIÓN
    # ========================================================

    configuration = {
        "experiment_id": (
            experiment_id
        ),

        "stage": (
            stage
        ),

        "dataset": {
            "train_csv": str(
                TRAIN_CSV
            ),

            "validation_csv": str(
                VALIDATION_CSV
            ),

            "test_csv": str(
                TEST_CSV
            ),

            "train_total": len(
                train_dataset
            ),

            "validation_total": len(
                val_dataset
            ),

            "test_total": len(
                test_dataset
            ),
        },

        "architecture": (
            "efficientnet_b0"
        ),

        "image_size": 224,

        "optimizer": (
            config[
                "optimizer"
            ]
        ),

        "learning_rate": (
            config[
                "learning_rate"
            ]
        ),

        "batch_size": (
            config[
                "batch_size"
            ]
        ),

        "epochs": (
            config[
                "epochs"
            ]
        ),

        "best_epoch": (
            best_epoch
        ),

        "balancing": (
            config[
                "balancing"
            ]
        ),

        "balancing_info": (
            balancing_info
        ),

        "augmentation_train_only": (
            True
        ),

        "training_strategy": (
            "finetune_last_3_blocks"
        ),

        "parent_model": (
            BASELINE_PATH.name
        ),

        "threshold_selected_from": (
            "validation"
        ),

        "selected_threshold": float(
            selected_threshold
        ),

        "selection_score": float(
            validation_score
        ),

        "responsable": (
            responsable
        ),

        "fecha": timestamp(),

        "saved_model": str(
            model_path
        ),
    }

    json_save(
        output_dir
        / "configuracion.json",
        configuration,
    )

    json_save(
        output_dir
        / "metricas_validation.json",
        validation_metrics,
    )

    json_save(
        output_dir
        / "metricas_test.json",
        test_metrics,
    )

    json_save(
        output_dir
        / "historial.json",
        history,
    )

    # ========================================================
    # CURVAS
    # ========================================================

    save_loss_curve(
        history,
        output_dir
        / "curva_loss.png",
    )

    save_metric_curve(
        history,
        output_dir
        / "curva_metricas.png",
    )

    save_confusion_matrix(
        test_metrics[
            "confusion_matrix"
        ],
        output_dir
        / "matriz_confusion_test.png",
    )

    save_roc_curve(
        test_true,
        test_prob,
        output_dir
        / "curva_roc_test.png",
    )

    save_pr_curve(
        test_true,
        test_prob,
        output_dir
        / "curva_pr_test.png",
    )

    result = {
        **configuration,

        "validation": (
            validation_metrics
        ),

        "test": (
            test_metrics
        ),
    }

    json_save(
        output_dir
        / "resultado_completo.json",
        result,
    )

    # Liberar memoria GPU entre experimentos.
    del model

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return result


# ============================================================
# RESÚMENES
# ============================================================

def result_to_row(
    result,
):

    test = (
        result[
            "test"
        ]
    )

    validation = (
        result[
            "validation"
        ]
    )

    return {
        "experiment_id": (
            result[
                "experiment_id"
            ]
        ),

        "stage": (
            result[
                "stage"
            ]
        ),

        "optimizer": (
            result[
                "optimizer"
            ]
        ),

        "learning_rate": (
            result[
                "learning_rate"
            ]
        ),

        "batch_size": (
            result[
                "batch_size"
            ]
        ),

        "epochs": (
            result[
                "epochs"
            ]
        ),

        "best_epoch": (
            result[
                "best_epoch"
            ]
        ),

        "balancing": (
            result[
                "balancing"
            ]
        ),

        "threshold": (
            result[
                "selected_threshold"
            ]
        ),

        "validation_score": (
            validation[
                "selection_score"
            ]
        ),

        "test_accuracy": (
            test[
                "accuracy"
            ]
        ),

        "test_precision": (
            test[
                "precision"
            ]
        ),

        "test_sensitivity": (
            test[
                "sensitivity"
            ]
        ),

        "test_specificity": (
            test[
                "specificity"
            ]
        ),

        "test_f1": (
            test[
                "f1"
            ]
        ),

        "test_roc_auc": (
            test[
                "roc_auc"
            ]
        ),

        "test_pr_auc": (
            test[
                "pr_auc"
            ]
        ),

        "test_fp": (
            test[
                "false_positive"
            ]
        ),

        "test_fn": (
            test[
                "false_negative"
            ]
        ),

        "fecha": (
            result[
                "fecha"
            ]
        ),

        "responsable": (
            result[
                "responsable"
            ]
        ),

        "modelo": (
            result[
                "saved_model"
            ]
        ),
    }


def save_comparison_plot(
    dataframe,
    output_path,
    title,
):

    if dataframe.empty:
        return

    labels = (
        dataframe[
            "experiment_id"
        ]
        .tolist()
    )

    x = np.arange(
        len(labels)
    )

    figure = plt.figure(
        figsize=(11, 6)
    )

    axis = figure.add_subplot(
        1,
        1,
        1,
    )

    for column, label in [
        (
            "test_sensitivity",
            "Sensibilidad",
        ),
        (
            "test_specificity",
            "Especificidad",
        ),
        (
            "test_f1",
            "F1",
        ),
        (
            "test_roc_auc",
            "ROC-AUC",
        ),
    ]:

        axis.plot(
            x,
            dataframe[
                column
            ].to_numpy(),
            marker="o",
            label=label,
        )

    axis.set_xticks(
        x
    )

    axis.set_xticklabels(
        labels,
        rotation=25,
    )

    axis.set_ylim(
        0,
        1.02,
    )

    axis.set_ylabel(
        "Valor"
    )

    axis.set_title(
        title
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


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Ejecutor controlado de "
            "experimentos EfficientNetB0 "
            "para osteosarcoma."
        )
    )

    parser.add_argument(
        "--responsable",
        default=(
            "Denilson Asis "
            "Saavedra Mamani"
        ),
    )

    parser.add_argument(
        "--solo-config",
        action="store_true",
        help=(
            "Ejecuta únicamente "
            "comparación de hiperparámetros."
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
        " EXPERIMENTOS OSTEOSARCOMA "
        "- EFFICIENTNET B0"
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

    if not BASELINE_PATH.exists():

        raise FileNotFoundError(
            f"No existe modelo base: "
            f"{BASELINE_PATH}"
        )

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

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # FASE A - HIPERPARÁMETROS
    # ========================================================

    print()
    print(
        "=" * 80
    )

    print(
        " FASE A - COMPARACIÓN "
        "DE HIPERPARÁMETROS"
    )

    print(
        "=" * 80
    )

    config_results = []

    for config in (
        CONFIG_EXPERIMENTS
    ):

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
            stage=(
                "01_configuracion"
            ),
        )

        config_results.append(
            result
        )

    config_rows = [
        result_to_row(
            result
        )
        for result
        in config_results
    ]

    config_df = pd.DataFrame(
        config_rows
    )

    config_df.to_csv(
        OUTPUT_ROOT
        / "comparacion_configuracion.csv",
        index=False,
    )

    json_save(
        OUTPUT_ROOT
        / "comparacion_configuracion.json",
        config_rows,
    )

    save_comparison_plot(
        config_df,
        OUTPUT_ROOT
        / "comparacion_configuracion.png",
        (
            "Comparación de "
            "hiperparámetros"
        ),
    )

    # IMPORTANTE:
    # selección únicamente por VALIDATION.
    best_config_result = max(
        config_results,
        key=lambda result: (
            result[
                "validation"
            ][
                "selection_score"
            ]
        ),
    )

    best_base_config = {
        "optimizer": (
            best_config_result[
                "optimizer"
            ]
        ),

        "learning_rate": (
            best_config_result[
                "learning_rate"
            ]
        ),

        "batch_size": (
            best_config_result[
                "batch_size"
            ]
        ),

        "epochs": (
            best_config_result[
                "epochs"
            ]
        ),
    }

    json_save(
        OUTPUT_ROOT
        / (
            "mejor_configuracion_"
            "validation.json"
        ),
        {
            "selected_from": (
                "validation"
            ),

            "experiment_id": (
                best_config_result[
                    "experiment_id"
                ]
            ),

            "selection_score": (
                best_config_result[
                    "validation"
                ][
                    "selection_score"
                ]
            ),

            **best_base_config,
        },
    )

    print()
    print(
        "MEJOR CONFIGURACIÓN "
        "POR VALIDATION:"
    )

    print(
        best_config_result[
            "experiment_id"
        ]
    )

    print(
        best_base_config
    )

    if args.solo_config:

        print()
        print(
            "Ejecución finalizada "
            "en --solo-config."
        )

        return

    # ========================================================
    # FASE B - BALANCEO
    # ========================================================

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

    balance_configs = [
        {
            "id": "BAL-01",
            **best_base_config,
            "balancing": "none",
        },
        {
            "id": "BAL-02",
            **best_base_config,
            "balancing": (
                "weighted_loss"
            ),
        },
        {
            "id": "BAL-03",
            **best_base_config,
            "balancing": (
                "weighted_sampler"
            ),
        },
    ]

    balance_results = []

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
            stage=(
                "02_balanceo"
            ),
        )

        balance_results.append(
            result
        )

    balance_rows = [
        result_to_row(
            result
        )
        for result
        in balance_results
    ]

    balance_df = pd.DataFrame(
        balance_rows
    )

    balance_df.to_csv(
        OUTPUT_ROOT
        / "comparacion_balanceo.csv",
        index=False,
    )

    json_save(
        OUTPUT_ROOT
        / "comparacion_balanceo.json",
        balance_rows,
    )

    save_comparison_plot(
        balance_df,
        OUTPUT_ROOT
        / "comparacion_balanceo.png",
        (
            "Comparación de "
            "técnicas de balanceo"
        ),
    )

    # Selección final:
    # únicamente VALIDATION.
    best_final = max(
        balance_results,
        key=lambda result: (
            result[
                "validation"
            ][
                "selection_score"
            ]
        ),
    )

    final_selection = {
        "criterio": (
            "selection_score "
            "calculado exclusivamente "
            "sobre validation"
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
        / (
            "configuracion_"
            "seleccionada.json"
        ),
        final_selection,
    )

    # ========================================================
    # PANEL DE ENTRENAMIENTOS - DATOS
    # ========================================================

    all_rows = (
        config_rows
        + balance_rows
    )

    panel_df = pd.DataFrame(
        all_rows
    )

    panel_df.to_csv(
        OUTPUT_ROOT
        / "panel_entrenamientos.csv",
        index=False,
    )

    json_save(
        OUTPUT_ROOT
        / "panel_entrenamientos.json",
        {
            "dataset": {
                "train_csv": str(
                    TRAIN_CSV
                ),

                "validation_csv": str(
                    VALIDATION_CSV
                ),

                "test_csv": str(
                    TEST_CSV
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
                all_rows
            ),

            "configuracion_seleccionada": (
                final_selection
            ),
        },
    )

    print()
    print(
        "=" * 80
    )

    print(
        " EXPERIMENTOS TERMINADOS"
    )

    print(
        "=" * 80
    )

    print(
        "Seleccionado:",
        final_selection[
            "experiment_id"
        ],
    )

    print(
        "Balance:",
        final_selection[
            "balancing"
        ],
    )

    print(
        "Modelo:",
        final_selection[
            "saved_model"
        ],
    )

    print(
        "Resultados:",
        OUTPUT_ROOT,
    )


if __name__ == "__main__":
    main()
