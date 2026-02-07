USE Universidad;
GO

CREATE TABLE Tipo_Usuario (
    Tipo_Usuario      NUMERIC(1, 0) NOT NULL,
    Descripcion_Tipo  VARCHAR(50) NOT NULL,
    Estado_Tipo       NUMERIC(1, 0) NOT NULL,
    CONSTRAINT PK_Tipo_Usuario PRIMARY KEY (Tipo_Usuario)
);
GO
