# app/core/auditoria.py
# =========================================================
# Catálogos centrales de auditoría:
# - códigos de movimiento (dbo.Movimiento_Auditoria)
# - códigos de tabla (dbo.Tabla_Auditoria)
# - helpers para normalizar ids de fila
# =========================================================

from __future__ import annotations


class Mov:
    """
    Códigos de movimiento para dbo.Movimiento_Auditoria.
    """

    # =========================================================
    # LOGIN / SESION
    # =========================================================
    LOGIN_OK = 1
    LOGIN_FAIL = 2
    LOGOUT = 7

    # =========================================================
    # MATRICULAS / FACTURACION
    # =========================================================
    MATRICULA_CREADA = 3
    FACTURA_GENERADA = 4
    MATRICULA_ESTADO_CAMBIADO = 5
    MATRICULA_ELIMINADA = 6

    # =========================================================
    # DOCENTES
    # =========================================================
    DOCENTE_CREADO = 10
    DOCENTE_ACTUALIZADO = 11
    DOCENTE_ELIMINADO = 12

    # =========================================================
    # ESTUDIANTES
    # =========================================================
    ESTUDIANTE_CREADO = 20
    ESTUDIANTE_ACTUALIZADO = 21
    ESTUDIANTE_ELIMINADO = 22

    # =========================================================
    # PROGRAMAS / CURSOS
    # =========================================================
    PROGRAMA_CREADO = 30
    PROGRAMA_ACTUALIZADO = 31
    PROGRAMA_ELIMINADO = 32

    CURSO_CREADO = 40
    CURSO_ACTUALIZADO = 41
    CURSO_ELIMINADO = 42

    # =========================================================
    # BECAS / BECADOS
    # =========================================================
    BECA_CREADA = 50
    BECA_ACTUALIZADA = 51
    BECA_ELIMINADA = 52

    BECADO_CREADO = 60
    BECADO_ACTUALIZADO = 61
    BECADO_ELIMINADO = 62

    # =========================================================
    # MATRICULA POR MATERIA
    # =========================================================
    MATRICULA_MATERIA_CREADA = 70
    MATRICULA_MATERIA_ACTUALIZADA = 71
    MATRICULA_MATERIA_ELIMINADA = 72

    # =========================================================
    # DOCENTE ↔ MATERIA
    # =========================================================
    DOCENTE_MATERIA_CREADA = 80
    DOCENTE_MATERIA_ACTUALIZADA = 81
    DOCENTE_MATERIA_ELIMINADA = 82

    # =========================================================
    # HORARIOS DE MATERIA
    # =========================================================
    MATERIA_HORARIO_CREADO = 85
    MATERIA_HORARIO_ACTUALIZADO = 86
    MATERIA_HORARIO_ELIMINADO = 87

    # =========================================================
    # PERIODOS
    # =========================================================
    PERIODO_CREADO = 90
    PERIODO_ACTUALIZADO = 91
    PERIODO_ELIMINADO = 92

    # =========================================================
    # RESTRICCIONES / VALIDACIONES ACADEMICAS
    # =========================================================
    RESTRICCION_CARGA_APLICADA = 100
    RESTRICCION_CARGA_LIBERADA = 101

    # =========================================================
    # CONSULTAS / REPORTES
    # =========================================================
    REPORTE_ESTUDIANTES_POR_CURSO = 110

    # =========================================================
    # ASIGNACIONES CURSO-DOCENTE
    # =========================================================
    CURSO_DOCENTE_CREADO = 120
    CURSO_DOCENTE_ACTUALIZADO = 121
    CURSO_DOCENTE_ELIMINADO = 122

    # =========================================================
    # ASISTENCIAS
    # =========================================================
    ASISTENCIA_LISTA_CREADA = 130
    ASISTENCIA_LISTA_ACTUALIZADA = 131
    ASISTENCIA_LISTA_ELIMINADA = 132
    ASISTENCIA_DETALLE_ACTUALIZADO = 133

    # =========================================================
    # FACTURACION MATRICULA MATERIA
    # =========================================================
    FACTURA_MATRICULA_CREADA = 140
    FACTURA_MATRICULA_ACTUALIZADA = 141
    FACTURA_MATRICULA_ANULADA = 142

    # =========================================================
    # USUARIOS / SEGURIDAD
    # =========================================================
    USUARIO_CREADO = 150
    USUARIO_ACTUALIZADO = 151
    USUARIO_ELIMINADO = 152


