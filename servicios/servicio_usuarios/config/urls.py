from django.urls import path, include


urlpatterns = [

    path(
        "api/",
        include(
            "identidad.interfaces.api.urls"
        )
    ),

]