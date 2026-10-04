from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from PIL import Image
from torch import nn
from torch.utils.data import (
    DataLoader,
    Dataset,
)
from torchvision import (
    models,
    transforms,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

SEED = 42

DEFAULT_DATA_DIR = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "03_particiones/localizacion_v1"
)

DEFAULT_OUTPUT = Path(
    "/modelos/"
    "osteosarcoma_localizer_efficientnet_b0_v1.pt"
)

DEFAULT_REPORT_DIR = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "04_reportes/localizacion_v1"
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


# ============================================================
# SEMILLA
# ============================================================

def seed_everything(
    seed: int,
):
    random.seed(seed)

    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(
            seed
        )


# ============================================================
# DATASET
# ============================================================

class LocalizationDataset(
    Dataset
):

    def __init__(
        self,
        csv_path: Path,
        train: bool,
    ):
        self.data = pd.read_csv(
            csv_path
        )

        transforms_list = [
            transforms.Resize(
                (224, 224)
            ),
        ]

        # Solo aumentos fotométricos.
        # No alteran las coordenadas de la caja.
        if train:
            transforms_list.extend(
                [
                    transforms.ColorJitter(
                        brightness=0.08,
                        contrast=0.08,
                    ),
                ]
            )

        transforms_list.extend(
            [
                transforms.ToTensor(),

                transforms.Normalize(
                    IMAGENET_MEAN,
                    IMAGENET_STD,
                ),
            ]
        )

        self.transform = (
            transforms.Compose(
                transforms_list
            )
        )

    def __len__(
        self,
    ):
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

            image = (
                image
                .convert(
                    "RGB"
                )
            )

        tensor = self.transform(
            image
        )

        bbox = torch.tensor(
            [
                float(
                    row[
                        "bbox_x1_norm"
                    ]
                ),

                float(
                    row[
                        "bbox_y1_norm"
                    ]
                ),

                float(
                    row[
                        "bbox_x2_norm"
                    ]
                ),

                float(
                    row[
                        "bbox_y2_norm"
                    ]
                ),
            ],
            dtype=torch.float32,
        )

        return (
            tensor,
            bbox,
            index,
        )


# ============================================================
# MODELO
# ============================================================

class OsteosarcomaLocalizer(
    nn.Module
):

    def __init__(
        self,
        pretrained: bool = True,
    ):
        super().__init__()

        weights = (
            models
            .EfficientNet_B0_Weights
            .DEFAULT
            if pretrained
            else None
        )

        self.backbone = (
            models.efficientnet_b0(
                weights=weights
            )
        )

        in_features = (
            self.backbone
            .classifier[1]
            .in_features
        )

        self.backbone.classifier = (
            nn.Identity()
        )

        self.regressor = (
            nn.Sequential(
                nn.Dropout(
                    p=0.25
                ),

                nn.Linear(
                    in_features,
                    256,
                ),

                nn.ReLU(),

                nn.Dropout(
                    p=0.15
                ),

                nn.Linear(
                    256,
                    4,
                ),

                nn.Sigmoid(),
            )
        )

    def forward(
        self,
        x,
    ):
        features = (
            self.backbone(
                x
            )
        )

        raw = (
            self.regressor(
                features
            )
        )

        # Garantizar:
        # x1 <= x2
        # y1 <= y2

        x1_raw = raw[
            :,
            0,
        ]

        y1_raw = raw[
            :,
            1,
        ]

        x2_raw = raw[
            :,
            2,
        ]

        y2_raw = raw[
            :,
            3,
        ]

        x1 = torch.minimum(
            x1_raw,
            x2_raw,
        )

        x2 = torch.maximum(
            x1_raw,
            x2_raw,
        )

        y1 = torch.minimum(
            y1_raw,
            y2_raw,
        )

        y2 = torch.maximum(
            y1_raw,
            y2_raw,
        )

        return torch.stack(
            [
                x1,
                y1,
                x2,
                y2,
            ],
            dim=1,
        )


# ============================================================
# IOU
# ============================================================

