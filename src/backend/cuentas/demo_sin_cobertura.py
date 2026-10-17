"""DEMO EN-08: código sin pruebas para bajar la cobertura del 80 %. No fusionar."""


def promedio(notas):
    if not notas:
        return 0
    total = 0
    for nota in notas:
        total += nota
    return total / len(notas)


def nota_maxima(notas):
    maxima = None
    for nota in notas:
        if maxima is None or nota > maxima:
            maxima = nota
    return maxima


def nota_minima(notas):
    minima = None
    for nota in notas:
        if minima is None or nota < minima:
            minima = nota
    return minima


def literal(nota):
    if nota >= 18:
        return "AD"
    if nota >= 14:
        return "A"
    if nota >= 11:
        return "B"
    return "C"


def contar_literales(notas):
    conteo = {"AD": 0, "A": 0, "B": 0, "C": 0}
    for nota in notas:
        conteo[literal(nota)] += 1
    return conteo


def porcentaje_asistencia(presentes, total):
    if total == 0:
        return 0
    porcentaje = presentes * 100 / total
    return round(porcentaje, 1)


def resumen(notas, presentes, total):
    return {
        "promedio": promedio(notas),
        "maxima": nota_maxima(notas),
        "minima": nota_minima(notas),
        "literales": contar_literales(notas),
        "asistencia": porcentaje_asistencia(presentes, total),
    }
