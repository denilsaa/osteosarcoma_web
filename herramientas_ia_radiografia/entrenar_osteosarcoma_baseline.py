from __future__ import annotations

import argparse
import copy
import json
import random
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
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from torchvision.models import EfficientNet_B0_Weights


CLASSES = ["no_osteosarcoma", "osteosarcoma"]

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class TumorDataset(Dataset):
    def __init__(
        self,
        csv_path: Path,
        transform,
    ) -> None:
        self.data = pd.read_csv(csv_path)

        required = {
            "image_id",
            "image_path",
            "osteosarcoma",
        }

        missing = required - set(self.data.columns)

        if missing:
            raise RuntimeError(
                f"Faltan columnas en {csv_path}: {sorted(missing)}"
            )

        self.transform = transform

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int):
        row = self.data.iloc[index]

        image_path = Path(str(row["image_path"]))

        if not image_path.exists():
            raise FileNotFoundError(
                f"No existe la imagen: {image_path}"
            )

        with Image.open(image_path) as image:
            image = image.convert("RGB")

        if self.transform is not None:
            image = self.transform(image)

        label = int(row["osteosarcoma"])

        return image, label


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
            accuracy_score(y_true, y_pred)
        ),
        "precision": float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "sensitivity": float(sensitivity),
        "recall": float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "specificity": float(specificity),
        "f1": float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "roc_auc": float(roc_auc),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
        "confusion_matrix": cm.tolist(),
    }


def collect_predictions(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> tuple[list[int], list[float], float]:
    model.eval()

    y_true = []
    y_prob = []

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
                enabled=device.type == "cuda",
            ):
                logits = model(images)
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
                loss.item() * batch_size
            )

            total_items += batch_size

    average_loss = (
        total_loss /
        max(total_items, 1)
    )

    return (
        y_true,
        y_prob,
        average_loss,
    )


def select_threshold(
    y_true: list[int],
    y_prob: list[float],
) -> tuple[float, dict]:
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
            metrics["sensitivity"] * 0.50
            + metrics["specificity"] * 0.20
            + metrics["f1"] * 0.20
            + metrics["roc_auc"] * 0.10
        )

        if score > best_score:
            best_score = score
            best_threshold = float(threshold)
            best_metrics = metrics

    return best_threshold, best_metrics


