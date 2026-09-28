from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Subset, WeightedRandomSampler
from torchvision import datasets, models, transforms
from torchvision.models import EfficientNet_B0_Weights


EXPECTED_CLASSES = [
    "no_radiografia",
    "radiografia",
]


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_splits(
    targets: list[int],
    seed: int,
):
    indices = np.arange(len(targets))
    targets_array = np.asarray(targets)

    train_idx, temp_idx = train_test_split(
        indices,
        test_size=0.30,
        random_state=seed,
        stratify=targets_array,
    )

    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=0.50,
        random_state=seed,
        stratify=targets_array[temp_idx],
    )

    return (
        train_idx.tolist(),
        val_idx.tolist(),
        test_idx.tolist(),
    )


def build_balanced_sampler(
    targets: list[int],
    train_indices: list[int],
) -> WeightedRandomSampler:
    train_targets = np.asarray(targets)[
        train_indices
    ]

    counts = np.bincount(
        train_targets,
        minlength=2,
    )

    class_weights = (
        1.0
        /
        np.maximum(
            counts,
            1,
        )
    )

    sample_weights = [
        class_weights[label]
        for label in train_targets
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


def calculate_metrics(
    y_true: list[int],
    y_prob: list[float],
    threshold: float,
) -> dict:
    y_pred = [
        1 if probability >= threshold else 0
        for probability in y_prob
    ]

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    tn, fp, fn, tp = cm.ravel()

    sensitivity = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0.0
    )

    try:
        roc_auc = roc_auc_score(
            y_true,
            y_prob,
        )
    except ValueError:
        roc_auc = 0.0

    return {
        "threshold": float(threshold),
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
            roc_auc
        ),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
        "confusion_matrix": (
            cm.tolist()
        ),
    }


def collect_predictions(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> tuple[list[int], list[float], float]:
    model.eval()

    y_true: list[int] = []
    y_prob: list[float] = []

    total_loss = 0.0
    total_items = 0

    criterion = nn.CrossEntropyLoss()

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(
                device,
                non_blocking=True,
            )

            labels = labels.to(
                device,
                non_blocking=True,
            )

            with torch.amp.autocast(
                device_type=device.type,
                enabled=(
                    device.type == "cuda"
                ),
            ):
                logits = model(
                    images
                )

                loss = criterion(
                    logits,
                    labels,
                )

            probabilities = torch.softmax(
                logits,
                dim=1,
            )[:, 1]

            y_true.extend(
                labels.cpu().tolist()
            )

            y_prob.extend(
                probabilities
                .float()
                .cpu()
                .tolist()
            )

            batch_size = labels.size(0)

            total_loss += (
                loss.item()
                *
                batch_size
            )

            total_items += batch_size

    average_loss = (
        total_loss
        /
        max(
            total_items,
            1,
        )
    )

    return (
        y_true,
        y_prob,
        average_loss,
    )


def find_threshold(
    y_true: list[int],
    y_prob: list[float],
    min_sensitivity: float,
) -> tuple[float, dict]:
    best_threshold = 0.50
    best_metrics = None

    candidate_thresholds = np.arange(
        0.05,
        0.951,
        0.01,
    )

    valid_candidates = []

    for threshold in candidate_thresholds:
        metrics = calculate_metrics(
            y_true,
            y_prob,
            float(threshold),
        )

        if (
            metrics["sensitivity"]
            >=
            min_sensitivity
        ):
            valid_candidates.append(
                (
                    metrics["specificity"],
                    metrics["f1"],
                    float(threshold),
                    metrics,
                )
            )

    if valid_candidates:
        valid_candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
            ),
            reverse=True,
        )

        _, _, best_threshold, best_metrics = (
            valid_candidates[0]
        )

        return (
            best_threshold,
            best_metrics,
        )

    fallback = []

    for threshold in candidate_thresholds:
        metrics = calculate_metrics(
            y_true,
            y_prob,
            float(threshold),
        )

        fallback.append(
            (
                metrics["sensitivity"],
                metrics["f1"],
                metrics["specificity"],
                float(threshold),
                metrics,
            )
        )

    fallback.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
        ),
        reverse=True,
    )

    (
        _,
        _,
        _,
        best_threshold,
        best_metrics,
    ) = fallback[0]

    return (
        best_threshold,
        best_metrics,
    )


def set_classifier_only(
    model: nn.Module,
) -> None:
    for parameter in model.parameters():
        parameter.requires_grad = False

    for parameter in model.classifier.parameters():
        parameter.requires_grad = True


def set_partial_finetuning(
    model: nn.Module,
) -> None:
    for parameter in model.parameters():
        parameter.requires_grad = False

    for parameter in model.classifier.parameters():
        parameter.requires_grad = True

    feature_blocks = list(
        model.features.children()
    )

    for block in feature_blocks[-3:]:
        for parameter in block.parameters():
            parameter.requires_grad = True


