"""Datos de demostración: cargar, quitar y descartar (spec datos-demostracion; EN-06, D6 a D9).

Reúne cuentas, estudiantes y asistencia; por eso va aparte de ``servicios.py``. Cada función
corre en una transacción y devuelve un resumen. Los comandos de ``management/commands`` solo
leen las opciones, piden la confirmación y escriben el resumen.

Solo nombres ficticios (RN-018): los estudiantes y las docentes salen de ``APELLIDOS`` y
``NOMBRES``.
"""

import datetime
import random
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

from actividad.models import Operacion
from actividad.servicios import registrar
from asistencia.models import Asistencia, Jornada
from cuentas.models import Usuario
from institucion import servicios
from institucion.models import AnioEscolar, Estudiante, Seccion

# Una cuenta por sección, de 1.º A a 2.º D, en formato R-11 (D8). La lista solo da los nombres:
# una cuenta es demo por ``Usuario.es_demo``, que pone la carga.
CUENTAS_DEMO = (
    "demounoa",
    "demounob",
    "demounoc",
    "demounod",
    "demodosa",
    "demodosb",
    "demodosc",
    "demodosd",
)
SECCIONES_DEMO = len(CUENTAS_DEMO)
MIN_ESTUDIANTES = 1
DIAS_DEMO = 10
HORA_TOMA = datetime.time(8)
# Llave del bloqueo de PostgreSQL que pone en fila a ``cargar_demo`` y ``quitar_demo`` (D7, D9).
BLOQUEO_DEMO = 6006
NOTA_JUSTIFICADO = "Cita médica"
# Asistió 85 %, Tarde 6 %, Faltó 6 % y Justificado 3 % (D7).
ESTADOS = (
    Asistencia.Estado.ASISTIO,
    Asistencia.Estado.TARDE,
    Asistencia.Estado.FALTO,
    Asistencia.Estado.JUSTIFICADO,
)
PESOS = (85, 6, 6, 3)

APELLIDOS = (
    "AGUILAR",
    "ALARCÓN",
    "ALVARADO",
    "CÁRDENAS",
    "CASTILLO",
    "CASTRO",
    "CHÁVEZ",
    "CONDORI",
    "CRUZ",
    "DÍAZ",
    "FLORES",
    "GARCÍA",
    "GÓMEZ",
    "GONZALES",
    "GUTIÉRREZ",
    "HUAMÁN",
    "MAMANI",
    "MEDINA",
    "MENDOZA",
    "PAREDES",
    "QUISPE",
    "RAMÍREZ",
    "RAMOS",
    "ROJAS",
    "SALAZAR",
    "SÁNCHEZ",
    "SOTO",
    "TORRES",
    "VARGAS",
    "YUPANQUI",
)
NOMBRES = (
    "ADRIÁN",
    "ALEJANDRA",
    "ANA LUCÍA",
    "ANTONELLA",
    "BRUNO",
    "CAMILA",
    "DANIELA",
    "DIEGO ALONSO",
    "EMILIA",
    "GABRIEL",
    "ISABELLA",
    "JOSÉ ANTONIO",
    "JOSÉ LUIS",
    "LUCAS",
    "LUCIANA",
    "LUIS MIGUEL",
    "MARÍA FERNANDA",
    "MATEO",
    "PAOLA",
    "ROSA",
    "SANTIAGO",
    "SEBASTIÁN",
    "SOFÍA",
    "THIAGO",
    "VALENTÍN",
    "VALERIA",
)