def export_onnx(
    model: nn.Module,
    path: Path,
    device: torch.device,
) -> None:
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
        str(path),
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={
            "image": {0: "batch"},
            "logits": {0: "batch"},
        },
        opset_version=17,
        do_constant_folding=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Baseline EfficientNetB0 "
            "para osteosarcoma."
        )
    )

    parser.add_argument(
        "--train-csv",
        type=Path,
        default=Path(
            "/datos_radiografias_san_juan_de_dios/"
            "03_particiones/train_v1.csv"
        ),
    )

    parser.add_argument(
        "--validation-csv",
        type=Path,
        default=Path(
            "/datos_radiografias_san_juan_de_dios/"
            "03_particiones/validation_v1.csv"
        ),
    )

    parser.add_argument(
        "--test-csv",
        type=Path,
        default=Path(
            "/datos_radiografias_san_juan_de_dios/"
            "03_particiones/test_v1.csv"
        ),
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
    )

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

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "/modelos/"
            "osteosarcoma_efficientnet_b0_"
            "baseline_v1.pt"
        ),
    )

    args = parser.parse_args()

    seed_everything(args.seed)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True

    print()
    print(
        "=========================================="
    )
    print(
        " BASELINE OSTEOSARCOMA - EFFICIENTNET B0"
    )
    print(
        "=========================================="
    )
    print(f"Dispositivo: {device}")

    if device.type == "cuda":
        print(
            "GPU:",
            torch.cuda.get_device_name(0),
        )

    train_transform = transforms.Compose(
        [
            transforms.Resize(
                (224, 224)
            ),
            transforms.RandomRotation(
                degrees=7
            ),
            transforms.RandomAffine(
                degrees=0,
                translate=(0.03, 0.03),
                scale=(0.97, 1.03),
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

    eval_transform = transforms.Compose(
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

    train_dataset = TumorDataset(
        args.train_csv,
        train_transform,
    )

    val_dataset = TumorDataset(
        args.validation_csv,
        eval_transform,
    )

    test_dataset = TumorDataset(
        args.test_csv,
        eval_transform,
    )

    train_labels = (
        train_dataset.data[
            "osteosarcoma"
        ]
        .astype(int)
        .to_numpy()
    )

    val_labels = (
        val_dataset.data[
            "osteosarcoma"
        ]
        .astype(int)
        .to_numpy()
    )

    test_labels = (
        test_dataset.data[
            "osteosarcoma"
        ]
        .astype(int)
        .to_numpy()
    )

    print()
    print("Distribución:")
    print(
        " TRAIN:",
        np.bincount(
            train_labels,
            minlength=2,
        ).tolist(),
    )
    print(
        " VALIDATION:",
        np.bincount(
            val_labels,
            minlength=2,
        ).tolist(),
    )
    print(
        " TEST:",
        np.bincount(
            test_labels,
            minlength=2,
        ).tolist(),
    )

    pin_memory = device.type == "cuda"

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.workers,
        pin_memory=pin_memory,
        persistent_workers=False,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        pin_memory=pin_memory,
        persistent_workers=False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.workers,
        pin_memory=pin_memory,
        persistent_workers=False,
    )

    weights = EfficientNet_B0_Weights.DEFAULT

    model = models.efficientnet_b0(
        weights=weights
    )

    in_features = (
        model.classifier[1].in_features
    )

    model.classifier[1] = nn.Linear(
        in_features,
        2,
    )

    # TASK 5:
    # baseline = extractor congelado.
    for parameter in model.features.parameters():
        parameter.requires_grad = False

    for parameter in model.classifier.parameters():
        parameter.requires_grad = True

    model.to(device)

    optimizer = torch.optim.AdamW(
        model.classifier.parameters(),
        lr=args.lr,
        weight_decay=1e-4,
    )

    criterion = nn.CrossEntropyLoss()

    scaler = torch.amp.GradScaler(
        device.type,
        enabled=device.type == "cuda",
    )

    best_state = None
    best_auc = -1.0
    best_epoch = 0
    history = []

    print()
    print(
        "===== ENTRENAMIENTO BASELINE ====="
    )
    print(
        "Feature extractor: CONGELADO"
    )
    print(
        "Balanceo: NINGUNO"
    )

    for epoch in range(
        1,
        args.epochs + 1,
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
                enabled=device.type == "cuda",
            ):
                logits = model(images)

                loss = criterion(
                    logits,
                    labels,
                )

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            batch_size = labels.size(0)

            running_loss += (
                loss.item() * batch_size
            )

            processed += batch_size

        train_loss = (
            running_loss /
            max(processed, 1)
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
            val_metrics,
        ) = select_threshold(
            val_true,
            val_prob,
        )

        epoch_data = {
            "epoch": epoch,
            "train_loss": float(
                train_loss
            ),
            "val_loss": float(
                val_loss
            ),
            **val_metrics,
        }

        history.append(epoch_data)

        print(
            f"Epoch {epoch}/{args.epochs} | "
            f"train={train_loss:.4f} | "
            f"val={val_loss:.4f} | "
            f"sens={val_metrics['sensitivity']:.4f} | "
            f"spec={val_metrics['specificity']:.4f} | "
            f"f1={val_metrics['f1']:.4f} | "
            f"auc={val_metrics['roc_auc']:.4f} | "
            f"thr={threshold:.2f}"
        )

        if (
            val_metrics["roc_auc"]
            > best_auc
        ):
            best_auc = (
                val_metrics["roc_auc"]
            )

            best_epoch = epoch

            best_state = copy.deepcopy(
                model.state_dict()
            )

    if best_state is None:
        raise RuntimeError(
            "No se obtuvo un modelo válido."
        )

    model.load_state_dict(best_state)
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

    validation_metrics["loss"] = float(
        val_loss
    )

    print()
    print(
        f"Mejor epoch: {best_epoch}"
    )
    print(
        "Umbral seleccionado SOLO con VALIDATION:",
        f"{selected_threshold:.2f}",
    )

    print()
    print(
        "===== EVALUACIÓN FINAL TEST ====="
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

    test_metrics = calculate_metrics(
        test_true,
        test_prob,
        selected_threshold,
    )

    test_metrics["loss"] = float(
        test_loss
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = {
        "architecture": "efficientnet_b0",
        "family": "EfficientNet",
        "version": (
            "osteosarcoma_baseline_v1"
        ),
        "classes": CLASSES,
        "state_dict": {
            key: value.detach().cpu()
            for key, value
            in model.state_dict().items()
        },
        "image_size": 224,
        "threshold": float(
            selected_threshold
        ),
        "seed": args.seed,
        "best_epoch": best_epoch,
        "training_strategy": (
            "classifier_only_baseline"
        ),
        "balancing": "none",
        "validation_metrics": (
            validation_metrics
        ),
        "test_metrics": test_metrics,
    }

    torch.save(
        checkpoint,
        args.output,
    )

    onnx_path = (
        args.output.with_suffix(".onnx")
    )

    metadata_path = (
        args.output.with_suffix(".json")
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
        "architecture": "efficientnet_b0",
        "family": "EfficientNet",
        "version": (
            "osteosarcoma_baseline_v1"
        ),
        "classes": CLASSES,
        "image_size": 224,
        "threshold": float(
            selected_threshold
        ),
        "seed": args.seed,
        "best_epoch": best_epoch,
        "training_strategy": (
            "classifier_only_baseline"
        ),
        "balancing": "none",
        "train_samples": int(
            len(train_dataset)
        ),
        "validation_samples": int(
            len(val_dataset)
        ),
        "test_samples": int(
            len(test_dataset)
        ),
        "train_osteosarcoma": int(
            train_labels.sum()
        ),
    }

    metrics = {
        "validation": validation_metrics,
        "test": test_metrics,
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

    print()
    print(
        "=========================================="
    )
    print(
        " BASELINE TERMINADO"
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
    print(f"PT:       {args.output}")
    print(f"ONNX:     {onnx_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Métricas: {metrics_path}")
    print(f"Historial:{history_path}")


if __name__ == "__main__":
    main()
