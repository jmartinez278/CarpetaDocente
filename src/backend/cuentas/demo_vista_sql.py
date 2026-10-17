"""DEMO EN-08: vista con SQL armado desde request.GET para que CodeQL y Sonar lo marquen.

Vulnerable a inyección SQL a propósito. No fusionar.
"""

from django.db import connection
from django.http import JsonResponse
from django.urls import path


def buscar_usuario(request):
    nombre = request.GET.get("nombre", "")
    consulta = f"SELECT id, username FROM auth_user WHERE username = '{nombre}'"
    with connection.cursor() as cursor:
        cursor.execute(consulta)
        filas = cursor.fetchall()
    return JsonResponse({"resultados": filas})


# Ruta local para que el análisis reconozca la función como vista de Django.
urlpatterns = [path("demo-sql/", buscar_usuario)]