@dataclass
class PlanDemo:
    """Lo que ``cargar_demo`` haría, ya validado; ``planear_demo`` no escribe nada."""

    anio_escolar: AnioEscolar
    estudiantes: int
    fechas: list[datetime.date]
    cargadas: list[tuple[Seccion, str]] = field(default_factory=list)
    ya_cargadas: list[Seccion] = field(default_factory=list)

    @property
    def dias(self):
        return len(self.fechas)

    def texto(self):
        if not self.cargadas:
            return "La demostración ya está cargada: no se creó nada."
        secciones = ", ".join(servicios.texto_seccion_corto(s) for s, _ in self.cargadas)
        texto = (
            f"Secciones demo: {secciones}. {self.estudiantes} estudiantes por sección "
            f"y {self.dias} días de asistencia"
        )
        if self.dias < DIAS_DEMO:
            texto += f" (el año escolar solo tiene {self.dias} días antes de hoy)"
        return texto + "."


def _fechas(anio, hoy):
    """Hasta 10 días de lunes a viernes antes de hoy y dentro del año escolar, en orden."""
    fecha = min(hoy, datetime.date(anio + 1, 1, 1)) - datetime.timedelta(days=1)
    fechas = []
    while len(fechas) < DIAS_DEMO and fecha.year == anio:
        if fecha.weekday() < 5:
            fechas.append(fecha)
        fecha -= datetime.timedelta(days=1)
    return sorted(fechas)


def _validar_cuentas(institucion):
    ajenas = Usuario.objects.filter(username__in=CUENTAS_DEMO).exclude(
        es_demo=True, rol=Usuario.Rol.DOCENTE, institucion=institucion
    )
    nombres = sorted(ajenas.values_list("username", flat=True))
    if nombres:
        raise ValidationError(
            f"Las cuentas {', '.join(nombres)} ya existen y no son cuentas demo de esta "
            "institución: no se carga la demostración."
        )


def planear_demo(institucion, estudiantes, hoy, clave):
    """Valida la carga y dice qué secciones llenaría (D7); ``ValidationError`` si se niega."""
    if not clave:
        raise ValidationError("Falta la variable DEMO_CLAVE con la contraseña de las cuentas demo.")
    if not MIN_ESTUDIANTES <= estudiantes <= servicios.MAX_ESTUDIANTES_LISTA:
        raise ValidationError(
            f"El número de estudiantes va de {MIN_ESTUDIANTES} a {servicios.MAX_ESTUDIANTES_LISTA}."
        )
    anio_escolar = AnioEscolar.objects.filter(
        institucion=institucion, estado=AnioEscolar.Estado.ABIERTO
    ).first()
    if anio_escolar is None:
        raise ValidationError("La institución no tiene un año escolar abierto.")
    _validar_cuentas(institucion)
    plan = PlanDemo(anio_escolar, estudiantes, _fechas(anio_escolar.anio, hoy))
    secciones = Seccion.objects.filter(anio_escolar=anio_escolar).select_related("docente")
    ocupadas = []
    for seccion, usuario in zip(
        secciones.order_by("grado", "nombre")[:SECCIONES_DEMO], CUENTAS_DEMO, strict=False
    ):
        docente = seccion.docente
        if docente is not None and docente.es_demo and docente.username == usuario:
            plan.ya_cargadas.append(seccion)
        elif docente is None and not seccion.estudiantes.exists():
            plan.cargadas.append((seccion, usuario))
        else:
            ocupadas.append(servicios.texto_seccion_corto(seccion))
    if ocupadas:
        raise ValidationError(
            f"Las secciones {', '.join(ocupadas)} ya tienen docente o estudiantes: "
            "no se carga la demostración."
        )
    return plan


def _nombre_docente(azar):
    return azar.choice(
        NOMBRES
    ).title(), f"{azar.choice(APELLIDOS)} {azar.choice(APELLIDOS)}".title()


def _cuenta(usuario, institucion, clave, azar):
    """La cuenta demo de la sección: nueva, o la existente con la clave actual (D8)."""
    nombre, apellidos = _nombre_docente(azar)
    cuenta = Usuario.objects.filter(username=usuario).first()
    if cuenta is None:
        return Usuario.objects.create_user(
            username=usuario,
            password=clave,
            rol=Usuario.Rol.DOCENTE,
            institucion=institucion,
            es_demo=True,
            first_name=nombre,
            last_name=apellidos,
        )
    _poner_clave(cuenta, clave)
    return cuenta


