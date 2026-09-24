from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, models, transforms
from torchvision.models import EfficientNet_B0_Weights


EXPECTED_CLASSES = ["no_radiografia", "radiografia"]


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_splits(targets: list[int], seed: int):
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

    return train_idx.tolist(), val_idx.tolist(), test_idx.tolist()


def evaluate(model, loader, device):
    model.eval()
    y_true: list[int] = []
    y_pred: list[int] = []
    y_prob: list[float] = []
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss()

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)
            total_loss += loss.item() * labels.size(0)

            probs = torch.softmax(logits, dim=1)
            pred = probs.argmax(dim=1)

            y_true.extend(labels.cpu().tolist())
            y_pred.extend(pred.cpu().tolist())
            y_prob.extend(probs[:, 1].cpu().tolist())

    if not y_true:
        return {
            "loss": 0.0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "confusion_matrix": [[0, 0], [0, 0]],
        }

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="binary",
        pos_label=1,
        zero_division=0,
    )

    return {
        "loss": total_loss / max(1, len(loader.dataset)),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": confusion_matrix(
            y_true,
            y_pred,
            labels=[0, 1],
        ).tolist(),
    }


def export_onnx(model: nn.Module, path: Path, device: torch.device) -> None:
    model.eval()
    model.to(device)
    dummy = torch.randn(1, 3, 224, 224, device=device)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("dataset_radiografia"))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--threshold", type=float, default=0.70)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("radiography_validator_efficientnet_b0.pt"),
    )
    args = parser.parse_args()

    seed_everything(args.seed)

    if torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    print(f"Dispositivo de entrenamiento: {device}")

    train_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(6),
            transforms.RandomAutocontrast(p=0.15),
            transforms.ToTensor(),
            transforms.Normalize(
                [0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225],
            ),
        ]
    )

    eval_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                [0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225],
            ),
        ]
    )

    base = datasets.ImageFolder(args.data)
    if base.classes != EXPECTED_CLASSES:
        raise RuntimeError(
            f"Se esperaban las carpetas {EXPECTED_CLASSES} y se encontraron {base.classes}."
        )

    train_idx, val_idx, test_idx = build_splits(base.targets, args.seed)

    train_ds = datasets.ImageFolder(args.data, transform=train_tf)
    eval_ds = datasets.ImageFolder(args.data, transform=eval_tf)

    pin_memory = device.type == "cuda"

    train_loader = DataLoader(
        Subset(train_ds, train_idx),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=pin_memory,
    )
    val_loader = DataLoader(
        Subset(eval_ds, val_idx),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory,
    )
    test_loader = DataLoader(
        Subset(eval_ds, test_idx),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory,
    )

    weights = EfficientNet_B0_Weights.DEFAULT
    model = models.efficientnet_b0(weights=weights)

    for parameter in model.features.parameters():
        parameter.requires_grad = False

    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, 2)
    model.to(device)

    optimizer = torch.optim.AdamW(
        model.classifier.parameters(),
        lr=args.lr,
        weight_decay=1e-4,
    )
    criterion = nn.CrossEntropyLoss()

    best_f1 = -1.0
    best_state = None

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * labels.size(0)

        val_metrics = evaluate(model, val_loader, device)
        train_loss = total_loss / max(1, len(train_loader.dataset))

        print(
            f"Epoch {epoch}/{args.epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_acc={val_metrics['accuracy']:.4f} | "
            f"val_f1={val_metrics['f1']:.4f}"
        )

        if val_metrics["f1"] > best_f1:
            best_f1 = val_metrics["f1"]
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

    if best_state is None:
        raise RuntimeError("No se pudo generar un modelo entrenado.")

    model.load_state_dict(best_state)
    model.to(device)

    test_metrics = evaluate(model, test_loader, device)

    checkpoint = {
        "architecture": "efficientnet_b0",
        "family": "EfficientNet",
        "classes": EXPECTED_CLASSES,
        "state_dict": best_state,
        "image_size": 224,
        "threshold": args.threshold,
        "prototype": True,
        "test_metrics": test_metrics,
        "seed": args.seed,
    }

    torch.save(checkpoint, args.output)

    onnx_path = args.output.with_suffix(".onnx")
    metadata_path = args.output.with_suffix(".json")
    metrics_path = args.output.with_suffix(".metrics.json")

    export_onnx(model, onnx_path, device)

    metadata = {
        "architecture": "efficientnet_b0",
        "family": "EfficientNet",
        "classes": EXPECTED_CLASSES,
        "image_size": 224,
        "threshold": args.threshold,
        "prototype": True,
        "seed": args.seed,
    }

    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    metrics_path.write_text(
        json.dumps(test_metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print("Entrenamiento terminado")
    print(f"Checkpoint PyTorch: {args.output.resolve()}")
    print(f"Modelo ONNX:         {onnx_path.resolve()}")
    print(f"Metadatos:           {metadata_path.resolve()}")
    print(f"Métricas:            {metrics_path.resolve()}")
    print(json.dumps(test_metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
