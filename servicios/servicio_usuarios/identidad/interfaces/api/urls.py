from django.urls import path

from .views.oncologo_view import (
    OncologoListCreateAPIView,
    OncologoDetailAPIView
)



urlpatterns = [

    path(
        "oncologos/",
        OncologoListCreateAPIView.as_view()
    ),


    path(
        "oncologos/<uuid:usuario_id>/",
        OncologoDetailAPIView.as_view()
    ),

]