class Tab:
    """
    Códigos de tabla para dbo.Tabla_Auditoria.
    """

    LEGACY = "LEGACY"

    ESTADO_GENERAL = "EG01"
    DOCENTES = "D01"
    CURSOS_PROGRAMAS = "CP01"
    MATERIAS = "M01"
    ESTUDIANTES = "E01"
    MATRICULA_MATERIA = "MM01"
    ASISTENCIA_DETALLE = "AD01"
    ASISTENCIA_LISTA = "AL01"
    AUDITORIA = "AU01"
    BECADOS = "BECD01"
    BECAS = "BEC01"
    CURSO_DOCENTE = "CD01"
    CURSO_JORNADAS = "CJ01"
    DIA_JORNADA = "DJ01"
    DIAS_SEMANA = "DS01"
    DOCENTE_MATERIA = "DM01"
    ESTADO_PAGO_MATRICULA = "EPM01"
    ESTADO_USUARIO = "EU01"
    FORMA_PAGO = "FP01"
    HORARIO_TIPO = "HT01"
    JORNADAS = "J01"
    MATERIA_HORARIO = "MH01"
    MATERIAS_POR_CURSO = "MPC01"
    MATRICULA_CURSO = "MC01"
    MATRICULA_MATERIA_FACTURACION = "MF01"
    MOVIMIENTO_AUDITORIA = "MA01"
    PERIODOS = "P01"
    PROFESIONES = "PR01"
    TIPO_USUARIO = "TU01"
    USUARIOS = "U01"


TABLA_AUDITORIA_MAP = {
    "Estado_General": Tab.ESTADO_GENERAL,
    "Docentes": Tab.DOCENTES,
    "Cursos_Programas": Tab.CURSOS_PROGRAMAS,
    "Materias": Tab.MATERIAS,
    "Estudiantes": Tab.ESTUDIANTES,
    "Matricula_Materia": Tab.MATRICULA_MATERIA,
    "Asistencia_Detalle": Tab.ASISTENCIA_DETALLE,
    "Asistencia_Lista": Tab.ASISTENCIA_LISTA,
    "Auditoria": Tab.AUDITORIA,
    "Becados": Tab.BECADOS,
    "Becas": Tab.BECAS,
    "Curso_Docente": Tab.CURSO_DOCENTE,
    "Curso_Jornadas": Tab.CURSO_JORNADAS,
    "Dia_Jornada": Tab.DIA_JORNADA,
    "Dias_Semana": Tab.DIAS_SEMANA,
    "Docente_Materia": Tab.DOCENTE_MATERIA,
    "Estado_Pago_Matricula": Tab.ESTADO_PAGO_MATRICULA,
    "Estado_Usuario": Tab.ESTADO_USUARIO,
    "Forma_Pago": Tab.FORMA_PAGO,
    "Horario_Tipo": Tab.HORARIO_TIPO,
    "Jornadas": Tab.JORNADAS,
    "Materia_Horario": Tab.MATERIA_HORARIO,
    "Materias_Por_Curso": Tab.MATERIAS_POR_CURSO,
    "Matricula_Curso": Tab.MATRICULA_CURSO,
    "Matricula_Materia_Facturacion": Tab.MATRICULA_MATERIA_FACTURACION,
    "Movimiento_Auditoria": Tab.MOVIMIENTO_AUDITORIA,
    "Periodos": Tab.PERIODOS,
    "Profesiones": Tab.PROFESIONES,
    "Tipo_Usuario": Tab.TIPO_USUARIO,
    "Usuarios": Tab.USUARIOS,
}


def get_tabla_codigo(nombre_tabla: str | None, default: str = Tab.LEGACY) -> str:
    """
    Devuelve el código de auditoría de una tabla a partir del nombre.

    Ejemplos:
    - 'Docentes' -> 'D01'
    - 'dbo.Docentes' -> 'D01'
    - None -> 'LEGACY'
    """
    if not nombre_tabla:
        return default

    nombre_limpio = str(nombre_tabla).strip()

    if "." in nombre_limpio:
        nombre_limpio = nombre_limpio.split(".")[-1]

    return TABLA_AUDITORIA_MAP.get(nombre_limpio, default)


def stringify_row_id(row_id: object | None, default: str = "N/A") -> str:
    """
    Convierte cualquier id simple en texto seguro para auditoría.

    Ejemplos:
    - 5 -> '5'
    - 'A001' -> 'A001'
    - None -> 'N/A'
    """
    if row_id is None:
        return default

    texto = str(row_id).strip()
    return texto if texto else default


def compose_row_id(*parts: object, sep: str = "|", default: str = "N/A") -> str:
    """
    Construye un id compuesto para tablas con PK compuesta.

    Ejemplos:
    - compose_row_id('2026-001', 3, 1) -> '2026-001|3|1'
    - compose_row_id(None, 3) -> '3'
    """
    values: list[str] = []

    for part in parts:
        if part is None:
            continue

        texto = str(part).strip()
        if texto:
            values.append(texto)

    if not values:
        return default

    return sep.join(values)


def compose_named_row_id(**kwargs: object) -> str:
    """
    Construye un id compuesto etiquetado.

    Ejemplo:
    - compose_named_row_id(Carnet='2026-001', Curso_Cod=3, Periodo=1)
      -> 'Carnet=2026-001|Curso_Cod=3|Periodo=1'
    """
    values: list[str] = []

    for key, value in kwargs.items():
        if value is None:
            continue

        texto = str(value).strip()
        if texto:
            values.append(f"{key}={texto}")

    if not values:
        return "N/A"

    return "|".join(values)