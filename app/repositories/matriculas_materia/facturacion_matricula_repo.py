from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import pyodbc


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_estado_codigo_by_desc(conn: pyodbc.Connection, estado_desc: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Estado_Codigo
        FROM dbo.Estado_General
        WHERE Estado_Desc = ?;
        """,
        (estado_desc.strip(),),
    )
    row = cur.fetchone()

    if not row:
        raise ValueError(f"Estado no encontrado: {estado_desc}")

    return int(row[0])


def get_estado_pago_cod_by_desc(conn: pyodbc.Connection, estado_pago_desc: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Estado_Pago_Cod
        FROM dbo.Estado_Pago_Matricula
        WHERE Estado_Pago_Desc = ?;
        """,
        (estado_pago_desc.strip(),),
    )
    row = cur.fetchone()

    if not row:
        raise ValueError(f"Estado de pago no encontrado: {estado_pago_desc}")

    return int(row[0])


# =========================================================
# Catálogos
# =========================================================
def fetch_formas_pago(conn: pyodbc.Connection) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Forma_Pago_Cod, Descripcion
        FROM dbo.Forma_Pago
        ORDER BY Descripcion;
        """
    )
    return [(int(r[0]), str(r[1])) for r in cur.fetchall()]


def get_forma_pago_desc_by_cod(conn: pyodbc.Connection, forma_pago_cod: int) -> str:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT Descripcion
        FROM dbo.Forma_Pago
        WHERE Forma_Pago_Cod = ?;
        """,
        (int(forma_pago_cod),),
    )
    row = cur.fetchone()

    if not row:
        raise ValueError("La forma de pago seleccionada no existe.")

    return str(row[0]).strip()


# =========================================================
# Referencia automática
# =========================================================
def get_prefijo_forma_pago(descripcion: str) -> str:
    desc = (descripcion or "").strip().lower()

    if "efectivo" in desc:
        return "EFEC"
    if "sinpe" in desc:
        return "SINP"
    if "tarjeta" in desc:
        return "TARJ"

    raise ValueError(
        "No fue posible generar la referencia automática. "
        "La forma de pago no tiene un prefijo configurado."
    )


def get_siguiente_consecutivo_referencia(conn: pyodbc.Connection) -> int:
    """
    Busca el consecutivo global más alto usado en Referencia_Pago
    con formato REF-XXXX-0001 y retorna el siguiente.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ISNULL(MAX(
            TRY_CAST(RIGHT(Referencia_Pago, 4) AS INT)
        ), 0) + 1
        FROM dbo.Matricula_Materia_Facturacion
        WHERE Referencia_Pago IS NOT NULL
          AND LTRIM(RTRIM(Referencia_Pago)) <> ''
          AND Referencia_Pago LIKE 'REF-%-[0-9][0-9][0-9][0-9]';
        """
    )
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else 1


def build_referencia_pago(conn: pyodbc.Connection, forma_pago_cod: int) -> str:
    descripcion = get_forma_pago_desc_by_cod(conn, forma_pago_cod)
    prefijo = get_prefijo_forma_pago(descripcion)
    consecutivo = get_siguiente_consecutivo_referencia(conn)

    return f"REF-{prefijo}-{consecutivo:04d}"


# =========================================================
# Beca vigente
# =========================================================
def fetch_beca_vigente_estudiante(
    conn: pyodbc.Connection,
    *,
    carnet: str,
) -> dict:
    """
    Retorna la beca activa más reciente del estudiante.
    Si no tiene, devuelve estructura sin beca.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT TOP 1
            b.id_beca,
            bc.nombre_beca,
            bc.porcentaje_descuento,
            b.fecha_aplicacion
        FROM dbo.Becados b
        INNER JOIN dbo.Becas bc
            ON bc.id_beca = b.id_beca
        WHERE b.carnet = ?
          AND b.Estado_Codigo = ?
          AND bc.Estado_Codigo = ?
        ORDER BY b.fecha_aplicacion DESC, b.id_becado DESC;
        """,
        (
            str(carnet).strip(),
            int(activo),
            int(activo),
        ),
    )
    row = cur.fetchone()

    if not row:
        return {
            "tiene_beca": False,
            "id_beca": None,
            "nombre_beca": "Sin beca",
            "porcentaje_beca": 0,
            "fecha_aplicacion": None,
        }

    return {
        "tiene_beca": True,
        "id_beca": int(row[0]),
        "nombre_beca": str(row[1]),
        "porcentaje_beca": int(row[2]),
        "fecha_aplicacion": str(row[3]),
    }