def bbox_iou(
    prediction,
    target,
):
    pred_x1 = prediction[
        :,
        0,
    ]

    pred_y1 = prediction[
        :,
        1,
    ]

    pred_x2 = prediction[
        :,
        2,
    ]

    pred_y2 = prediction[
        :,
        3,
    ]

    target_x1 = target[
        :,
        0,
    ]

    target_y1 = target[
        :,
        1,
    ]

    target_x2 = target[
        :,
        2,
    ]

    target_y2 = target[
        :,
        3,
    ]

    inter_x1 = torch.maximum(
        pred_x1,
        target_x1,
    )

    inter_y1 = torch.maximum(
        pred_y1,
        target_y1,
    )

    inter_x2 = torch.minimum(
        pred_x2,
        target_x2,
    )

    inter_y2 = torch.minimum(
        pred_y2,
        target_y2,
    )

    inter_width = torch.clamp(
        inter_x2 - inter_x1,
        min=0,
    )

    inter_height = torch.clamp(
        inter_y2 - inter_y1,
        min=0,
    )

    intersection = (
        inter_width
        * inter_height
    )

    pred_area = (
        torch.clamp(
            pred_x2 - pred_x1,
            min=0,
        )
        *
        torch.clamp(
            pred_y2 - pred_y1,
            min=0,
        )
    )

    target_area = (
        torch.clamp(
            target_x2 - target_x1,
            min=0,
        )
        *
        torch.clamp(
            target_y2 - target_y1,
            min=0,
        )
    )

    union = (
        pred_area
        + target_area
        - intersection
    )

    iou = (
        intersection
        /
        torch.clamp(
            union,
            min=1e-7,
        )
    )

    return iou


# ============================================================
# LOSS
# ============================================================

class LocalizationLoss(
    nn.Module
):

    def __init__(
        self,
    ):
        super().__init__()

        self.smooth_l1 = (
            nn.SmoothL1Loss()
        )

    def forward(
        self,
        prediction,
        target,
    ):
        regression_loss = (
            self.smooth_l1(
                prediction,
                target,
            )
        )

        iou = bbox_iou(
            prediction,
            target,
        )

        iou_loss = (
            1.0
            - iou.mean()
        )

        total = (
            regression_loss
            +
            0.50
            * iou_loss
        )

        return (
            total,
            regression_loss,
            iou_loss,
        )


# ============================================================
# MÉTRICAS
# ============================================================

def evaluate_metrics(
    predictions,
    targets,
):
    predictions = np.asarray(
        predictions,
        dtype=np.float32,
    )

    targets = np.asarray(
        targets,
        dtype=np.float32,
    )

    pred_tensor = torch.tensor(
        predictions
    )

    target_tensor = torch.tensor(
        targets
    )

    ious = (
        bbox_iou(
            pred_tensor,
            target_tensor,
        )
        .numpy()
    )

    pred_center_x = (
        predictions[
            :,
            0,
        ]
        +
        predictions[
            :,
            2,
        ]
    ) / 2.0

    pred_center_y = (
        predictions[
            :,
            1,
        ]
        +
        predictions[
            :,
            3,
        ]
    ) / 2.0

    target_center_x = (
        targets[
            :,
            0,
        ]
        +
        targets[
            :,
            2,
        ]
    ) / 2.0

    target_center_y = (
        targets[
            :,
            1,
        ]
        +
        targets[
            :,
            3,
        ]
    ) / 2.0

    center_errors = np.sqrt(
        (
            pred_center_x
            -
            target_center_x
        ) ** 2
        +
        (
            pred_center_y
            -
            target_center_y
        ) ** 2
    )

    return {
        "mean_iou": float(
            np.mean(
                ious
            )
        ),

        "median_iou": float(
            np.median(
                ious
            )
        ),

        "iou_ge_0_30": float(
            np.mean(
                ious >= 0.30
            )
        ),

        "iou_ge_0_50": float(
            np.mean(
                ious >= 0.50
            )
        ),

        "iou_ge_0_70": float(
            np.mean(
                ious >= 0.70
            )
        ),

        "mean_center_error": float(
            np.mean(
                center_errors
            )
        ),

        "median_center_error": float(
            np.median(
                center_errors
            )
        ),

        "min_iou": float(
            np.min(
                ious
            )
        ),

        "max_iou": float(
            np.max(
                ious
            )
        ),
    }


# ============================================================
# EVALUACIÓN DATA LOADER
# ============================================================

