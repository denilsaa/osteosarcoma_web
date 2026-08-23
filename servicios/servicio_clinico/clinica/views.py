from django.db import connection
from django.http import JsonResponse


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        return JsonResponse(
            {
                "servicio": "servicio_clinico",
                "estado": "ok",
                "base_datos": "conectada",
            }
        )

    except Exception:
        return JsonResponse(
            {
                "servicio": "servicio_clinico",
                "estado": "error",
                "base_datos": "desconectada",
            },
            status=503,
        )