def _poner_clave(cuenta, clave):
    """Activa la cuenta con la clave vigente y sin cambio pendiente: así se rota la clave."""
    cuenta.is_active = True
    cuenta.debe_cambiar_password = False
    cuenta.set_password(clave)
    cuenta.save()


def _lista(azar, cantidad):
    """Texto «APELLIDOS, NOMBRES» para ``servicios.importar_lista``, sin repetir estudiantes."""
    estudiantes = set()
    while len(estudiantes) < cantidad:
        apellidos = f"{azar.choice(APELLIDOS)} {azar.choice(APELLIDOS)}"
        estudiantes.add((apellidos, azar.choice(NOMBRES)))
    return "\n".join(f"{apellidos}, {nombres}" for apellidos, nombres in sorted(estudiantes))


def _asistencia(seccion, cuenta, fechas, azar):
    """Jornadas y estados con ``bulk_create``; la hora de la toma, a las 8:00 de su fecha."""
    lima = timezone.get_current_timezone()
    estudiantes = list(seccion.estudiantes.order_by("apellidos", "nombres"))
    for fecha in fechas:
        jornada = Jornada.objects.create(seccion=seccion, fecha=fecha, registrado_por=cuenta)
        estados = azar.choices(ESTADOS, weights=PESOS, k=len(estudiantes))
        Asistencia.objects.bulk_create(
            Asistencia(
                jornada=jornada,
                estudiante=estudiante,
                estado=estado,
                nota_justificacion=NOTA_JUSTIFICADO
                if estado == Asistencia.Estado.JUSTIFICADO
                else "",
            )
            for estudiante, estado in zip(estudiantes, estados, strict=True)
        )
        toma = datetime.datetime.combine(fecha, HORA_TOMA, tzinfo=lima)
        # ``auto_now_add`` y ``auto_now`` no se aplican en ``update()``.
        Jornada.objects.filter(pk=jornada.pk).update(creado_en=toma)
        Asistencia.objects.filter(jornada=jornada).update(actualizado_en=toma)


