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

from PIL import (
    Image,
    ImageDraw,
)

from torch.utils.data import (
    DataLoader,
    Dataset,
)

from torchvision import transforms

from torchvision.models.detection import (
    FasterRCNN_ResNet50_FPN_Weights,
    fasterrcnn_resnet50_fpn,
)

from torchvision.models.detection.faster_rcnn import (
    FastRCNNPredictor,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

SEED = 42

DATA_DIR = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "03_particiones/localizacion_v1"
)

DEFAULT_OUTPUT = Path(
    "/modelos/"
    "osteosarcoma_detector_fasterrcnn_v2.pt"
)

DEFAULT_REPORT_DIR = Path(
    "/datos_radiografias_san_juan_de_dios/"
    "04_reportes/localizacion_v2"
)


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

class OsteosarcomaDetectionDataset(
    Dataset,
):

    def __init__(
        self,
        csv_path: Path,
        train: bool,
    ):
        self.data = pd.read_csv(
            csv_path
        )

        self.train = train

        self.color_transform = (
            transforms.ColorJitter(
                brightness=0.08,
                contrast=0.08,
            )
            if train
            else None
        )

        self.to_tensor = (
            transforms.ToTensor()
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
        ) as source:
            image = source.convert(
                "RGB"
            )

        width, height = image.size

        if (
            self.train
            and self.color_transform
            is not None
        ):
            image = (
                self.color_transform(
                    image
                )
            )

        image_tensor = (
            self.to_tensor(
                image
            )
        )

        x1 = float(
            row[
                "bbox_x1"
            ]
        )

        y1 = float(
            row[
                "bbox_y1"
            ]
        )

        x2 = float(
            row[
                "bbox_x2"
            ]
        )

        y2 = float(
            row[
                "bbox_y2"
            ]
        )

        x1 = max(
            0.0,
            min(
                x1,
                width - 1,
            ),
        )

        y1 = max(
            0.0,
            min(
                y1,
                height - 1,
            ),
        )

        x2 = max(
            x1 + 1.0,
            min(
                x2,
                width,
            ),
        )

        y2 = max(
            y1 + 1.0,
            min(
                y2,
                height,
            ),
        )

        boxes = torch.tensor(
            [
                [
                    x1,
                    y1,
                    x2,
                    y2,
                ]
            ],
            dtype=torch.float32,
        )

        labels = torch.tensor(
            [1],
            dtype=torch.int64,
        )

        area = (
            boxes[
                :,
                2
            ]
            - boxes[
                :,
                0
            ]
        ) * (
            boxes[
                :,
                3
            ]
            - boxes[
                :,
                1
            ]
        )

        target = {
            "boxes": boxes,

            "labels": labels,

            "image_id": torch.tensor(
                [index],
                dtype=torch.int64,
            ),

            "area": area,

            "iscrowd": torch.zeros(
                (1,),
                dtype=torch.int64,
            ),
        }

        metadata = {
            "index": int(
                index
            ),

            "image_id": str(
                row[
                    "image_id"
                ]
            ),

            "image_path": str(
                image_path
            ),

            "anatomy": str(
                row.get(
                    "anatomy",
                    "",
                )
            ),

            "width": int(
                width
            ),

            "height": int(
                height
            ),
        }

        return (
            image_tensor,
            target,
            metadata,
        )


def collate_fn(
    batch,
):
    images = [
        item[0]
        for item in batch
    ]

    targets = [
        item[1]
        for item in batch
    ]

    metadata = [
        item[2]
        for item in batch
    ]

    return (
        images,
        targets,
        metadata,
    )


# ============================================================
# MODELO
# ============================================================

def crear_modelo(
    pretrained: bool,
):
    if pretrained:
        weights = (
            FasterRCNN_ResNet50_FPN_Weights
            .DEFAULT
        )
    else:
        weights = None

    model = (
        fasterrcnn_resnet50_fpn(
            weights=weights,
            min_size=512,
            max_size=768,
        )
    )

    in_features = (
        model
        .roi_heads
        .box_predictor
        .cls_score
        .in_features
    )

    model.roi_heads.box_predictor = (
        FastRCNNPredictor(
            in_features,
            2,
        )
    )

    return model


# ============================================================
# IOU
# ============================================================

