USE [Universidad];
GO

/* =====================================================
   AUDITORÍA - Setup
   - dbo.Movimiento_Auditoria: catálogo de movimientos
   - dbo.Auditoria: bitácora de eventos
   ===================================================== */

-- 1) Tabla catálogo de movimientos
IF OBJECT_ID('dbo.Movimiento_Auditoria', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Movimiento_Auditoria(
        Movimiento_Cod INT NOT NULL,
        Descripcion    VARCHAR(120) NOT NULL,
        Estado_Codigo  TINYINT NOT NULL,
        CONSTRAINT PK_Movimiento_Auditoria PRIMARY KEY (Movimiento_Cod)
    );
END
GO

-- 2) Tabla de auditoría (bitácora)
IF OBJECT_ID('dbo.Auditoria', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Auditoria(
        Auditoria_Id      INT IDENTITY(1,1) NOT NULL,
        Codigo_Usuario    VARCHAR(30) NOT NULL,
        Fecha_Movimiento  DATETIME2(7) NOT NULL CONSTRAINT DF_Auditoria_Fecha DEFAULT (SYSDATETIME()),
        Movimiento_Cod    INT NOT NULL,
        CONSTRAINT PK_Auditoria PRIMARY KEY (Auditoria_Id)
    );
END
GO

-- 3) Asegurar DEFAULT de fecha (por si la tabla existía sin default)
IF OBJECT_ID('DF_Auditoria_Fecha', 'D') IS NULL
AND COL_LENGTH('dbo.Auditoria', 'Fecha_Movimiento') IS NOT NULL
BEGIN
    ALTER TABLE dbo.Auditoria
    ADD CONSTRAINT DF_Auditoria_Fecha DEFAULT (SYSDATETIME()) FOR Fecha_Movimiento;
END
GO

-- 4) FK Auditoria -> Movimiento_Auditoria
IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = 'FK_Auditoria_Movimiento'
)
BEGIN
    ALTER TABLE dbo.Auditoria
    WITH CHECK
    ADD CONSTRAINT FK_Auditoria_Movimiento
        FOREIGN KEY (Movimiento_Cod)
        REFERENCES dbo.Movimiento_Auditoria (Movimiento_Cod);
END
GO

-- 5) Seed de movimientos (solo inserta si no existen)
MERGE dbo.Movimiento_Auditoria AS T
USING (VALUES
    (1,  'Login exitoso',         1),
    (2,  'Login fallido',         1),
    (3,  'Matrícula creada',      1),
    (4,  'Factura generada',      1),

    (10, 'Docente creado',        1),
    (11, 'Docente actualizado',   1),
    (12, 'Docente eliminado',     1),

    (20, 'Estudiante creado',     1),
    (21, 'Estudiante actualizado',1),
    (22, 'Estudiante eliminado',  1),

    (30, 'Programa creado',       1),
    (31, 'Programa actualizado',  1),
    (32, 'Programa eliminado',    1),

    (40, 'Curso creado',          1),
    (41, 'Curso actualizado',     1),
    (42, 'Curso eliminado',       1),

    (50, 'Beca creada',           1),
    (51, 'Beca actualizada',      1),
    (52, 'Beca eliminada',        1),

    (60, 'Becado creado',         1),
    (61, 'Becado actualizado',    1),
    (62, 'Becado eliminado',      1)
) AS S(Movimiento_Cod, Descripcion, Estado_Codigo)
ON T.Movimiento_Cod = S.Movimiento_Cod
WHEN NOT MATCHED THEN
    INSERT (Movimiento_Cod, Descripcion, Estado_Codigo)
    VALUES (S.Movimiento_Cod, S.Descripcion, S.Estado_Codigo);
GO

