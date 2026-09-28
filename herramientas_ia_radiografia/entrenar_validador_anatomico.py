from __future__ import annotations

import argparse
import copy
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from PIL import Image

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from torch import nn
from torch.utils.data import (
    DataLoader,
    Dataset,
    WeightedRandomSampler,
)

from torchvision import models, transforms
from torchvision.models import EfficientNet_B0_Weights


# ============================================================
# CONFIGURACIÓN
# ============================================================

CLASS_NAMES = [
    "no_admitida",
    "admitida",
]

CLASS_TO_INDEX = {
    "no_admitida": 0,
    "admitida": 1,
}

IMAGE_SIZE = 224

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


# ============================================================
# UTILIDADES
# ============================================================

def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


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


def print_section(
    title: str,
) -> None:

    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ============================================================
# DATASET
# ============================================================

class AnatomyDataset(Dataset):

    def __init__(
        self,
        csv_path: Path,
        transform=None,
    ) -> None:

        self.data = pd.read_csv(
            csv_path
        )

        self.data = self.data[
            self.data[
                "usable_for_anatomy_training"
            ] == 1
        ].copy()

        self.data = (
            self.data
            .reset_index(
                drop=True
            )
        )

        self.transform = transform

        invalid_classes = (
            set(
                self.data[
                    "anatomy_class"
                ].unique()
            )
            - set(
                CLASS_NAMES
            )
        )

        if invalid_classes:
            raise RuntimeError(
                "Clases anatómicas "
                "inesperadas: "
                f"{invalid_classes}"
            )

    def __len__(
        self,
    ) -> int:

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
            row[
                "image_path"
            ]
        )

        with Image.open(
            image_path
        ) as image:

            image = image.convert(
                "RGB"
            )

            if self.transform:
                image = self.transform(
                    image
                )

        label = CLASS_TO_INDEX[
            row[
                "anatomy_class"
            ]
        ]

        return (
            image,
            label,
        )

    def labels(
        self,
    ) -> list[int]:

        return [
            CLASS_TO_INDEX[
                value
            ]
            for value
            in self.data[
                "anatomy_class"
            ].tolist()
        ]


# ============================================================
# TRANSFORMACIONES
# ============================================================