def calculate_iou(
    box_a,
    box_b,
):
    ax1, ay1, ax2, ay2 = [
        float(value)
        for value in box_a
    ]

    bx1, by1, bx2, by2 = [
        float(value)
        for value in box_b
    ]

    intersection_x1 = max(
        ax1,
        bx1,
    )

    intersection_y1 = max(
        ay1,
        by1,
    )

    intersection_x2 = min(
        ax2,
        bx2,
    )

    intersection_y2 = min(
        ay2,
        by2,
    )

    intersection_width = max(
        0.0,
        intersection_x2
        - intersection_x1,
    )

    intersection_height = max(
        0.0,
        intersection_y2
        - intersection_y1,
    )

    intersection = (
        intersection_width
        * intersection_height
    )

    area_a = max(
        0.0,
        ax2 - ax1,
    ) * max(
        0.0,
        ay2 - ay1,
    )

    area_b = max(
        0.0,
        bx2 - bx1,
    ) * max(
        0.0,
        by2 - by1,
    )

    union = (
        area_a
        + area_b
        - intersection
    )

    if union <= 0:
        return 0.0

    return float(
        intersection
        / union
    )


# ============================================================
# EVALUACIÓN
# ============================================================

def evaluar(
    model,
    loader,
    device,
):
    model.eval()

    records = []

    with torch.no_grad():

        for (
            images,
            targets,
            metadata,
        ) in loader:

            images_device = [
                image.to(
                    device
                )
                for image
                in images
            ]

            outputs = model(
                images_device
            )

            for (
                output,
                target,
                meta,
            ) in zip(
                outputs,
                targets,
                metadata,
            ):

                gt_box = (
                    target[
                        "boxes"
                    ][0]
                    .cpu()
                    .numpy()
                )

                predicted_box = None
                predicted_score = 0.0

                if (
                    len(
                        output[
                            "boxes"
                        ]
                    )
                    > 0
                ):

                    scores = (
                        output[
                            "scores"
                        ]
                        .detach()
                        .cpu()
                        .numpy()
                    )

                    best_index = int(
                        np.argmax(
                            scores
                        )
                    )

                    predicted_score = float(
                        scores[
                            best_index
                        ]
                    )

                    predicted_box = (
                        output[
                            "boxes"
                        ][
                            best_index
                        ]
                        .detach()
                        .cpu()
                        .numpy()
                    )

                if predicted_box is None:
                    iou = 0.0

                    pred_x1 = None
                    pred_y1 = None
                    pred_x2 = None
                    pred_y2 = None

                    center_error = 1.0

                else:
                    iou = calculate_iou(
                        gt_box,
                        predicted_box,
                    )

                    (
                        pred_x1,
                        pred_y1,
                        pred_x2,
                        pred_y2,
                    ) = [
                        float(value)
                        for value
                        in predicted_box
                    ]

                    gt_center_x = (
                        float(
                            gt_box[0]
                        )
                        +
                        float(
                            gt_box[2]
                        )
                    ) / 2.0

                    gt_center_y = (
                        float(
                            gt_box[1]
                        )
                        +
                        float(
                            gt_box[3]
                        )
                    ) / 2.0

                    pred_center_x = (
                        pred_x1
                        + pred_x2
                    ) / 2.0

                    pred_center_y = (
                        pred_y1
                        + pred_y2
                    ) / 2.0

                    distance = np.sqrt(
                        (
                            pred_center_x
                            - gt_center_x
                        ) ** 2
                        +
                        (
                            pred_center_y
                            - gt_center_y
                        ) ** 2
                    )

                    diagonal = np.sqrt(
                        meta[
                            "width"
                        ] ** 2
                        +
                        meta[
                            "height"
                        ] ** 2
                    )

                    center_error = float(
                        distance
                        / max(
                            diagonal,
                            1.0,
                        )
                    )

                record = {
                    "index": (
                        meta[
                            "index"
                        ]
                    ),

                    "image_id": (
                        meta[
                            "image_id"
                        ]
                    ),

                    "image_path": (
                        meta[
                            "image_path"
                        ]
                    ),

                    "anatomy": (
                        meta[
                            "anatomy"
                        ]
                    ),

                    "width": (
                        meta[
                            "width"
                        ]
                    ),

                    "height": (
                        meta[
                            "height"
                        ]
                    ),

                    "score": (
                        predicted_score
                    ),

                    "iou": float(
                        iou
                    ),

                    "center_error_norm": (
                        center_error
                    ),

                    "gt_x1": float(
                        gt_box[0]
                    ),

                    "gt_y1": float(
                        gt_box[1]
                    ),

                    "gt_x2": float(
                        gt_box[2]
                    ),

                    "gt_y2": float(
                        gt_box[3]
                    ),

                    "pred_x1": (
                        pred_x1
                    ),

                    "pred_y1": (
                        pred_y1
                    ),

                    "pred_x2": (
                        pred_x2
                    ),

                    "pred_y2": (
                        pred_y2
                    ),
                }

                records.append(
                    record
                )

    dataframe = pd.DataFrame(
        records
    )

    ious = (
        dataframe[
            "iou"
        ]
        .astype(float)
        .to_numpy()
    )

    center_errors = (
        dataframe[
            "center_error_norm"
        ]
        .astype(float)
        .to_numpy()
    )

    metrics = {
        "total": int(
            len(
                dataframe
            )
        ),

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

        "mean_center_error_norm": float(
            np.mean(
                center_errors
            )
        ),

        "median_center_error_norm": float(
            np.median(
                center_errors
            )
        ),

        "mean_detection_score": float(
            dataframe[
                "score"
            ]
            .mean()
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

    return (
        dataframe,
        metrics,
    )


# ============================================================
# VISUALIZACIÓN TEST
# ============================================================

def guardar_visualizaciones(
    dataframe: pd.DataFrame,
    output_dir: Path,
):
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for _, row in (
        dataframe.iterrows()
    ):

        image_path = Path(
            str(
                row[
                    "image_path"
                ]
            )
        )

        with Image.open(
            image_path
        ) as source:
            image = source.convert(
                "RGB"
            )

        draw = ImageDraw.Draw(
            image
        )

        line_width = max(
            4,
            int(
                min(
                    image.size
                )
                * 0.004
            ),
        )

        # Ground Truth = verde
        draw.rectangle(
            [
                (
                    float(
                        row[
                            "gt_x1"
                        ]
                    ),
                    float(
                        row[
                            "gt_y1"
                        ]
                    ),
                ),
                (
                    float(
                        row[
                            "gt_x2"
                        ]
                    ),
                    float(
                        row[
                            "gt_y2"
                        ]
                    ),
                ),
            ],
            outline=(
                0,
                255,
                0,
            ),
            width=line_width,
        )

        if pd.notna(
            row[
                "pred_x1"
            ]
        ):

            # Predicción = amarillo
            draw.rectangle(
                [
                    (
                        float(
                            row[
                                "pred_x1"
                            ]
                        ),
                        float(
                            row[
                                "pred_y1"
                            ]
                        ),
                    ),
                    (
                        float(
                            row[
                                "pred_x2"
                            ]
                        ),
                        float(
                            row[
                                "pred_y2"
                            ]
                        ),
                    ),
                ],
                outline=(
                    255,
                    215,
                    0,
                ),
                width=line_width,
            )

        output_path = (
            output_dir
            / (
                Path(
                    str(
                        row[
                            "image_id"
                        ]
                    )
                ).stem
                + (
                    f"_iou_"
                    f"{float(row['iou']):.3f}"
                    ".png"
                )
            )
        )

        image.save(
            output_path
        )


# ============================================================
# CURVA ENTRENAMIENTO
# ============================================================

def guardar_curva(
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

    val_iou = [
        item[
            "val_mean_iou"
        ]
        for item
        in history
    ]

    figure = plt.figure(
        figsize=(
            8,
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
        val_iou,
        marker="o",
        label="Validation mean IoU",
    )

    axis.set_xlabel(
        "Época"
    )

    axis.set_title(
        "Detector Faster R-CNN V2"
    )

    axis.grid(
        alpha=0.25
    )

    axis.legend()

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
# ARGUMENTOS
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=18,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.0001,
    )

    parser.add_argument(
        "--patience",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
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

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

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
        "DETECTOR OSTEOSARCOMA "
        "FASTER R-CNN V2"
    )

    print(
        "=" * 72
    )

    print(
        "Dispositivo:",
        device,
    )

    if (
        device.type
        == "cuda"
    ):
        print(
            "GPU:",
            torch.cuda.get_device_name(
                0
            ),
        )

    train_dataset = (
        OsteosarcomaDetectionDataset(
            DATA_DIR
            / "train_localizacion_v1.csv",
            train=True,
        )
    )

    validation_dataset = (
        OsteosarcomaDetectionDataset(
            DATA_DIR
            / "validation_localizacion_v1.csv",
            train=False,
        )
    )

    test_dataset = (
        OsteosarcomaDetectionDataset(
            DATA_DIR
            / "test_localizacion_v1.csv",
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
        collate_fn=collate_fn,
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=1,
        shuffle=False,
        num_workers=0,
        collate_fn=collate_fn,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=1,
        shuffle=False,
        num_workers=0,
        collate_fn=collate_fn,
    )

    model = crear_modelo(
        pretrained=True
    )

    model.to(
        device
    )

    optimizer = (
        torch.optim.AdamW(
            [
                parameter
                for parameter
                in model.parameters()
                if parameter.requires_grad
            ],
            lr=(
                args.learning_rate
            ),
            weight_decay=1e-4,
        )
    )

    scheduler = (
        torch.optim.lr_scheduler
        .ReduceLROnPlateau(
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

    best_validation_iou = -1.0

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

        processed = 0

        for (
            images,
            targets,
            _,
        ) in train_loader:

            images = [
                image.to(
                    device
                )
                for image
                in images
            ]

            targets_device = []

            for target in targets:

                targets_device.append(
                    {
                        key: (
                            value.to(
                                device
                            )
                            if isinstance(
                                value,
                                torch.Tensor,
                            )
                            else value
                        )
                        for (
                            key,
                            value,
                        )
                        in target.items()
                    }
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

                losses = model(
                    images,
                    targets_device,
                )

                loss = sum(
                    value
                    for value
                    in losses.values()
                )

            scaler.scale(
                loss
            ).backward()

            scaler.step(
                optimizer
            )

            scaler.update()

            running_loss += float(
                loss.item()
            ) * len(
                images
            )

            processed += len(
                images
            )

        train_loss = (
            running_loss
            / max(
                processed,
                1,
            )
        )

        (
            _,
            validation_metrics,
        ) = evaluar(
            model,
            validation_loader,
            device,
        )

        validation_iou = (
            validation_metrics[
                "mean_iou"
            ]
        )

        scheduler.step(
            validation_iou
        )

        history.append(
            {
                "epoch": epoch,

                "train_loss": float(
                    train_loss
                ),

                "val_mean_iou": float(
                    validation_iou
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

                "learning_rate": float(
                    optimizer
                    .param_groups[0][
                        "lr"
                    ]
                ),
            }
        )

        print(
            f"Epoch "
            f"{epoch}/"
            f"{args.epochs} | "
            f"loss="
            f"{train_loss:.4f} | "
            f"val IoU="
            f"{validation_iou:.4f} | "
            f">=0.30="
            f"{validation_metrics['iou_ge_0_30']:.4f} | "
            f">=0.50="
            f"{validation_metrics['iou_ge_0_50']:.4f} | "
            f">=0.70="
            f"{validation_metrics['iou_ge_0_70']:.4f}"
        )

        if (
            validation_iou
            >
            best_validation_iou
        ):

            best_validation_iou = (
                validation_iou
            )

            best_epoch = (
                epoch
            )

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
            "No se obtuvo modelo válido."
        )

    model.load_state_dict(
        best_state
    )

    model.to(
        device
    )

    (
        validation_dataframe,
        validation_metrics,
    ) = evaluar(
        model,
        validation_loader,
        device,
    )

    (
        test_dataframe,
        test_metrics,
    ) = evaluar(
        model,
        test_loader,
        device,
    )

    checkpoint = {
        "architecture": (
            "fasterrcnn_resnet50_fpn"
        ),

        "task": (
            "osteosarcoma_detection"
        ),

        "version": (
            "osteosarcoma_detector_v2"
        ),

        "classes": [
            "background",
            "osteosarcoma",
        ],

        "best_epoch": (
            best_epoch
        ),

        "best_validation_iou": (
            best_validation_iou
        ),

        "min_size": 512,

        "max_size": 768,

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

    validation_dataframe.to_csv(
        args.report_dir
        / "predicciones_validation.csv",
        index=False,
    )

    test_dataframe.to_csv(
        args.report_dir
        / "predicciones_test.csv",
        index=False,
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

    guardar_curva(
        history,
        args.report_dir
        / "curva_entrenamiento.png",
    )

    guardar_visualizaciones(
        test_dataframe,
        args.report_dir
        / "visualizaciones_test",
    )

    print()
    print(
        "=" * 72
    )

    print(
        "DETECTOR V2 TERMINADO"
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
