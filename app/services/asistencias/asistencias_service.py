# app/services/asistencias/asistencias_service.py
from __future__ import annotations

from datetime import datetime
import calendar
import pyodbc

from app.repositories.asistencias.asistencias_repo import (
    count_asistencia_resumen,
    count_estudiantes_matriculados,
    exists_curso,
    exists_docente,
    exists_estudiante,
    exists_materia,
    exists_periodo,
    fetch_asistencia_detalle,
    fetch_cursos_por_periodo,
    fetch_docentes_por_periodo_curso_materia,
    fetch_estudiantes_matriculados,
    fetch_horario_principal_materia,
    fetch_horarios_materia,
    fetch_materias_por_periodo_curso,
    fetch_periodos_activos,
    find_asistencia_lista_by_unique,
    get_asistencia_lista_detalle_cabecera,
    get_estado_codigo_by_desc,
    insert_asistencia_lista,
    replace_asistencia_detalle,
    update_asistencia_lista_cabecera,
)


# =========================================================
# Helpers internos
# =========================================================
_DIA_NUM_TO_COD = {
    0: "L",  # lunes
    1: "K",  # martes
    2: "M",  # miércoles
    3: "J",  # jueves
    4: "V",  # viernes
    5: "S",  # sábado
    6: "D",  # domingo
}

_DIA_COD_TO_NOMBRE = {
    "L": "Lunes",
    "K": "Martes",
    "M": "Miércoles",
    "J": "Jueves",
    "V": "Viernes",
    "S": "Sábado",
    "D": "Domingo",
}


def _parse_fecha_iso(fecha_texto: str) -> datetime.date:
    """
    Espera formato YYYY-MM-DD
    """
    valor = str(fecha_texto or "").strip()
    if not valor:
        raise ValueError("Debe indicar la fecha de la lista.")

    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("La fecha debe tener formato YYYY-MM-DD.") from exc


def _dia_cod_desde_fecha(fecha_texto: str) -> str:
    fecha = _parse_fecha_iso(fecha_texto)
    weekday = fecha.weekday()  # lunes=0 ... domingo=6
    return _DIA_NUM_TO_COD[weekday]


def _nombre_dia_desde_fecha(fecha_texto: str) -> str:
    fecha = _parse_fecha_iso(fecha_texto)
    return calendar.day_name[fecha.weekday()].capitalize()


def _normalizar_lista_carnets(items: list[str] | tuple[str, ...] | None) -> list[str]:
    if not items:
        return []

    vistos: set[str] = set()
    salida: list[str] = []

    for item in items:
        carnet = str(item or "").strip()
        if not carnet:
            continue
        if carnet in vistos:
            continue
        vistos.add(carnet)
        salida.append(carnet)

    return salida


def _validar_fk_basicas(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
) -> None:
    if not exists_periodo(conn, periodo_id):
        raise ValueError("El período seleccionado no existe.")

    if not exists_curso(conn, curso_cod):
        raise ValueError("El curso seleccionado no existe.")

    if not exists_materia(conn, materia_cod):
        raise ValueError("La materia seleccionada no existe.")

    if not exists_docente(conn, docente_cod):
        raise ValueError("El docente seleccionado no existe.")


def _validar_fecha_vs_horario_materia(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
    fecha_clase: str,
) -> tuple[str, str]:
    """
    Opción B:
    No bloquea el guardado si la fecha no coincide con el horario
    configurado de la materia.

    Retorna el día real de la fecha seleccionada:
        (dia_cod, dia_nombre)

    El horario de la materia queda como referencia informativa.
    """
    _parse_fecha_iso(fecha_clase)

    dia_cod_fecha = _dia_cod_desde_fecha(fecha_clase)
    dia_nombre_fecha = _DIA_COD_TO_NOMBRE.get(dia_cod_fecha, "Desconocido")

    return dia_cod_fecha, dia_nombre_fecha

def _validar_estudiantes_en_grupo(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    asistentes: list[str],
    ausentes: list[str],
) -> list[tuple[str, str]]:
    """
    Valida que todos los carnets enviados pertenezcan al grupo exacto.
    Retorna la lista oficial de estudiantes matriculados del grupo.
    """
    estudiantes_grupo = fetch_estudiantes_matriculados(
        conn,
        periodo_id=periodo_id,
        curso_cod=curso_cod,
        materia_cod=materia_cod,
        docente_cod=docente_cod,
    )

    set_grupo = {carnet for carnet, _nombre in estudiantes_grupo}
    enviados = asistentes + ausentes

    for carnet in enviados:
        if not exists_estudiante(conn, carnet):
            raise ValueError(f"El estudiante con carnet '{carnet}' no existe.")
        if carnet not in set_grupo:
            raise ValueError(
                f"El estudiante con carnet '{carnet}' no pertenece al grupo seleccionado."
            )

    return estudiantes_grupo


