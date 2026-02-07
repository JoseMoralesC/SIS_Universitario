USE Universidad;
GO

CREATE TABLE Estado_Usuario (
    Estado_Usuario      NUMERIC(1, 0) NOT NULL,
    Descripcion_Estado  VARCHAR(50) NOT NULL,
    CONSTRAINT PK_Estado_Usuario PRIMARY KEY (Estado_Usuario)
);
GO
