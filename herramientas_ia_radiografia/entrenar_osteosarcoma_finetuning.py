from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from torch import nn
from torch.utils.data import DataLoader
from torchvision import models, transforms


SEED = 42
BATCH_SIZE = 32
EPOCHS = 5
LEARNING_RATE = 1e-4
WORKERS = 0

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

OUTPUT_PATH = Path(
    "/modelos/"
    "osteosarcoma_efficientnet_b0_finetuned_v1.pt"
)

CLASSES = [
    "no_osteosarcoma",
    "osteosarcoma",
]

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


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class TumorDataset(
    torch.utils.data.Dataset
):
    def __init__(
        self,
        csv_path: Path,
        transform,
    ):
        self.data = pd.read_csv(csv_path)
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(
        self,
        index: int,
    ):
        from PIL import Image

        row = self.data.iloc[index]

        image_path = Path(
            str(row["image_path"])
        )

        with Image.open(
            image_path
        ) as image:
            image = image.convert("RGB")

        image = self.transform(image)

        label = int(
            row["osteosarcoma"]
        )

        return image, label


def calculate_metrics(
    y_true,
    y_prob,
    threshold,
):
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
        "roc_auc": float(auc),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
        "confusion_matrix": (
            cm.tolist()
        ),
    }


def collect_predictions(
    model,
    loader,
    device,
):
    model.eval()

    y_true = []
    y_prob = []

    criterion = (
        nn.CrossEntropyLoss()
    )

    total_loss = 0.0
    total_items = 0

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
                logits = model(images)

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
                labels.cpu().tolist()
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

    return (
        y_true,
        y_prob,
        total_loss
        / max(total_items, 1),
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
        metrics = calculate_metrics(
            y_true,
            y_prob,
            float(threshold),
        )

        score = (
            metrics["sensitivity"]
            * 0.50
            +
            metrics["specificity"]
            * 0.20
            +
            metrics["f1"]
            * 0.20
            +
            metrics["roc_auc"]
            * 0.10
        )

        if score > best_score:
            best_score = score
            best_threshold = float(
                threshold
            )
            best_metrics = metrics

    return (
        best_threshold,
        best_metrics,
    )


def export_onnx(
    model,
    output_path,
    device,
):
    model.eval()
    model.to(device)

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
        str(output_path),
        input_names=["image"],
        output_names=["logits"],
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


def main():
    seed_everything(SEED)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    if device.type == "cuda":
        torch.backends.cudnn.benchmark = (
            True
        )

    print()
    print(
        "=========================================="
    )
    print(
        " OSTEOSARCOMA - FINE-TUNING V1"
    )
    print(
        "=========================================="
    )
    print(
        f"Dispositivo: {device}"
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
            f"No existe baseline: "
            f"{BASELINE_PATH}"
        )

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

    train_dataset = TumorDataset(
        TRAIN_CSV,
        train_transform,
    )

    val_dataset = TumorDataset(
        VALIDATION_CSV,
        eval_transform,
    )

    test_dataset = TumorDataset(
        TEST_CSV,
        eval_transform,
    )

    print()
    print(
        "Distribución:"
    )

    for name, dataset in [
        ("TRAIN", train_dataset),
        (
            "VALIDATION",
            val_dataset,
        ),
        ("TEST", test_dataset),
    ]:
        labels = (
            dataset.data[
                "osteosarcoma"
            ]
            .astype(int)
            .to_numpy()
        )

        print(
            f" {name}:",
            np.bincount(
                labels,
                minlength=2,
            ).tolist(),
        )

    pin_memory = (
        device.type == "cuda"
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=WORKERS,
        pin_memory=pin_memory,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=WORKERS,
        pin_memory=pin_memory,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=WORKERS,
        pin_memory=pin_memory,
    )

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
        checkpoint["state_dict"]
    )

    # Congelar todo.
    for parameter in (
        model.parameters()
    ):
        parameter.requires_grad = False

    # Clasificador entrenable.
    for parameter in (
        model.classifier.parameters()
    ):
        parameter.requires_grad = True

    # Fine-tuning:
    # últimos tres bloques.
    feature_blocks = list(
        model.features.children()
    )

    for block in (
        feature_blocks[-3:]
    ):
        for parameter in (
            block.parameters()
        ):
            parameter.requires_grad = (
                True
            )

    model.to(device)

    trainable_parameters = [
        parameter
        for parameter
        in model.parameters()
        if parameter.requires_grad
    ]

    print()
    print(
        "Baseline cargado correctamente."
    )
    print(
        "Últimos 3 bloques: DESCONGELADOS"
    )
    print(
        f"Learning rate: "
        f"{LEARNING_RATE}"
    )
    print(
        f"Epochs: {EPOCHS}"
    )
    print(
        "Balanceo: NINGUNO"
    )

    optimizer = (
        torch.optim.AdamW(
            trainable_parameters,
            lr=LEARNING_RATE,
            weight_decay=1e-4,
        )
    )

    criterion = (
        nn.CrossEntropyLoss()
    )

    scaler = torch.amp.GradScaler(
        device.type,
        enabled=(
            device.type == "cuda"
        ),
    )

    best_state = None
    best_auc = -1.0
    best_epoch = 0
    history = []

    print()
    print(
        "===== FINE-TUNING ====="
    )

    for epoch in range(
        1,
        EPOCHS + 1,
    ):
        model.train()

        running_loss = 0.0
        processed = 0

        for images, labels in (
            train_loader
        ):
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
                    device.type
                    == "cuda"
                ),
            ):
                logits = model(images)

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
            / max(processed, 1)
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
        ) = select_threshold(
            val_true,
            val_prob,
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": float(
                    train_loss
                ),
                "val_loss": float(
                    val_loss
                ),
                **metrics,
            }
        )

        print(
            f"Epoch "
            f"{epoch}/{EPOCHS} | "
            f"train={train_loss:.4f} | "
            f"val={val_loss:.4f} | "
            f"sens="
            f"{metrics['sensitivity']:.4f} | "
            f"spec="
            f"{metrics['specificity']:.4f} | "
            f"f1="
            f"{metrics['f1']:.4f} | "
            f"auc="
            f"{metrics['roc_auc']:.4f} | "
            f"thr="
            f"{threshold:.2f}"
        )

        if (
            metrics["roc_auc"]
            > best_auc
        ):
            best_auc = (
                metrics["roc_auc"]
            )

            best_epoch = epoch

            best_state = copy.deepcopy(
                model.state_dict()
            )

    if best_state is None:
        raise RuntimeError(
            "No se obtuvo modelo."
        )

    model.load_state_dict(
        best_state
    )

    model.to(device)

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
    ) = select_threshold(
        val_true,
        val_prob,
    )

    validation_metrics["loss"] = (
        float(val_loss)
    )

    print()
    print(
        f"Mejor epoch: "
        f"{best_epoch}"
    )

    print(
        "Umbral VALIDATION:",
        f"{selected_threshold:.2f}",
    )

    (
        test_true,
        test_prob,
        test_loss,
    ) = collect_predictions(
        model,
        test_loader,
        device,
    )

    test_metrics = (
        calculate_metrics(
            test_true,
            test_prob,
            selected_threshold,
        )
    )

    test_metrics["loss"] = (
        float(test_loss)
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    new_checkpoint = {
        "architecture": (
            "efficientnet_b0"
        ),
        "family": "EfficientNet",
        "version": (
            "osteosarcoma_"
            "finetuned_v1"
        ),
        "classes": CLASSES,
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
        "seed": SEED,
        "best_epoch": (
            best_epoch
        ),
        "training_strategy": (
            "finetune_last_"
            "3_blocks"
        ),
        "balancing": "none",
        "parent_model": (
            BASELINE_PATH.name
        ),
        "validation_metrics": (
            validation_metrics
        ),
        "test_metrics": (
            test_metrics
        ),
    }

    torch.save(
        new_checkpoint,
        OUTPUT_PATH,
    )

    onnx_path = (
        OUTPUT_PATH.with_suffix(
            ".onnx"
        )
    )

    json_path = (
        OUTPUT_PATH.with_suffix(
            ".json"
        )
    )

    metrics_path = (
        OUTPUT_PATH.with_suffix(
            ".metrics.json"
        )
    )

    history_path = (
        OUTPUT_PATH.with_suffix(
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
        "family": "EfficientNet",
        "version": (
            "osteosarcoma_"
            "finetuned_v1"
        ),
        "classes": CLASSES,
        "image_size": 224,
        "threshold": float(
            selected_threshold
        ),
        "seed": SEED,
        "best_epoch": (
            best_epoch
        ),
        "epochs": EPOCHS,
        "learning_rate": (
            LEARNING_RATE
        ),
        "batch_size": (
            BATCH_SIZE
        ),
        "training_strategy": (
            "finetune_last_"
            "3_blocks"
        ),
        "balancing": "none",
        "parent_model": (
            BASELINE_PATH.name
        ),
    }

    json_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    metrics_path.write_text(
        json.dumps(
            {
                "validation":
                    validation_metrics,
                "test":
                    test_metrics,
            },
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

    print()
    print(
        "=========================================="
    )
    print(
        " FINE-TUNING TERMINADO"
    )
    print(
        "=========================================="
    )

    print()
    print("VALIDATION:")
    print(
        json.dumps(
            validation_metrics,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print("TEST:")
    print(
        json.dumps(
            test_metrics,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(
        f"PT:       "
        f"{OUTPUT_PATH}"
    )
    print(
        f"ONNX:     "
        f"{onnx_path}"
    )
    print(
        f"Metadata: "
        f"{json_path}"
    )
    print(
        f"Métricas: "
        f"{metrics_path}"
    )
    print(
        f"Historial:"
        f"{history_path}"
    )


if __name__ == "__main__":
    main()
