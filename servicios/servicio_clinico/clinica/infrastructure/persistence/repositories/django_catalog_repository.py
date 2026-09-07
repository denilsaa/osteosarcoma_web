from clinica.domain.repositories import (
    CatalogRepository,
)
from clinica.infrastructure.persistence.models import (
    Sexo,
    TipoContacto,
    TipoDocumento,
)


class DjangoCatalogRepository(
    CatalogRepository
):
    """
    Adaptador Django ORM para catálogos
    utilizados por Pacientes.
    """

    def get_patient_catalogs(
        self,
    ) -> dict:
        sexes = [
            {
                "id": item.id_sexo,
                "code": item.codigo,
                "name": item.nombre,
            }
            for item in (
                Sexo.objects
                .all()
                .order_by("nombre")
            )
        ]

        document_types = [
            {
                "id":
                    item.id_tipo_documento,
                "code":
                    item.codigo,
                "name":
                    item.nombre,
            }
            for item in (
                TipoDocumento.objects
                .all()
                .order_by("nombre")
            )
        ]

        contact_types = [
            {
                "id":
                    item.id_tipo_contacto,
                "code":
                    item.codigo,
                "name":
                    item.nombre,
            }
            for item in (
                TipoContacto.objects
                .all()
                .order_by("nombre")
            )
        ]

        return {
            "sexes":
                sexes,

            "document_types":
                document_types,

            "contact_types":
                contact_types,
        }