def train_stage(
    *,
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    epochs: int,
    lr: float,
    stage_name: str,
    min_sensitivity: float,
) -> tuple[dict, list[dict]]:
    trainable_parameters = [
        parameter
        for parameter in model.parameters()
        if parameter.requires_grad
    ]

    optimizer = torch.optim.AdamW(
        trainable_parameters,
        lr=lr,
        weight_decay=1e-4,
    )

    criterion = nn.CrossEntropyLoss()

    scaler = torch.amp.GradScaler(
        device.type,
        enabled=(
            device.type == "cuda"
        ),
    )

    best_state = None
    best_score = -1.0

    history: list[dict] = []

    for epoch in range(
        1,
        epochs + 1,
    ):
        model.train()

        running_loss = 0.0
        processed = 0

        for images, labels in train_loader:
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
                device_type=device.type,
                enabled=(
                    device.type == "cuda"
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

            batch_size = labels.size(0)

            running_loss += (
                loss.item()
                *
                batch_size
            )

            processed += batch_size

        train_loss = (
            running_loss
            /
            max(
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

        threshold, val_metrics = (
            find_threshold(
                val_true,
                val_prob,
                min_sensitivity,
            )
        )

        score = (
            val_metrics["sensitivity"]
            *
            0.60
            +
            val_metrics["specificity"]
            *
            0.25
            +
            val_metrics["f1"]
            *
            0.15
        )

        epoch_data = {
            "stage": stage_name,
            "epoch": epoch,
            "train_loss": float(
                train_loss
            ),
            "val_loss": float(
                val_loss
            ),
            "threshold": float(
                threshold
            ),
            **val_metrics,
        }

        history.append(
            epoch_data
        )

        print(
            f"[{stage_name}] "
            f"Epoch {epoch}/{epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_loss={val_loss:.4f} | "
            f"sens={val_metrics['sensitivity']:.4f} | "
            f"spec={val_metrics['specificity']:.4f} | "
            f"f1={val_metrics['f1']:.4f} | "
            f"auc={val_metrics['roc_auc']:.4f} | "
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
                in model.state_dict().items()
            }

    if best_state is None:
        raise RuntimeError(
            "No se obtuvo un estado valido "
            "durante el entrenamiento."
        )

    return (
        best_state,
        history,
    )


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
        224,
        224,
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Entrenamiento V2 del validador "
            "radiografia / no radiografia."
        )
    )

    parser.add_argument(
        "--data",
        type=Path,
        default=Path(
            "dataset_radiografia_v2"
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

    parser.add_argument(
        "--warmup-lr",
        type=float,
        default=1e-3,
    )

    parser.add_argument(
        "--finetune-lr",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--min-sensitivity",
        type=float,
        default=0.98,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "/modelos/"
            "radiography_validator_"
            "efficientnet_b0_v2.pt"
        ),
    )

    args = parser.parse_args()

    seed_everything(
        args.seed
    )

    if torch.cuda.is_available():
        device = torch.device(
            "cuda"
        )

        torch.backends.cudnn.benchmark = True

    else:
        device = torch.device(
            "cpu"
        )

    print()
    print(
        "========================================"
    )
    print(
        " ENTRENAMIENTO RADIOGRAPHY VALIDATOR V2"
    )
    print(
        "========================================"
    )

    print(
        f"Dispositivo: {device}"
    )

    if device.type == "cuda":
        print(
            "GPU: "
            f"{torch.cuda.get_device_name(0)}"
        )

        print(
            "VRAM disponible: "
            f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
        )

    print(
        f"Dataset: {args.data.resolve()}"
    )

    train_transform = transforms.Compose(
        [
            transforms.Resize(
                (
                    224,
                    224,
                )
            ),
            transforms.RandomHorizontalFlip(
                p=0.5
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
                    0.95,
                    1.05,
                ),
            ),
            transforms.RandomAutocontrast(
                p=0.20
            ),
            transforms.ToTensor(),
            transforms.Normalize(
                [
                    0.485,
                    0.456,
                    0.406,
                ],
                [
                    0.229,
                    0.224,
                    0.225,
                ],
            ),
        ]
    )

    eval_transform = transforms.Compose(
        [
            transforms.Resize(
                (
                    224,
                    224,
                )
            ),
            transforms.ToTensor(),
            transforms.Normalize(
                [
                    0.485,
                    0.456,
                    0.406,
                ],
                [
                    0.229,
                    0.224,
                    0.225,
                ],
            ),
        ]
    )

    base_dataset = datasets.ImageFolder(
        args.data
    )

    if (
        base_dataset.classes
        !=
        EXPECTED_CLASSES
    ):
        raise RuntimeError(
            "Se esperaban las clases "
            f"{EXPECTED_CLASSES} y se encontraron "
            f"{base_dataset.classes}."
        )

    (
        train_indices,
        val_indices,
        test_indices,
    ) = build_splits(
        base_dataset.targets,
        args.seed,
    )

    train_dataset = datasets.ImageFolder(
        args.data,
        transform=train_transform,
    )

    eval_dataset = datasets.ImageFolder(
        args.data,
        transform=eval_transform,
    )

    sampler = build_balanced_sampler(
        base_dataset.targets,
        train_indices,
    )

    pin_memory = (
        device.type == "cuda"
    )

    train_loader = DataLoader(
        Subset(
            train_dataset,
            train_indices,
        ),
        batch_size=args.batch_size,
        sampler=sampler,
        num_workers=args.workers,
        pin_memory=pin_memory,
        persistent_workers=(
            args.workers > 0
        ),
    )

    val_loader = DataLoader(
        Subset(
            eval_dataset,
            val_indices,
        ),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        pin_memory=pin_memory,
        persistent_workers=(
            args.workers > 0
        ),
    )

    test_loader = DataLoader(
        Subset(
            eval_dataset,
            test_indices,
        ),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        pin_memory=pin_memory,
        persistent_workers=(
            args.workers > 0
        ),
    )

    train_targets = np.asarray(
        base_dataset.targets
    )[train_indices]

    val_targets = np.asarray(
        base_dataset.targets
    )[val_indices]

    test_targets = np.asarray(
        base_dataset.targets
    )[test_indices]

    print()
    print(
        "Distribucion:"
    )

    print(
        "  TRAIN:",
        np.bincount(
            train_targets,
            minlength=2,
        ).tolist(),
    )

    print(
        "  VALIDATION:",
        np.bincount(
            val_targets,
            minlength=2,
        ).tolist(),
    )

    print(
        "  TEST:",
        np.bincount(
            test_targets,
            minlength=2,
        ).tolist(),
    )

    weights = EfficientNet_B0_Weights.DEFAULT

    model = models.efficientnet_b0(
        weights=weights
    )

    in_features = (
        model.classifier[1]
        .in_features
    )

    model.classifier[1] = nn.Linear(
        in_features,
        2,
    )

    model.to(
        device
    )

    full_history: list[dict] = []

    # ==============================================
    # ETAPA 1 - WARM-UP
    # ==============================================

    print()
    print(
        "===== ETAPA 1: WARM-UP ====="
    )

    set_classifier_only(
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
        epochs=args.warmup_epochs,
        lr=args.warmup_lr,
        stage_name="warmup",
        min_sensitivity=(
            args.min_sensitivity
        ),
    )

    model.load_state_dict(
        warmup_state
    )

    model.to(
        device
    )

    full_history.extend(
        warmup_history
    )

    # ==============================================
    # ETAPA 2 - FINE-TUNING
    # ==============================================

    print()
    print(
        "===== ETAPA 2: FINE-TUNING ====="
    )

    set_partial_finetuning(
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
        epochs=args.finetune_epochs,
        lr=args.finetune_lr,
        stage_name="finetune",
        min_sensitivity=(
            args.min_sensitivity
        ),
    )

    model.load_state_dict(
        finetune_state
    )

    model.to(
        device
    )

    full_history.extend(
        finetune_history
    )

    # ==============================================
    # UMBRAL FINAL - SOLO VALIDATION
    # ==============================================

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
        selected_threshold,
        validation_metrics,
    ) = find_threshold(
        val_true,
        val_prob,
        args.min_sensitivity,
    )

    # ==============================================
    # TEST FINAL
    # ==============================================

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
        selected_threshold,
    )

    test_metrics["loss"] = float(
        test_loss
    )

    validation_metrics["loss"] = float(
        val_loss
    )

    # ==============================================
    # GUARDADO
    # ==============================================

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
            "radiography_validator_v2"
        ),
        "classes": (
            EXPECTED_CLASSES
        ),
        "state_dict": {
            key: value
            .detach()
            .cpu()
            for key, value
            in model.state_dict().items()
        },
        "image_size": 224,
        "threshold": float(
            selected_threshold
        ),
        "prototype": True,
        "seed": args.seed,
        "minimum_validation_sensitivity": (
            args.min_sensitivity
        ),
        "validation_metrics": (
            validation_metrics
        ),
        "test_metrics": (
            test_metrics
        ),
    }

    torch.save(
        checkpoint,
        args.output,
    )

    onnx_path = (
        args.output.with_suffix(
            ".onnx"
        )
    )

    metadata_path = (
        args.output.with_suffix(
            ".json"
        )
    )

    metrics_path = (
        args.output.with_suffix(
            ".metrics.json"
        )
    )

    history_path = (
        args.output.with_suffix(
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
            "radiography_validator_v2"
        ),
        "classes": (
            EXPECTED_CLASSES
        ),
        "image_size": 224,
        "threshold": float(
            selected_threshold
        ),
        "prototype": True,
        "seed": args.seed,
        "minimum_validation_sensitivity": (
            args.min_sensitivity
        ),
    }

    all_metrics = {
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
            all_metrics,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    history_path.write_text(
        json.dumps(
            full_history,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "========================================"
    )
    print(
        " ENTRENAMIENTO V2 TERMINADO"
    )
    print(
        "========================================"
    )

    print(
        f"Umbral seleccionado: "
        f"{selected_threshold:.2f}"
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
        f"PT:       {args.output}"
    )

    print(
        f"ONNX:     {onnx_path}"
    )

    print(
        f"Metadata: {metadata_path}"
    )

    print(
        f"Metricas: {metrics_path}"
    )

    print(
        f"Historial:{history_path}"
    )

    print()
    print(
        "El modelo V1 NO fue reemplazado."
    )


if __name__ == "__main__":
    main()
