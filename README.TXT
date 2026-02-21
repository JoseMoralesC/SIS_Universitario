Sistema de Gestión Académica
SIS-Universitario — Entregable No. 1 y Entregable No. 2

Curso: Programación III
Lenguaje: Python
Base de Datos: SQL Server Express
Base de datos utilizada: Universidad

Descripción General

El SIS-Universitario es un sistema de información académica desarrollado en Python, con conexión a SQL Server Express, cuyo objetivo es gestionar los procesos académicos básicos de una universidad.

Este Entregable No. 1 se enfoca exclusivamente en:

Conexión segura a SQL Server mediante autenticación SQL.

Validación de usuarios contra el motor de base de datos.

Verificación de existencia del usuario en la tabla Usuarios.

Interfaz gráfica de Login.

Manejo adecuado de errores.

Cumplimiento estricto de los requisitos solicitados por el docente.

Alcance del Entregable No. 1

- Conexión a SQL Server Express
- Autenticación por usuario y contraseña (SQL Authentication)
- Validación del usuario en la tabla Usuarios
- Mensaje de error específico si el usuario existe en SQL pero no en la tabla
- Interfaz gráfica de Login con Tkinter
- Visualización de imagen según tipo de usuario
- Manejo de errores controlado
- Estructura modular del proyecto

Nota:
Las funcionalidades académicas (matrícula, notas, asistencia, reportes, etc.) serán implementadas en entregables posteriores.

Interfaz de Login

La ventana de login incluye:

Campo Usuario

Campo Contraseña

Botón Validar

Botón Cancelar

Imagen dinámica del usuario según su rol:

Administrador.jpg

Auditor.jpg

Operador.jpg

default.png (imagen por defecto)

La imagen cambia automáticamente al escribir el nombre de usuario.

Seguridad y Validaciones

El sistema realiza las siguientes validaciones en orden:

Conexión a SQL Server

Se valida que el usuario y contraseña existan en SQL Server.

Validación en tabla Usuarios

Se verifica que el usuario autenticado exista en la tabla Usuarios.

Mensaje específico requerido

Si el usuario existe en SQL Server pero no en la tabla:

“Usuario con permiso en SQL, pero, no registrado en la tabla de la Base de Datos”

Manejo de errores

Credenciales incorrectas

Base de datos inexistente

Falta de permisos

Errores inesperados

Base de Datos

Motor: SQL Server Express

Nombre de la Base de Datos: Universidad

Instancia: localhost\SQLEXPRESS

Tablas implementadas en este entregable:

Usuarios

Tipo_Usuario

Profesiones

Docentes

Cursos_Programas

Materias

Estudiantes

Matricula_Curso

Matricula_Materia

Formas_Pago

Auditoria

Movimientos_Auditoria

El diseño y normalización de la base de datos se realizó siguiendo los lineamientos del enunciado del proyecto.

Usuarios del Sistema

Se crearon usuarios con autenticación SQL Server:

Administrador (usuario con privilegios)

Auditor

Operador

Estandar (usuario operativo)

Cada usuario:

Existe en SQL Server (Logins)

Existe en la tabla Usuarios

Tiene su imagen asociada en el sistema

----------------------------------------------------------------
ENTREGABLE No. 2
----------------------------------------------------------------

Descripción General del Entregable No. 2

El Entregable No. 2 amplía el sistema SIS-Universitario incorporando un menú principal moderno y la implementación de mantenimientos académicos mediante operaciones CRUD reales, conectados directamente a la base de datos SQL Server.

Este entregable introduce una arquitectura más robusta, orientada a la escalabilidad y reutilización de código, manteniendo separación estricta de responsabilidades por capas.

Alcance del Entregable No. 2

- Ventana de bienvenida (Welcome) como punto de entrada del sistema.
- Menú principal con navegación lateral.
- Carga diferida (lazy-load) de módulos según selección del usuario.
- Implementación completa de CRUD para los siguientes mantenimientos:

  - Docentes
  - Programas
  - Cursos / Materias
  - Estudiantes

- Integración directa con SQL Server mediante pyodbc.
- Validaciones de negocio centralizadas en la capa de servicios.
- Manejo controlado de errores de base de datos y validaciones.
- Interfaz gráfica unificada y consistente utilizando Tkinter.

Interfaz del Sistema

El sistema cuenta con:

- Ventana de bienvenida con información general del sistema.
- Menú principal con navegación lateral.
- Módulos organizados en pestañas.
- Formularios de mantenimiento con:
  - Campos de texto
  - Combobox dinámicos
  - Botones de acción: Nuevo, Guardar, Actualizar y Eliminar
- Listados con grillas (TreeView) con scroll vertical y horizontal.
- Ajuste automático del ancho de columnas según contenido.

Arquitectura del Sistema

El proyecto sigue una arquitectura modular basada en capas:

- UI: manejo de ventanas y componentes gráficos.
- Endpoints: orquestación de operaciones y conexión a base de datos.
- Services: validaciones y reglas de negocio.
- Repositories: acceso directo a SQL Server.
- Core: configuración general, conexión y sesión.

Estructura del Proyecto (Entregable No. 2)

SIS_Universitario/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── session.py
│   │   └── __init__.py
│   │
│   ├── endpoints/
│   │   ├── docentes_endpoints.py
│   │   ├── cursos_endpoints.py
│   │   ├── programas_endpoints.py
│   │   ├── estudiantes_endpoints.py
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── docentes_service.py
│   │   ├── cursos_service.py
│   │   ├── programas_service.py
│   │   ├── estudiantes_service.py
│   │   └── __init__.py
│   │
│   ├── repositories/
│   │   ├── docentes_repo.py
│   │   ├── cursos_repo.py
│   │   ├── programas_repo.py
│   │   ├── estudiantes_repo.py
│   │   └── __init__.py
│   │
│   ├── ui/
│   │   ├── welcome_window.py
│   │   ├── main_menu.py
│   │   ├── mantenimientos/
│   │   │   ├── base_tab.py
│   │   │   ├── docentes_tab.py
│   │   │   ├── cursos_tab.py
│   │   │   ├── programas_tab.py
│   │   │   ├── estudiantes_tab.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   └── assets/
│       └── users/
│           ├── Administrador.jpg
│           ├── Auditor.jpg
│           ├── Operador.jpg
│           └── default.png
│
├── databases/
│   └── scripts SQL
│
├── main.py
├── requirements.txt
└── README.txt

Ejecución del Sistema

Verificar que SQL Server Express esté activo.

Confirmar que la base de datos Universidad exista.

Actualizar en app/core/config.py los datos de conexión si es necesario.

Ejecutar el sistema desde consola:

python main.py

Dependencias

Instalar dependencias necesarias:

pip install pyodbc pillow

Requiere:

ODBC Driver 17 o 18 for SQL Server

Python 3.10+

Observaciones Finales

El sistema cumple con los requisitos del Entregable No. 1 y Entregable No. 2.

La arquitectura permite escalar el sistema para futuros entregables.

Se mantiene una separación clara de capas y responsabilidades.

El código sigue un enfoque modular y mantenible.

Autor

José Rodolfo Morales Calderón
Curso: Programación III
Institución: Colegio Universitario de Cartago (CUC)
Repositorio Github (Publico): https://github.com/JoseMoralesC/SIS_Universitario