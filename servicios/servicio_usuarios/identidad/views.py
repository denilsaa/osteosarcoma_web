from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Comprueba que el microservicio y PostgreSQL
    se encuentren disponibles.
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        return JsonResponse(
            {
                "servicio": "servicio_usuarios",
                "estado": "ok",
                "base_datos": "conectada",
            },
            status=200,
        )

    except Exception:
        return JsonResponse(
            {
                "servicio": "servicio_usuarios",
                "estado": "error",
                "base_datos": "desconectada",
            },
            status=503,
        )