def collect_predictions(
    model,
    loader,
    device,
    criterion,
):
    model.eval()

    predictions = []
    targets = []
    indices = []

    running_loss = 0.0
    running_count = 0

    with torch.no_grad():

        for (
            images,
            bbox,
            batch_indices,
        ) in loader:

            images = images.to(
                device,
                non_blocking=True,
            )

            bbox = bbox.to(
                device,
                non_blocking=True,
            )

            with torch.amp.autocast(
                device_type=device.type,
                enabled=(
                    device.type
                    == "cuda"
                ),
            ):

                output = model(
                    images
                )

                (
                    loss,
                    _,
                    _,
                ) = criterion(
                    output,
                    bbox,
                )

            batch_size = (
                images.size(0)
            )

            running_loss += (
                loss.item()
                * batch_size
            )

            running_count += (
                batch_size
            )

            predictions.extend(
                output
                .float()
                .cpu()
                .numpy()
                .tolist()
            )

            targets.extend(
                bbox
                .float()
                .cpu()
                .numpy()
                .tolist()
            )

            indices.extend(
                batch_indices
                .cpu()
                .numpy()
                .tolist()
            )

    metrics = (
        evaluate_metrics(
            predictions,
            targets,
        )
    )

    metrics[
        "loss"
    ] = float(
        running_loss
        /
        max(
            running_count,
            1,
        )
    )

    return (
        predictions,
        targets,
        indices,
        metrics,
    )


# ============================================================
# GRÁFICAS
# ============================================================

