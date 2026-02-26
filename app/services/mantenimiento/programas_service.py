# app/services/programas_service.py
from __future__ import annotations

import pyodbc

from app.repositories.mantenimiento.programas_repo import exists_programa_descripcion


from app.core.exceptions import ValidationError

def validar_programa_data(
    *,
    descripcion: str,
    horario_tipo_id: int | None,
    jornadas_ids: list[int] | None,
    precio_matricula: str,
    estado_codigo: int,
) -> dict:
    descripcion = (descripcion or "").strip()
    precio_txt = (precio_matricula or "").strip()
    jornadas_ids = jornadas_ids or []

    if not descripcion:
        raise ValidationError("La descripción es requerida.")

    # Horario_TipoId puede ser NULL
    if horario_tipo_id == "" or horario_tipo_id is None:
        horario_tipo_id = None
    else:
        try:
            horario_tipo_id = int(horario_tipo_id)
        except Exception:
            raise ValidationError("Horario inválido. Debe seleccionar 1, 2 o 3.")
        if horario_tipo_id not in (1, 2, 3):
            raise ValidationError("Horario inválido. Debe seleccionar 1, 2 o 3.")

    # Normaliza jornadas: solo {1,2,3}, sin duplicados
    jornadas_ids_clean: list[int] = []
    for x in jornadas_ids:
        try:
            jid = int(x)
        except Exception:
            continue
        if jid in (1, 2, 3) and jid not in jornadas_ids_clean:
            jornadas_ids_clean.append(jid)
    jornadas_ids_clean.sort()

    if horario_tipo_id is None:
        if jornadas_ids_clean:
            raise ValidationError("No puede seleccionar jornadas si el horario no está definido.")
    else:
        if len(jornadas_ids_clean) != horario_tipo_id:
            raise ValidationError(
                f"Debe seleccionar exactamente {horario_tipo_id} jornada(s) según el horario elegido."
            )

    # Precio
    try:
        # permite "12,500.00" -> "12500.00" por si acaso
        precio = float(precio_txt.replace(",", ""))
    except Exception:
        raise ValidationError("Precio Matrícula inválido (use número, ejemplo 12500 o 12500.50).")

    if precio < 0:
        raise ValidationError("Precio Matrícula no puede ser negativo.")

    # Estado
    try:
        estado_codigo = int(estado_codigo)
    except Exception:
        raise ValidationError("Estado inválido.")

    return {
        "descripcion": descripcion,
        "horario_tipo_id": horario_tipo_id,
        "jornadas_ids": jornadas_ids_clean,
        "precio_matricula": precio,
        "estado_codigo": estado_codigo,
    }


def validar_programa_unicidad(
    conn: pyodbc.Connection,
    *,
    curso_cod: int | None,
    descripcion: str,
) -> None:
    """
    Anti-duplicados:
    - No permitir Descripcion duplicada en Cursos_Programas.
    - En UPDATE excluye el mismo Curso_Cod.
    """
    exclude = int(curso_cod) if curso_cod is not None else None

    if exists_programa_descripcion(conn, descripcion, exclude_curso_cod=exclude):
        raise ValidationError("Ya existe un programa con esa descripción.")