def _validar_listas(
    *,
    asistentes: list[str],
    ausentes: list[str],
    total_grupo: int,
) -> None:
    set_asistentes = set(asistentes)
    set_ausentes = set(ausentes)

    inter = set_asistentes.intersection(set_ausentes)
    if inter:
        detalle = ", ".join(sorted(inter))
        raise ValueError(
            f"No se puede registrar un estudiante en asistentes y ausentes a la vez: {detalle}"
        )

    total_registrados = len(set_asistentes) + len(set_ausentes)
    if total_registrados == 0:
        raise ValueError("Debe registrar al menos un estudiante en la lista.")

    if total_registrados > total_grupo:
        raise ValueError(
            "La cantidad registrada supera el total de estudiantes matriculados del grupo."
        )


# =========================================================
# Lookups públicos
# =========================================================
def listar_periodos_activos(conn: pyodbc.Connection) -> list[dict]:
    rows = fetch_periodos_activos(conn)
    return [{"id": periodo_id, "label": label} for periodo_id, label in rows]


def listar_cursos_por_periodo(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
) -> list[dict]:
    if not periodo_id:
        return []

    rows = fetch_cursos_por_periodo(conn, periodo_id=int(periodo_id))
    return [{"id": curso_cod, "label": desc} for curso_cod, desc in rows]


def listar_materias_por_periodo_curso(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
) -> list[dict]:
    if not periodo_id or not curso_cod:
        return []

    rows = fetch_materias_por_periodo_curso(
        conn,
        periodo_id=int(periodo_id),
        curso_cod=int(curso_cod),
    )
    return [{"id": materia_cod, "label": desc} for materia_cod, desc in rows]


def listar_docentes_por_periodo_curso_materia(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
) -> list[dict]:
    if not periodo_id or not curso_cod or not materia_cod:
        return []

    rows = fetch_docentes_por_periodo_curso_materia(
        conn,
        periodo_id=int(periodo_id),
        curso_cod=int(curso_cod),
        materia_cod=int(materia_cod),
    )
    return [{"id": docente_cod, "label": nombre} for docente_cod, nombre in rows]


def obtener_horario_principal_materia(
    conn: pyodbc.Connection,
    *,
    materia_cod: int,
) -> dict | None:
    if not materia_cod:
        return None

    row = fetch_horario_principal_materia(conn, materia_cod=int(materia_cod))
    if not row:
        return None

    dia_cod, dia_nombre, jornada_id, jornada = row
    return {
        "dia_cod": dia_cod,
        "dia_nombre": dia_nombre,
        "jornada_id": jornada_id,
        "jornada": jornada,
    }


def listar_estudiantes_grupo(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
) -> list[dict]:
    if not periodo_id or not curso_cod or not materia_cod or not docente_cod:
        return []

    rows = fetch_estudiantes_matriculados(
        conn,
        periodo_id=int(periodo_id),
        curso_cod=int(curso_cod),
        materia_cod=int(materia_cod),
        docente_cod=int(docente_cod),
    )

    return [
        {
            "carnet": carnet,
            "nombre": nombre,
            "label": f"{carnet} | {nombre}",
        }
        for carnet, nombre in rows
    ]


def obtener_resumen_grupo(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
) -> dict:
    total = count_estudiantes_matriculados(
        conn,
        periodo_id=int(periodo_id),
        curso_cod=int(curso_cod),
        materia_cod=int(materia_cod),
        docente_cod=int(docente_cod),
    )

    return {
        "total_matriculados": total,
    }


# =========================================================
# Cargar lista existente
# =========================================================
def cargar_asistencia_existente(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    fecha_clase: str,
) -> dict | None:
    _validar_fk_basicas(
        conn,
        periodo_id=int(periodo_id),
        curso_cod=int(curso_cod),
        materia_cod=int(materia_cod),
        docente_cod=int(docente_cod),
    )
    _parse_fecha_iso(fecha_clase)

    found = find_asistencia_lista_by_unique(
        conn,
        periodo_id=int(periodo_id),
        curso_cod=int(curso_cod),
        materia_cod=int(materia_cod),
        docente_cod=int(docente_cod),
        fecha_clase=fecha_clase,
    )
    if not found:
        return None

    asistencia_lista_id = int(found[0])

    cabecera = get_asistencia_lista_detalle_cabecera(
        conn,
        asistencia_lista_id=asistencia_lista_id,
    )
    detalle = fetch_asistencia_detalle(
        conn,
        asistencia_lista_id=asistencia_lista_id,
    )
    resumen = count_asistencia_resumen(
        conn,
        asistencia_lista_id=asistencia_lista_id,
    )

    asistentes: list[dict] = []
    ausentes: list[dict] = []

    for item in detalle:
        _detalle_id, carnet, nombre, estado_asistencia, observacion, estado_codigo = item

        registro = {
            "carnet": str(carnet),
            "nombre": str(nombre),
            "label": f"{str(carnet)} | {str(nombre)}",
            "observacion": observacion,
            "estado_codigo": int(estado_codigo),
        }

        if str(estado_asistencia).strip().upper() == "A":
            asistentes.append(registro)
        else:
            ausentes.append(registro)

    if cabecera is None:
        return None

    return {
        "cabecera": {
            "asistencia_lista_id": int(cabecera[0]),
            "periodo_id": int(cabecera[1]),
            "periodo_label": str(cabecera[2]),
            "curso_cod": int(cabecera[3]),
            "curso_desc": str(cabecera[4]),
            "materia_cod": int(cabecera[5]),
            "materia_desc": str(cabecera[6]),
            "docente_cod": int(cabecera[7]),
            "docente_nombre": str(cabecera[8]),
            "dia_cod": str(cabecera[9]),
            "dia_nombre": str(cabecera[10]),
            "fecha_clase": str(cabecera[11]),
            "fecha_registro": str(cabecera[12]),
            "codigo_usuario": None if cabecera[13] is None else int(cabecera[13]),
            "estado_codigo": int(cabecera[14]),
        },
        "asistentes": asistentes,
        "ausentes": ausentes,
        "resumen": resumen,
    }