def _en_fila():
    """Una carga y un retiro a la vez esperan uno al otro hasta el fin de la transacción.

    Bloquear filas no basta: en la primera carga, el retiro no encuentra secciones demo que
    bloquear y desactivaría las cuentas que la carga acaba de confirmar.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [BLOQUEO_DEMO])


def cargar_demo(institucion, estudiantes, hoy, clave):
    """Llena las 8 primeras secciones del año ABIERTO, todo o nada (D6 a D8).

    Devuelve el ``PlanDemo`` cumplido. Cada sección usa un ``random.Random`` con semilla fija:
    la misma carga da los mismos nombres y estados.
    """
    with transaction.atomic():
        _en_fila()
        plan = planear_demo(institucion, estudiantes, hoy, clave)
        for seccion in plan.ya_cargadas:
            _poner_clave(seccion.docente, clave)
        for seccion, usuario in plan.cargadas:
            azar = random.Random(f"demo-{seccion.grado}{seccion.nombre}")  # noqa: S311
            cuenta = _cuenta(usuario, institucion, clave, azar)
            seccion.docente = cuenta
            seccion.save()
            _, errores = servicios.importar_lista_sin_registro(seccion, _lista(azar, estudiantes))
            if errores:
                raise ValidationError([error.titulo for error in errores])
            _asistencia(seccion, cuenta, plan.fechas, azar)
        # Una sola entrada para toda la carga, con el usuario vacío: la corre la consola (US-008).
        registrar(
            None,
            Operacion.DEMO_CARGADA,
            entidad="anio_escolar",
            entidad_id=plan.anio_escolar,
            detalle={
                "secciones": len(plan.cargadas),
                "estudiantes": plan.estudiantes,
                "dias": plan.dias,
            },
        )
    return plan


@dataclass
class Conteos:
    """Lo que se borra (o se borraría) de una o varias secciones."""

    estudiantes: int = 0
    jornadas: int = 0
    estados: int = 0

    def texto(self):
        return (
            f"{self.estudiantes} estudiantes, {self.jornadas} jornadas "
            f"y {self.estados} estados de asistencia"
        )


@dataclass
class ResumenQuitar(Conteos):
    secciones: int = 0
    cuentas: int = 0

    @property
    def vacio(self):
        return self.secciones == 0 and self.cuentas == 0

    def texto(self):
        if self.vacio:
            return "No hay demostración que quitar: no cambió nada."
        return (
            f"{self.secciones} secciones demo liberadas: {super().texto()}. "
            f"Cuentas demo desactivadas: {self.cuentas}."
        )


def _conteos(secciones):
    return Conteos(
        estudiantes=Estudiante.objects.filter(seccion__in=secciones).count(),
        jornadas=Jornada.objects.filter(seccion__in=secciones).count(),
        estados=Asistencia.objects.filter(jornada__seccion__in=secciones).count(),
    )


def _borrar(secciones):
    """Jornadas antes que estudiantes: ``asistencia.estudiante`` es ``RESTRICT`` (D9).

    US-020 agrega aquí las notas, antes de los estudiantes (decisión 10).
    """
    Jornada.objects.filter(seccion__in=secciones).delete()
    Estudiante.objects.filter(seccion__in=secciones).delete()


def secciones_demo():
    """Secciones de años ABIERTOS cuya docente tiene la marca ``es_demo`` (D9)."""
    return Seccion.objects.filter(
        anio_escolar__estado=AnioEscolar.Estado.ABIERTO, docente__es_demo=True
    )


def conteos_demo():
    """Lo que ``quitar_demo`` borraría y desactivaría, sin tocar nada."""
    secciones = list(secciones_demo())
    return ResumenQuitar(
        **vars(_conteos(secciones)),
        secciones=len(secciones),
        cuentas=Usuario.objects.filter(es_demo=True, is_active=True).count(),
    )


def quitar_demo():
    """Libera las secciones demo y desactiva las cuentas demo sin borrarlas (D9, RN-023).

    ``jornada.registrado_por`` es ``PROTECT``: las cuentas no se podrían borrar aunque se quisiera.
    """
    with transaction.atomic():
        _en_fila()
        secciones = list(secciones_demo().select_for_update(of=("self",)))
        resumen = conteos_demo()
        _borrar(secciones)
        for seccion in secciones:
            seccion.docente = None
            seccion.save()
        Usuario.objects.filter(es_demo=True, is_active=True).update(is_active=False)
        if not resumen.vacio:
            registrar(None, Operacion.DEMO_QUITADA, detalle=vars(resumen))
    return resumen


def conteos_seccion(seccion):
    """Lo que ``descartar_seccion`` borraría, sin tocar nada."""
    return _conteos([seccion])


def descartar_seccion(seccion):
    """Borra estudiantes, jornadas y estados de una sección del año ABIERTO; conserva la docente.

    Es el camino para borrar una lista con registros, que «Vaciar lista» no permite (D9).
    """
    with transaction.atomic():
        seccion = (
            Seccion.objects.select_for_update(of=("self",))
            .select_related("anio_escolar")
            .get(pk=seccion.pk)
        )
        if seccion.anio_escolar.estado != AnioEscolar.Estado.ABIERTO:
            raise ValidationError(
                f"El año {seccion.anio_escolar.anio} está cerrado: no se descarta "
                f"{servicios.texto_seccion_corto(seccion)}."
            )
        conteos = conteos_seccion(seccion)
        _borrar([seccion])
        registrar(
            None,
            Operacion.SECCION_DESCARTADA,
            entidad="seccion",
            entidad_id=seccion,
            detalle=vars(conteos),
        )
    return conteos
