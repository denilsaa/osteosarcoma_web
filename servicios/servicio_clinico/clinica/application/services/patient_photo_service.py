from io import (
    BytesIO,
)

from pathlib import (
    Path,
)

from django.core.files.base import (
    ContentFile,
)

from django.utils.text import (
    get_valid_filename,
)

from PIL import (
    Image,
    UnidentifiedImageError,
)


class PatientPhotoService:

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    MAX_SIZE_BYTES = (
        5
        *
        1024
        *
        1024
    )


    ALLOWED_FORMATS = {
        "JPEG":
            ".jpg",

        "PNG":
            ".png",

        "WEBP":
            ".webp",
    }


    # ======================================================
    # VALIDAR
    # ======================================================

    @classmethod
    def validate_and_prepare(
        cls,
        uploaded_file,
    ) -> tuple[
        str,
        ContentFile,
    ]:

        if uploaded_file is None:

            raise ValueError(
                "Seleccione una imagen."
            )


        # ==================================================
        # TAMAÑO
        # ==================================================

        if (
            uploaded_file.size
            >
            cls.MAX_SIZE_BYTES
        ):

            raise ValueError(
                "La imagen no puede superar los 5 MB."
            )


        # ==================================================
        # LEER
        # ==================================================

        try:

            image_bytes = (
                uploaded_file.read()
            )


            uploaded_file.seek(
                0
            )


        except Exception as error:

            raise ValueError(
                "No fue posible leer la imagen."
            ) from error


        # ==================================================
        # VALIDAR IMAGEN REAL
        # ==================================================

        try:

            image = (
                Image.open(
                    BytesIO(
                        image_bytes
                    )
                )
            )


            image.verify()


            image = (
                Image.open(
                    BytesIO(
                        image_bytes
                    )
                )
            )


            image_format = (
                image.format
                or
                ""
            ).upper()


        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
        ) as error:

            raise ValueError(
                "El archivo seleccionado "
                "no es una imagen válida."
            ) from error


        # ==================================================
        # FORMATO
        # ==================================================

        if (
            image_format
            not in
            cls.ALLOWED_FORMATS
        ):

            raise ValueError(
                "Solo se permiten imágenes "
                "JPG, JPEG, PNG o WEBP."
            )


        extension = (
            cls
            .ALLOWED_FORMATS[
                image_format
            ]
        )


        # ==================================================
        # NOMBRE SEGURO
        # ==================================================

        original_stem = (
            Path(
                uploaded_file.name
            )
            .stem
        )


        safe_stem = (
            get_valid_filename(
                original_stem
            )
            or
            "foto"
        )


        filename = (
            f"{safe_stem}"
            f"{extension}"
        )


        return (
            filename,

            ContentFile(
                image_bytes
            ),
        )