# =========================================================
# Guardar / actualizar lista
# =========================================================
def guardar_asistencia(
    conn: pyodbc.Connection,
    *,
    periodo_id: int,
    curso_cod: int,
    materia_cod: int,
    docente_cod: int,
    fecha_clase: str,
    asistentes: list[str] | tuple[str, ...] | None,
    ausentes: list[str] | tuple[str, ...] | None,
    codigo_usuario: int | None,
) -> dict:
    """
    Crea o actualiza una lista de asistencia según exista o no
    una lista previa para la combinación:
    período + curso + materia + docente + fecha
    """
    periodo_id = int(periodo_id)
    curso_cod = int(curso_cod)
    materia_cod = int(materia_cod)
    docente_cod = int(docente_cod)

    asistentes_norm = _normalizar_lista_carnets(asistentes)
    ausentes_norm = _normalizar_lista_carnets(ausentes)

    _validar_fk_basicas(
        conn,
        periodo_id=periodo_id,
        curso_cod=curso_cod,
        materia_cod=materia_cod,
        docente_cod=docente_cod,
    )

    _parse_fecha_iso(fecha_clase)

    dia_cod, dia_nombre = _validar_fecha_vs_horario_materia(
        conn,
        materia_cod=materia_cod,
        fecha_clase=fecha_clase,
    )

    estudiantes_grupo = _validar_estudiantes_en_grupo(
        conn,
        periodo_id=periodo_id,
        curso_cod=curso_cod,
        materia_cod=materia_cod,
        docente_cod=docente_cod,
        asistentes=asistentes_norm,
        ausentes=ausentes_norm,
    )

    _validar_listas(
        asistentes=asistentes_norm,
        ausentes=ausentes_norm,
        total_grupo=len(estudiantes_grupo),
    )

    estado_activo = get_estado_codigo_by_desc(conn, "Activo")

    existente = find_asistencia_lista_by_unique(
        conn,
        periodo_id=periodo_id,
        curso_cod=curso_cod,
        materia_cod=materia_cod,
        docente_cod=docente_cod,
        fecha_clase=fecha_clase,
    )

    if existente:
        asistencia_lista_id = int(existente[0])

        update_asistencia_lista_cabecera(
            conn,
            asistencia_lista_id=asistencia_lista_id,
            dia_cod=dia_cod,
            fecha_clase=fecha_clase,
            codigo_usuario=codigo_usuario,
            estado_codigo=estado_activo,
        )

        replace_asistencia_detalle(
            conn,
            asistencia_lista_id=asistencia_lista_id,
            asistentes=asistentes_norm,
            ausentes=ausentes_norm,
            estado_codigo=estado_activo,
        )

        accion = "actualizada"
    else:
        asistencia_lista_id = insert_asistencia_lista(
            conn,
            periodo_id=periodo_id,
            curso_cod=curso_cod,
            materia_cod=materia_cod,
            docente_cod=docente_cod,
            dia_cod=dia_cod,
            fecha_clase=fecha_clase,
            codigo_usuario=codigo_usuario,
            estado_codigo=estado_activo,
        )

        replace_asistencia_detalle(
            conn,
            asistencia_lista_id=asistencia_lista_id,
            asistentes=asistentes_norm,
            ausentes=ausentes_norm,
            estado_codigo=estado_activo,
        )

        accion = "creada"

    resumen = count_asistencia_resumen(
        conn,
        asistencia_lista_id=asistencia_lista_id,
    )

    return {
        "ok": True,
        "accion": accion,
        "asistencia_lista_id": int(asistencia_lista_id),
        "dia_cod": dia_cod,
        "dia_nombre": dia_nombre,
        "fecha_clase": fecha_clase,
        "total_asistentes": int(resumen["asistentes"]),
        "total_ausentes": int(resumen["ausentes"]),
        "total_registrados": int(resumen["total_registrados"]),
        "total_grupo": len(estudiantes_grupo),
        "pendientes": max(0, len(estudiantes_grupo) - int(resumen["total_registrados"])),
    }