def build_transforms():

    train_transform = (
        transforms.Compose(
            [
                transforms.Resize(
                    (
                        IMAGE_SIZE,
                        IMAGE_SIZE,
                    )
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
                    (
                        IMAGE_SIZE,
                        IMAGE_SIZE,
                    )
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
# BALANCEO
# ============================================================

def build_sampler(
    labels: list[int],
) -> WeightedRandomSampler:

    labels_array = np.asarray(
        labels
    )

    counts = np.bincount(
        labels_array,
        minlength=2,
    )

    weights = (
        1.0
        /
        np.maximum(
            counts,
            1,
        )
    )

    sample_weights = [
        weights[label]
        for label
        in labels_array
    ]

    return WeightedRandomSampler(
        weights=torch.DoubleTensor(
            sample_weights
        ),
        num_samples=len(
            sample_weights
        ),
        replacement=True,
    )


# ============================================================
# MÉTRICAS
# ============================================================

def calculate_metrics(
    y_true: list[int],
    y_prob: list[float],
    threshold: float,
) -> dict:

    y_pred = [
        1
        if probability >= threshold
        else 0
        for probability
        in y_prob
    ]

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[
            0,
            1,
        ],
    )

    tn, fp, fn, tp = (
        cm.ravel()
    )

    sensitivity = (
        tp
        / (
            tp + fn
        )
        if (
            tp + fn
        ) > 0
        else 0.0
    )

    specificity = (
        tn
        / (
            tn + fp
        )
        if (
            tn + fp
        ) > 0
        else 0.0
    )

    try:
        auc = roc_auc_score(
            y_true,
            y_prob,
        )

    except ValueError:
        auc = 0.0

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

        "roc_auc": float(
            auc
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
            cm.tolist()
        ),
    }


# ============================================================
# PREDICCIONES
# ============================================================

def collect_predictions(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> tuple[
    list[int],
    list[float],
    float,
]:

    model.eval()

    y_true = []
    y_prob = []

    total_loss = 0.0
    total_items = 0

    criterion = (
        nn.CrossEntropyLoss()
    )

    with torch.no_grad():

        for (
            images,
            labels,
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

    average_loss = (
        total_loss
        / max(
            total_items,
            1,
        )
    )

    return (
        y_true,
        y_prob,
        average_loss,
    )


# ============================================================
# UMBRAL
# ============================================================

def find_threshold(
    y_true: list[int],
    y_prob: list[float],
) -> tuple[
    float,
    dict,
]:

    candidates = []

    for threshold in np.arange(
        0.10,
        0.91,
        0.01,
    ):

        metrics = calculate_metrics(
            y_true,
            y_prob,
            float(
                threshold
            ),
        )

        # En esta barrera interesa evitar que
        # una anatomía no admitida pase hacia
        # el análisis tumoral.
        #
        # Por eso priorizamos especificidad
        # de la clase positiva "admitida"
        # y luego sensibilidad/F1.

        score = (
            metrics[
                "specificity"
            ] * 0.50
            +
            metrics[
                "sensitivity"
            ] * 0.30
            +
            metrics[
                "f1"
            ] * 0.20
        )

        candidates.append(
            (
                score,
                float(
                    threshold
                ),
                metrics,
            )
        )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    _, threshold, metrics = (
        candidates[0]
    )

    return (
        threshold,
        metrics,
    )


# ============================================================
# FINE-TUNING
# ============================================================

def classifier_only(
    model: nn.Module,
) -> None:

    for parameter in (
        model.parameters()
    ):
        parameter.requires_grad = (
            False
        )

    for parameter in (
        model.classifier.parameters()
    ):
        parameter.requires_grad = (
            True
        )


def partial_finetuning(
    model: nn.Module,
) -> None:

    for parameter in (
        model.parameters()
    ):
        parameter.requires_grad = (
            False
        )

    for parameter in (
        model.classifier.parameters()
    ):
        parameter.requires_grad = (
            True
        )

    blocks = list(
        model.features.children()
    )

    for block in blocks[
        -3:
    ]:
        for parameter in (
            block.parameters()
        ):
            parameter.requires_grad = (
                True
            )


# ============================================================
# ENTRENAMIENTO DE ETAPA
# ============================================================

def train_stage(
    *,
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    epochs: int,
    learning_rate: float,
    stage: str,
) -> tuple[
    dict,
    list[dict],
]:

    parameters = [
        parameter
        for parameter
        in model.parameters()
        if parameter.requires_grad
    ]

    optimizer = (
        torch.optim.AdamW(
            parameters,
            lr=learning_rate,
            weight_decay=1e-4,
        )
    )

    criterion = (
        nn.CrossEntropyLoss()
    )

    scaler = (
        torch.amp.GradScaler(
            device.type,
            enabled=(
                device.type
                == "cuda"
            ),
        )
    )

    best_state = None
    best_score = -1.0

    history = []

    for epoch in range(
        1,
        epochs + 1,
    ):

        model.train()

        running_loss = 0.0
        processed = 0

        for (
            images,
            labels,
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
            val_loss,
        ) = collect_predictions(
            model,
            val_loader,
            device,
        )

        (
            threshold,
            metrics,
        ) = find_threshold(
            val_true,
            val_prob,
        )

        score = (
            metrics[
                "specificity"
            ] * 0.50
            +
            metrics[
                "sensitivity"
            ] * 0.30
            +
            metrics[
                "f1"
            ] * 0.20
        )

        epoch_data = {
            "stage": stage,
            "epoch": epoch,
            "train_loss": float(
                train_loss
            ),
            "validation_loss": float(
                val_loss
            ),
            **metrics,
        }

        history.append(
            epoch_data
        )

        print(
            f"[{stage}] "
            f"Epoch {epoch}/{epochs} | "
            f"train={train_loss:.4f} | "
            f"val={val_loss:.4f} | "
            f"sens={metrics['sensitivity']:.4f} | "
            f"spec={metrics['specificity']:.4f} | "
            f"f1={metrics['f1']:.4f} | "
            f"auc={metrics['roc_auc']:.4f} | "
            f"thr={threshold:.2f}"
        )

        if score > best_score:

            best_score = score

            best_state = {
                key: value
                .detach()
                .cpu()
                .clone()
                for key, value
                in model
                .state_dict()
                .items()
            }

    if best_state is None:
        raise RuntimeError(
            "No se obtuvo un modelo válido."
        )

    return (
        best_state,
        history,
    )


# ============================================================
# EXPORTAR ONNX
# ============================================================

def export_onnx(
    model: nn.Module,
    path: Path,
    device: torch.device,
) -> None:

    model.eval()
    model.to(
        device
    )

    dummy = torch.randn(
        1,
        3,
        IMAGE_SIZE,
        IMAGE_SIZE,
        device=device,
    )

    torch.onnx.export(
        model,
        dummy,
        str(path),

        input_names=[
            "image"
        ],

        output_names=[
            "logits"
        ],

        dynamic_axes={
            "image": {
                0: "batch"
            },
            "logits": {
                0: "batch"
            },
        },

        opset_version=17,
        do_constant_folding=True,
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        type=Path,
        default=Path(
            "/datos_radiografias_san_juan_de_dios/"
            "03_particiones/anatomia_v1"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "/modelos/"
            "anatomy_validator_"
            "efficientnet_b0_v1.pt"
        ),
    )

    parser.add_argument(
        "--warmup-epochs",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--finetune-epochs",
        type=int,
        default=7,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    # Usaremos 0 porque ya tuvimos problemas
    # de shared memory con múltiples workers.
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    seed_everything(
        args.seed
    )

    # ========================================================
    # DISPOSITIVO
    # ========================================================

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print_section(
        "ENTRENAMIENTO VALIDADOR ANATÓMICO V1"
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
    # TRANSFORMS
    # ========================================================

    (
        train_transform,
        eval_transform,
    ) = build_transforms()

    # ========================================================
    # DATASETS
    # ========================================================

    train_dataset = AnatomyDataset(
        args.data
        / "train_anatomia_v1.csv",
        train_transform,
    )

    val_dataset = AnatomyDataset(
        args.data
        / "validation_anatomia_v1.csv",
        eval_transform,
    )

    test_dataset = AnatomyDataset(
        args.data
        / "test_anatomia_v1.csv",
        eval_transform,
    )

    train_labels = (
        train_dataset.labels()
    )

    print()
    print(
        "TRAIN:",
        len(
            train_dataset
        ),
        np.bincount(
            train_labels,
            minlength=2,
        ).tolist(),
    )

    print(
        "VALIDATION:",
        len(
            val_dataset
        ),
        np.bincount(
            val_dataset.labels(),
            minlength=2,
        ).tolist(),
    )

    print(
        "TEST:",
        len(
            test_dataset
        ),
        np.bincount(
            test_dataset.labels(),
            minlength=2,
        ).tolist(),
    )

    # ========================================================
    # LOADERS
    # ========================================================

    sampler = build_sampler(
        train_labels
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=(
            args.batch_size
        ),
        sampler=sampler,
        num_workers=(
            args.workers
        ),
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=(
            args.batch_size
        ),
        shuffle=False,
        num_workers=(
            args.workers
        ),
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=(
            args.batch_size
        ),
        shuffle=False,
        num_workers=(
            args.workers
        ),
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    # ========================================================
    # MODELO
    # ========================================================

    weights = (
        EfficientNet_B0_Weights.DEFAULT
    )

    model = models.efficientnet_b0(
        weights=weights
    )

    features = (
        model.classifier[1]
        .in_features
    )

    model.classifier[1] = nn.Linear(
        features,
        2,
    )

    model.to(
        device
    )

    history = []

    # ========================================================
    # WARM-UP
    # ========================================================

    print_section(
        "ETAPA 1 - WARM-UP"
    )

    classifier_only(
        model
    )

    (
        warmup_state,
        warmup_history,
    ) = train_stage(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=device,
        epochs=(
            args.warmup_epochs
        ),
        learning_rate=1e-3,
        stage="warmup",
    )

    model.load_state_dict(
        warmup_state
    )

    model.to(
        device
    )

    history.extend(
        warmup_history
    )

    # ========================================================
    # FINE-TUNING
    # ========================================================

    print_section(
        "ETAPA 2 - FINE-TUNING"
    )

    partial_finetuning(
        model
    )

    (
        finetune_state,
        finetune_history,
    ) = train_stage(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=device,
        epochs=(
            args.finetune_epochs
        ),
        learning_rate=1e-4,
        stage="finetune",
    )

    model.load_state_dict(
        finetune_state
    )

    model.to(
        device
    )

    history.extend(
        finetune_history
    )

    # ========================================================
    # UMBRAL DEFINITIVO - VALIDATION
    # ========================================================

    (
        val_true,
        val_prob,
        val_loss,
    ) = collect_predictions(
        model,
        val_loader,
        device,
    )

    (
        threshold,
        validation_metrics,
    ) = find_threshold(
        val_true,
        val_prob,
    )

    validation_metrics[
        "loss"
    ] = float(
        val_loss
    )

    # ========================================================
    # TEST - UNA SOLA VEZ
    # ========================================================

    (
        test_true,
        test_prob,
        test_loss,
    ) = collect_predictions(
        model,
        test_loader,
        device,
    )

    test_metrics = calculate_metrics(
        test_true,
        test_prob,
        threshold,
    )

    test_metrics[
        "loss"
    ] = float(
        test_loss
    )

    # ========================================================
    # GUARDAR
    # ========================================================

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = {
        "architecture": (
            "efficientnet_b0"
        ),
        "family": (
            "EfficientNet"
        ),
        "version": (
            "anatomy_validator_v1"
        ),
        "classes": (
            CLASS_NAMES
        ),
        "image_size": (
            IMAGE_SIZE
        ),
        "threshold": float(
            threshold
        ),
        "seed": (
            args.seed
        ),
        "created_at_utc": (
            utc_now()
        ),
        "validation_metrics": (
            validation_metrics
        ),
        "test_metrics": (
            test_metrics
        ),
        "state_dict": {
            key: value
            .detach()
            .cpu()
            for key, value
            in model
            .state_dict()
            .items()
        },
    }

    torch.save(
        checkpoint,
        args.output,
    )

    onnx_path = (
        args.output
        .with_suffix(
            ".onnx"
        )
    )

    metadata_path = (
        args.output
        .with_suffix(
            ".json"
        )
    )

    metrics_path = (
        args.output
        .with_suffix(
            ".metrics.json"
        )
    )

    history_path = (
        args.output
        .with_suffix(
            ".history.json"
        )
    )

    export_onnx(
        model,
        onnx_path,
        device,
    )

    metadata = {
        "architecture": (
            "efficientnet_b0"
        ),
        "family": (
            "EfficientNet"
        ),
        "version": (
            "anatomy_validator_v1"
        ),
        "classes": (
            CLASS_NAMES
        ),
        "positive_class": (
            "admitida"
        ),
        "accepted_anatomy": [
            "humerus",
            "radius",
            "ulna",
            "femur",
            "tibia",
            "fibula",
        ],
        "image_size": (
            IMAGE_SIZE
        ),
        "threshold": float(
            threshold
        ),
        "normalization": {
            "mean": (
                IMAGENET_MEAN
            ),
            "std": (
                IMAGENET_STD
            ),
        },
        "seed": (
            args.seed
        ),
        "created_at_utc": (
            utc_now()
        ),
    }

    metrics = {
        "validation": (
            validation_metrics
        ),
        "test": (
            test_metrics
        ),
    }

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    metrics_path.write_text(
        json.dumps(
            metrics,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    history_path.write_text(
        json.dumps(
            history,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    print_section(
        "ENTRENAMIENTO TERMINADO"
    )

    print(
        "Umbral:",
        f"{threshold:.2f}",
    )

    print()
    print(
        "VALIDATION:"
    )

    print(
        json.dumps(
            validation_metrics,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(
        "TEST:"
    )

    print(
        json.dumps(
            test_metrics,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(
        "PT      :",
        args.output,
    )

    print(
        "ONNX    :",
        onnx_path,
    )

    print(
        "Metadata:",
        metadata_path,
    )

    print(
        "Métricas:",
        metrics_path,
    )

    print(
        "Historial:",
        history_path,
    )


if __name__ == "__main__":
    main()
