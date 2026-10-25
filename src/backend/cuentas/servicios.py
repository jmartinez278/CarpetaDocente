"""Reglas de negocio de las cuentas: bloqueo por intentos fallidos (RN-024) e inactividad (RN-025).

Las vistas y el backend de autenticación no escriben los campos de control de la
cuenta: llaman a estas funciones. La hora se puede pasar como argumento para
probar el bloqueo sin esperar (design.md de US-001, D1).
"""

import re
import unicodedata
from datetime import datetime, timedelta

from django.contrib.auth import hashers
from django.db import transaction
from django.utils import timezone

from cuentas.models import Usuario

INTENTOS_MAXIMOS = 5
DURACION_BLOQUEO = timedelta(minutes=15)
INACTIVIDAD_MAXIMA = timedelta(minutes=60)

_CAMPOS_DE_CONTROL = ["intentos_fallidos", "bloqueado_hasta"]

# R-11 / RF-003: letras a-z (al menos dos) y un número final opcional desde el 2.
FORMATO_USUARIO = re.compile(r"^[a-z]{2,}(?:[2-9]|[1-9][0-9]+)?$")


def esta_bloqueado(usuario: Usuario, ahora: datetime | None = None) -> bool:
    """Indica si la cuenta sigue bloqueada por RN-024 en ``ahora``."""
    ahora = ahora or timezone.now()
    return usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > ahora


def sesion_vencida(ultima_actividad: float | None, ahora: datetime | None = None) -> bool:
    """Indica si la sesión superó la inactividad máxima de RN-025 (RNF-015) en ``ahora``.

    ``ultima_actividad`` es la marca de tiempo (segundos) de la última petición de la
    sesión. Vence con 60 minutos o más sin peticiones. Una sesión sin marca no vence:
    es una abierta antes del despliegue y recibe la marca en su siguiente petición.
    """
    if ultima_actividad is None:
        return False
    ahora = ahora or timezone.now()
    return ahora.timestamp() - ultima_actividad >= INACTIVIDAD_MAXIMA.total_seconds()


def aviso_de_inactividad() -> tuple[str, str]:
    """Las dos líneas del aviso de cierre por inactividad, con la duración de RN-025."""
    minutos = int(INACTIVIDAD_MAXIMA.total_seconds() // 60)
    return (
        "Tu sesión se cerró por inactividad.",
        f"Pasaron {minutos} minutos sin uso. Ingresa de nuevo para continuar.",
    )


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


def usuario_valido(usuario: str) -> bool:
    """Indica si el usuario sigue el formato de R-11 (RF-003): jperez, jperez2, jperez10.

    Solo letras a-z en minúsculas (al menos dos) y un número final opcional desde el 2.
    """
    return FORMATO_USUARIO.fullmatch(usuario) is not None


def _solo_letras(texto: str) -> str:
    """Minúsculas, sin tildes ni ñ (NFKD) y sin nada que no sea a-z."""
    sin_marcas = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z]", "", sin_marcas)


def usuario_base(nombres: str, apellidos: str) -> str:
    """Usuario de R-11 sin número: inicial del primer nombre más el primer apellido.

    "Ñahui Rosa" / "Núñez Ávila" da "nnunez".
    """
    primer_nombre = (nombres.split() or [""])[0]
    primer_apellido = (apellidos.split() or [""])[0]
    return _solo_letras(primer_nombre)[:1] + _solo_letras(primer_apellido)


def sugerir_usuario(nombres: str, apellidos: str) -> str | None:
    """Propone el usuario libre de R-11 (RF-003): la base o la base con el primer número libre.

    Compara sin distinguir mayúsculas. Devuelve ``None`` si la base tiene menos de dos letras.
    """
    base = usuario_base(nombres, apellidos)
    if len(base) < 2:
        return None
    existentes = set(
        Usuario.objects.filter(username__iregex=rf"^{base}[0-9]*$").values_list(
            "username", flat=True
        )
    )
    ocupados = {u.lower() for u in existentes}
    if base not in ocupados:
        return base
    numero = 2
    while f"{base}{numero}" in ocupados:
        numero += 1
    return f"{base}{numero}"
