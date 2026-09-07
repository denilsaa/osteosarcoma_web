from django.db import connection
from rest_framework.decorators import (
    api_view,
)
from rest_framework.response import Response


@api_view(["GET"])
def health_view(
    request,
):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1;"
        )

        cursor.fetchone()

    return Response(
        {
            "service":
                "servicio_clinico",

            "status":
                "ok",

            "database":
                "connected",

            "architecture":
                "clean-ddd-ports-adapters",
        }
    )