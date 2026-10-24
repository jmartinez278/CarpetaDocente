"""Reglas de negocio de las cuentas: bloqueo temporal por intentos fallidos (RN-024).

Las vistas y el backend de autenticación no escriben los campos de control de la
cuenta: llaman a estas funciones. La hora se puede pasar como argumento para
probar el bloqueo sin esperar (design.md de US-001, D1).
"""

from datetime import datetime, timedelta

from django.contrib.auth import hashers
from django.db import transaction
from django.utils import timezone

from cuentas.models import Usuario

INTENTOS_MAXIMOS = 5
DURACION_BLOQUEO = timedelta(minutes=15)

_CAMPOS_DE_CONTROL = ["intentos_fallidos", "bloqueado_hasta"]


def esta_bloqueado(usuario: Usuario, ahora: datetime | None = None) -> bool:
    """Indica si la cuenta sigue bloqueada por RN-024 en ``ahora``."""
    ahora = ahora or timezone.now()
    return usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > ahora


def intentar_ingreso(usuario: Usuario, contrasena: str, ahora: datetime | None = None) -> bool:
    """Registra un intento de ingreso y devuelve si la cuenta puede entrar (RN-024).

    - La contraseña siempre se comprueba, también durante el bloqueo: el tiempo de
      respuesta no delata el bloqueo. Se compara contra el hash (RNF-012).
    - Durante el bloqueo nada entra, el intento no cuenta y el bloqueo no se extiende.
    - Cada contraseña incorrecta suma un intento; el quinto bloquea la cuenta 15
      minutos y deja el conteo en cero para cuando termine el bloqueo.
    - Una cuenta inactiva no entra aunque la contraseña sea correcta, y eso no
      reinicia el conteo.
    - Un ingreso correcto deja la cuenta sin intentos ni bloqueo.

    La fila de la cuenta se bloquea con ``select_for_update`` mientras se decide,
    para que dos intentos simultáneos no se pisen el conteo. El hash se calcula
    antes, fuera del bloqueo: si no, los intentos sobre una cuenta existente se
    harían en fila y el tiempo delataría que existe. Si la contraseña cambió entre
    el cálculo y el bloqueo, se vuelve a comprobar contra la vigente.
    """
    ahora = ahora or timezone.now()
    hash_comprobado = Usuario.objects.values_list("password", flat=True).get(pk=usuario.pk)
    correcta, actualizar_hash = hashers.verify_password(contrasena, hash_comprobado)
    with transaction.atomic():
        Usuario.objects.select_for_update().only("pk").get(pk=usuario.pk)
        usuario.refresh_from_db(fields=[*_CAMPOS_DE_CONTROL, "is_active", "password"])
        if usuario.password != hash_comprobado:
            correcta, actualizar_hash = hashers.verify_password(contrasena, usuario.password)

        if esta_bloqueado(usuario, ahora):
            return False
        if not correcta:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= INTENTOS_MAXIMOS:
                usuario.bloqueado_hasta = ahora + DURACION_BLOQUEO
                usuario.intentos_fallidos = 0
            usuario.save(update_fields=_CAMPOS_DE_CONTROL)
            return False
        if not usuario.is_active:
            return False
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        campos = list(_CAMPOS_DE_CONTROL)
        if actualizar_hash:
            # Como ModelBackend: un hash de un hasher anterior pasa al preferido.
            usuario.password = hashers.make_password(contrasena)
            campos.append("password")
        usuario.save(update_fields=campos)
        return True


def desbloquear(usuario: Usuario) -> bool:
    """Quita el bloqueo y los intentos acumulados de la cuenta (RN-024, panel del Administrador).

    Devuelve si cambió algo, para que el panel registre el desbloqueo solo cuando lo hubo.
    Decide con el estado vigente de la cuenta, con su fila bloqueada: una copia leída
    antes del bloqueo o dos desbloqueos simultáneos no dan un resultado equivocado.
    """
    with transaction.atomic():
        Usuario.objects.select_for_update().only("pk").get(pk=usuario.pk)
        usuario.refresh_from_db(fields=_CAMPOS_DE_CONTROL)
        if usuario.intentos_fallidos == 0 and usuario.bloqueado_hasta is None:
            return False
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.save(update_fields=_CAMPOS_DE_CONTROL)
        return True
