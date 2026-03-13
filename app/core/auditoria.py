# app/core/auditoria.py
# Códigos de movimiento para dbo.Movimiento_Auditoria


class Mov:

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
    # PROGRAMAS
    # =========================================================
    PROGRAMA_CREADO = 30
    PROGRAMA_ACTUALIZADO = 31
    PROGRAMA_ELIMINADO = 32

    # =========================================================
    # CURSOS
    # =========================================================
    CURSO_CREADO = 40
    CURSO_ACTUALIZADO = 41
    CURSO_ELIMINADO = 42

    # =========================================================
    # BECAS
    # =========================================================
    BECA_CREADA = 50
    BECA_ACTUALIZADA = 51
    BECA_ELIMINADA = 52

    # =========================================================
    # BECADOS
    # =========================================================
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