# =========================================================
# Materias pendientes de facturar
# =========================================================
def fetch_materias_pendientes_facturacion(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    anio: int,
) -> list[dict]:
    """
    Trae materias matriculadas del estudiante que aún NO han sido facturadas
    en ese curso/período.
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")

    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            mm.Matricula_Materia_Id,
            m.Materia_Cod,
            m.Descripcion,
            m.Precio,
            d.Docente_Cod,
            d.Nombre_Completo
        FROM dbo.Matricula_Materia mm
        INNER JOIN dbo.Materias m
            ON m.Materia_Cod = mm.Materia_Cod
        INNER JOIN dbo.Docentes d
            ON d.Docente_Cod = mm.Docente_Cod
        WHERE mm.Carnet = ?
          AND m.Curso_Cod = ?
          AND mm.Estado_Codigo = ?
          AND (
                mm.Periodo_Id = ?
                OR (mm.Periodo_Id IS NULL AND mm.Periodo = ?)
          )
          AND NOT EXISTS (
                SELECT 1
                FROM dbo.Matricula_Materia_Facturacion f
                WHERE f.Carnet = mm.Carnet
                  AND f.Curso_Cod = ?
                  AND f.Materia_Cod = mm.Materia_Cod
                  AND f.Estado_Codigo = ?
                  AND (
                        f.Periodo_Id = ?
                        OR (f.Periodo_Id IS NULL AND mm.Periodo = ?)
                  )
          )
        ORDER BY m.Descripcion;
        """,
        (
            str(carnet).strip(),
            int(curso_cod),
            int(activo),
            int(periodo_id),
            int(anio),
            int(curso_cod),
            int(activo),
            int(periodo_id),
            int(anio),
        ),
    )

    rows = []
    for r in cur.fetchall():
        rows.append(
            {
                "matricula_materia_id": int(r[0]),
                "materia_cod": int(r[1]),
                "materia": str(r[2]),
                "precio_base": _to_decimal(r[3]),
                "docente_cod": int(r[4]),
                "docente": str(r[5]),
            }
        )
    return rows


# =========================================================
# Resumen de facturación
# =========================================================
def build_resumen_facturacion(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    anio: int,
) -> dict:
    beca = fetch_beca_vigente_estudiante(conn, carnet=carnet)
    materias = fetch_materias_pendientes_facturacion(
        conn,
        carnet=carnet,
        curso_cod=curso_cod,
        periodo_id=periodo_id,
        anio=anio,
    )

    subtotal = sum((m["precio_base"] for m in materias), Decimal("0.00"))
    porcentaje = Decimal(str(beca["porcentaje_beca"]))
    descuento = (subtotal * porcentaje / Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    total = (subtotal - descuento).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    cantidad = len(materias)
    descuento_por_materia = Decimal("0.00")

    if cantidad > 0 and descuento > 0:
        descuento_por_materia = (descuento / Decimal(str(cantidad))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    detalle = []
    acumulado_desc = Decimal("0.00")

    for i, m in enumerate(materias, start=1):
        desc_item = descuento_por_materia

        if i == cantidad:
            desc_item = (descuento - acumulado_desc).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        acumulado_desc += desc_item
        total_item = (m["precio_base"] - desc_item).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        detalle.append(
            {
                "matricula_materia_id": m["matricula_materia_id"],
                "materia_cod": m["materia_cod"],
                "materia": m["materia"],
                "precio_base": m["precio_base"],
                "docente_cod": m["docente_cod"],
                "docente": m["docente"],
                "porcentaje_beca": int(beca["porcentaje_beca"]),
                "monto_descuento": desc_item,
                "monto_final": total_item,
            }
        )

    return {
        "beca": beca,
        "materias": detalle,
        "subtotal": subtotal,
        "descuento": descuento,
        "total": total,
        "cantidad_materias": cantidad,
    }


# =========================================================
# Persistencia
# =========================================================
def insert_facturacion_matricula(
    conn: pyodbc.Connection,
    *,
    carnet: str,
    curso_cod: int,
    periodo_id: int,
    anio: int,
    forma_pago_cod: int,
    referencia_pago: str | None,
    observacion: str | None,
    codigo_usuario: int,
) -> dict:
    """
    Inserta una fila por cada materia pendiente de facturar.
    El flujo actual registra el pago como CANCELADO (pagado).

    La referencia se genera automáticamente con formato:
    REF-EFEC-0001 / REF-SINP-0002 / REF-TARJ-0003
    """
    activo = get_estado_codigo_by_desc(conn, "Activo")
    estado_pago_cancelado = get_estado_pago_cod_by_desc(conn, "Cancelado")

    resumen = build_resumen_facturacion(
        conn,
        carnet=carnet,
        curso_cod=curso_cod,
        periodo_id=periodo_id,
        anio=anio,
    )

    materias = resumen["materias"]

    if not materias:
        return {
            "insertados": 0,
            "subtotal": Decimal("0.00"),
            "descuento": Decimal("0.00"),
            "total": Decimal("0.00"),
            "referencia_pago": None,
        }

    referencia_generada = build_referencia_pago(conn, int(forma_pago_cod))
    referencia_final = referencia_generada.strip()

    cur = conn.cursor()

    for item in materias:
        cur.execute(
            """
            INSERT INTO dbo.Matricula_Materia_Facturacion
            (
                Carnet,
                Curso_Cod,
                Materia_Cod,
                Forma_Pago_Cod,
                Estado_Codigo,
                Estado_Pago_Cod,
                Fecha,
                Fecha_Pago,
                Periodo_Id,
                Precio_Base,
                Porcentaje_Beca,
                Monto_Descuento,
                Monto_Final,
                Referencia_Pago,
                Observacion,
                Codigo_Usuario
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, SYSDATETIME(), SYSDATETIME(), ?,
                ?, ?, ?, ?, ?, ?, ?
            );
            """,
            (
                str(carnet).strip(),
                int(curso_cod),
                int(item["materia_cod"]),
                int(forma_pago_cod),
                int(activo),
                int(estado_pago_cancelado),
                int(periodo_id),
                item["precio_base"],
                int(item["porcentaje_beca"]),
                item["monto_descuento"],
                item["monto_final"],
                referencia_final,
                (observacion or "").strip() or None,
                int(codigo_usuario),
            ),
        )

    conn.commit()

    return {
        "insertados": len(materias),
        "subtotal": resumen["subtotal"],
        "descuento": resumen["descuento"],
        "total": resumen["total"],
        "referencia_pago": referencia_final,
    }