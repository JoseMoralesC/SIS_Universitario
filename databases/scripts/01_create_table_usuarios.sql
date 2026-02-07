USE Universidad;
GO

CREATE TABLE Usuarios (
    Codigo_Usuario NUMERIC(1, 0) NOT NULL,
    Id_Usuario     NUMERIC(10, 0) NOT NULL,
    Usuario        VARCHAR(12) NOT NULL,
    Nombre_Usuario NVARCHAR(35) NOT NULL,
    Tipo_Usuario   NUMERIC(1, 0) NOT NULL,
    Estado_Usuario NUMERIC(1, 0) NOT NULL,
    CONSTRAINT PK_Usuarios PRIMARY KEY (Usuario)
);
GO