def save_history_plot(
    history,
    output_path,
):
    epochs = [
        item[
            "epoch"
        ]
        for item
        in history
    ]

    train_loss = [
        item[
            "train_loss"
        ]
        for item
        in history
    ]

    val_loss = [
        item[
            "val_loss"
        ]
        for item
        in history
    ]

    val_iou = [
        item[
            "val_mean_iou"
        ]
        for item
        in history
    ]

    figure = plt.figure(
        figsize=(
            9,
            5,
        )
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
        label="Train loss",
    )

    axis.plot(
        epochs,
        val_loss,
        marker="o",
        label="Validation loss",
    )

    axis.plot(
        epochs,
        val_iou,
        marker="o",
        label="Validation mean IoU",
    )

    axis.set_xlabel(
        "Época"
    )

    axis.set_title(
        "Entrenamiento localizador"
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

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_DIR,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=25,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--patience",
        type=int,
        default=6,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    seed_everything(
        args.seed
    )

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
        "ENTRENAMIENTO LOCALIZADOR "
        "OSTEOSARCOMA V1"
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

    train_csv = (
        args.data
        / "train_localizacion_v1.csv"
    )

    validation_csv = (
        args.data
        / "validation_localizacion_v1.csv"
    )

    test_csv = (
        args.data
        / "test_localizacion_v1.csv"
    )

    train_dataset = (
        LocalizationDataset(
            train_csv,
            train=True,
        )
    )

    validation_dataset = (
        LocalizationDataset(
            validation_csv,
            train=False,
        )
    )

    test_dataset = (
        LocalizationDataset(
            test_csv,
            train=False,
        )
    )

    print()
    print(
        "TRAIN:",
        len(
            train_dataset
        ),
    )

    print(
        "VALIDATION:",
        len(
            validation_dataset
        ),
    )

    print(
        "TEST:",
        len(
            test_dataset
        ),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(
            device.type
            == "cuda"
        ),
    )

    model = (
        OsteosarcomaLocalizer(
            pretrained=True
        )
    )

    model.to(
        device
    )

    criterion = (
        LocalizationLoss()
    )

    optimizer = (
        torch.optim.AdamW(
            model.parameters(),
            lr=args.learning_rate,
            weight_decay=1e-4,
        )
    )

    scheduler = (
        torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="max",
            factor=0.5,
            patience=2,
        )
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
    best_iou = -1.0

    epochs_without_improvement = 0

    history = []

    args.report_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    for epoch in range(
        1,
        args.epochs + 1,
    ):

        model.train()

        running_loss = 0.0
        running_count = 0

        for (
            images,
            bbox,
            _,
        ) in train_loader:

            images = images.to(
                device,
                non_blocking=True,
            )

            bbox = bbox.to(
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

                output = model(
                    images
                )

                (
                    loss,
                    _,
                    _,
                ) = criterion(
                    output,
                    bbox,
                )

            scaler.scale(
                loss
            ).backward()

            scaler.step(
                optimizer
            )

            scaler.update()

            batch_size = (
                images.size(0)
            )

            running_loss += (
                loss.item()
                * batch_size
            )

            running_count += (
                batch_size
            )

        train_loss = (
            running_loss
            /
            max(
                running_count,
                1,
            )
        )

        (
            _,
            _,
            _,
            validation_metrics,
        ) = collect_predictions(
            model,
            validation_loader,
            device,
            criterion,
        )

        val_iou = (
            validation_metrics[
                "mean_iou"
            ]
        )

        scheduler.step(
            val_iou
        )

        history_item = {
            "epoch": epoch,

            "train_loss": float(
                train_loss
            ),

            "val_loss": (
                validation_metrics[
                    "loss"
                ]
            ),

            "val_mean_iou": (
                validation_metrics[
                    "mean_iou"
                ]
            ),

            "val_median_iou": (
                validation_metrics[
                    "median_iou"
                ]
            ),

            "val_iou_ge_0_30": (
                validation_metrics[
                    "iou_ge_0_30"
                ]
            ),

            "val_iou_ge_0_50": (
                validation_metrics[
                    "iou_ge_0_50"
                ]
            ),

            "val_center_error": (
                validation_metrics[
                    "mean_center_error"
                ]
            ),

            "learning_rate": float(
                optimizer
                .param_groups[0][
                    "lr"
                ]
            ),
        }

        history.append(
            history_item
        )

        print(
            f"Epoch "
            f"{epoch}/"
            f"{args.epochs} | "
            f"train="
            f"{train_loss:.4f} | "
            f"val="
            f"{validation_metrics['loss']:.4f} | "
            f"IoU="
            f"{validation_metrics['mean_iou']:.4f} | "
            f"IoU>=0.30="
            f"{validation_metrics['iou_ge_0_30']:.4f} | "
            f"IoU>=0.50="
            f"{validation_metrics['iou_ge_0_50']:.4f}"
        )

        if val_iou > best_iou:

            best_iou = val_iou

            best_epoch = epoch

            best_state = (
                copy.deepcopy(
                    model
                    .state_dict()
                )
            )

            epochs_without_improvement = 0

        else:
            epochs_without_improvement += 1

        if (
            epochs_without_improvement
            >= args.patience
        ):

            print()
            print(
                "EARLY STOPPING"
            )

            break

    if best_state is None:
        raise RuntimeError(
            "No se obtuvo un "
            "modelo válido."
        )

    model.load_state_dict(
        best_state
    )

    model.to(
        device
    )

    (
        validation_predictions,
        validation_targets,
        validation_indices,
        validation_metrics,
    ) = collect_predictions(
        model,
        validation_loader,
        device,
        criterion,
    )

    (
        test_predictions,
        test_targets,
        test_indices,
        test_metrics,
    ) = collect_predictions(
        model,
        test_loader,
        device,
        criterion,
    )

    checkpoint = {
        "architecture": (
            "efficientnet_b0"
        ),

        "task": (
            "osteosarcoma_localization"
        ),

        "version": (
            "osteosarcoma_localizer_v1"
        ),

        "image_size": 224,

        "output": [
            "x1",
            "y1",
            "x2",
            "y2",
        ],

        "coordinates": (
            "normalized_0_1"
        ),

        "seed": args.seed,

        "best_epoch": (
            best_epoch
        ),

        "best_validation_iou": (
            best_iou
        ),

        "state_dict": {
            key: (
                value
                .detach()
                .cpu()
            )
            for (
                key,
                value,
            )
            in model
            .state_dict()
            .items()
        },

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

    (
        args.report_dir
        / "metricas_validation.json"
    ).write_text(
        json.dumps(
            validation_metrics,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (
        args.report_dir
        / "metricas_test.json"
    ).write_text(
        json.dumps(
            test_metrics,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (
        args.report_dir
        / "historial.json"
    ).write_text(
        json.dumps(
            history,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    np.savez(
        args.report_dir
        / "predicciones_test.npz",
        predictions=np.asarray(
            test_predictions,
            dtype=np.float32,
        ),
        targets=np.asarray(
            test_targets,
            dtype=np.float32,
        ),
        indices=np.asarray(
            test_indices,
            dtype=np.int64,
        ),
    )

    save_history_plot(
        history,
        args.report_dir
        / "curvas_entrenamiento.png",
    )

    print()
    print(
        "=" * 72
    )

    print(
        "ENTRENAMIENTO TERMINADO"
    )

    print(
        "=" * 72
    )

    print(
        "Mejor época:",
        best_epoch,
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
        "Modelo:",
        args.output,
    )

    print(
        "Reportes:",
        args.report_dir,
    )


if __name__ == "__main__":
    main()
