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

----------------------------------------------------------------
ENTREGABLE No. 3
----------------------------------------------------------------

Descripción General del Entregable No. 3

El Entregable No. 3 amplía el sistema SIS-Universitario incorporando la gestión completa del proceso de Matrículas Académicas, implementando reglas reales de negocio, validaciones preventivas y funcionalidades de consulta y reporte, manteniendo la arquitectura modular definida desde los entregables anteriores.

Este entregable consolida la separación por capas (UI, Endpoints, Services y Repositories) y refuerza la escalabilidad del sistema para futuros módulos académicos.

Alcance del Entregable No. 3

- Implementación del módulo de Gestión de Matrículas.
- Registro de matrículas por curso, docente y período académico.
- Generación automática del estado inicial de la matrícula según reglas del sistema.
- Prevención de duplicados mediante validaciones en base de datos y en la interfaz gráfica.
- Filtro dinámico de estudiantes elegibles para matrícula.
- Consulta de matrículas por curso.
- Generación de reportes de estudiantes matriculados por curso.
- Integración completa con el sistema de auditoría de movimientos.

Gestión de Matrículas

El módulo de Matrículas permite:

- Seleccionar Curso / Programa.
- Visualizar únicamente los Docentes asociados al curso seleccionado.
- Visualizar únicamente los Estudiantes elegibles, excluyendo aquellos ya matriculados en el período activo.
- Registrar matrículas válidas respetando las reglas académicas definidas.
- Cambiar el estado de una matrícula existente.
- Eliminar matrículas con confirmación del usuario.

Consultas y Reportes

El sistema incluye:

- Consulta por curso con visualización en grilla.
- Reporte de estudiantes matriculados por curso.
- Actualización dinámica de los datos mostrados según la interacción del usuario.
- Manejo adecuado de casos sin resultados.

Interfaz Gráfica y Experiencia de Usuario

La interfaz del módulo de Matrículas incorpora:

- Flujo lógico de selección: Curso → Docente → Estudiante.
- Combobox dependientes y dinámicos.
- Prevención de errores desde la interfaz.
- Grillas con scroll vertical y horizontal.
- Navegación mediante pestañas (Listado, Consulta por Curso, Reportes).

Arquitectura y Diseño

El Entregable No. 3 mantiene y refuerza la arquitectura modular del sistema:

- UI: manejo de vistas, validaciones visuales y experiencia de usuario.
- Endpoints: orquestación de operaciones y control transaccional.
- Services: validaciones de negocio y reglas académicas.
- Repositories: acceso directo y controlado a la base de datos.
- Core: auditoría, sesión y configuración general.

Estado del Proyecto

Con la finalización del Entregable No. 3:

- El sistema cumple con los requisitos académicos solicitados.
- La base del sistema es estable, modular y escalable.
- El proyecto queda preparado para la incorporación de nuevos módulos como:
  - Matrícula por materias
  - Notas académicas
  - Asistencia
  - Reportes avanzados

Estructura del Proyecto (Entregable No. 3)
SIS_Universitario/
├── app/
│ ├── init.py
│ │
│ ├── assets/
│ │ ├── background.png
│ │ └── users/
│ │ ├── Administrador.jpg
│ │ ├── Auditor.jpg
│ │ ├── Operador.jpg
│ │ └── default.png
│ │
│ ├── core/
│ │ ├── init.py
│ │ ├── auditoria.py
│ │ ├── config.py
│ │ ├── db.py
│ │ ├── error_handler.py
│ │ ├── exceptions.py
│ │ └── session.py
│ │
│ ├── endpoints/
│ │ ├── mantenimiento/
│ │ │ ├── becados_endpoints.py
│ │ │ ├── becas_endpoints.py
│ │ │ ├── cursos_endpoints.py
│ │ │ ├── docentes_endpoints.py
│ │ │ ├── estudiantes_endpoints.py
│ │ │ └── programas_endpoints.py
│ │ └── matriculas/
│ │ ├── init.py
│ │ └── matriculas_endpoints.py
│ │
│ ├── repositories/
│ │ ├── init.py
│ │ ├── auditoria_repo.py
│ │ ├── usuarios_repo.py
│ │ ├── mantenimiento/
│ │ │ ├── becados_repo.py
│ │ │ ├── becas_repo.py
│ │ │ ├── cursos_repo.py
│ │ │ ├── docentes_repo.py
│ │ │ ├── estado_general_repo.py
│ │ │ ├── estudiantes_repo.py
│ │ │ ├── profesiones_repo.py
│ │ │ └── programas_repo.py
│ │ └── matriculas/
│ │ ├── init.py
│ │ └── matriculas_repo.py
│ │
│ ├── services/
│ │ ├── init.py
│ │ ├── auth_service.py
│ │ ├── mantenimiento/
│ │ │ ├── becados_service.py
│ │ │ ├── becas_service.py
│ │ │ ├── cursos_service.py
│ │ │ ├── docentes_service.py
│ │ │ ├── estudiantes_service.py
│ │ │ └── programas_service.py
│ │ └── matriculas/
│ │ ├── init.py
│ │ └── matriculas_service.py
│ │
│ ├── ui/
│ │ ├── init.py
│ │ ├── theme.py
│ │ ├── login_window.py
│ │ ├── welcome_window.py
│ │ ├── main_menu.py
│ │ ├── transitions/
│ │ │ └── window_slide.py
│ │ ├── components/
│ │ │ ├── init.py
│ │ │ ├── confirm_dialog.py
│ │ │ ├── error_dialog.py
│ │ │ └── toast.py
│ │ ├── mantenimientos/
│ │ │ ├── init.py
│ │ │ ├── base_tab.py
│ │ │ ├── becados_tab.py
│ │ │ ├── becas_tab.py
│ │ │ ├── cursos_tab.py
│ │ │ ├── docentes_tab.py
│ │ │ ├── estudiantes_tab.py
│ │ │ └── programas_tab.py
│ │ ├── matriculas/
│ │ │ └── init.py
│ │ └── views/
│ │ ├── init.py
│ │ ├── main_menu_view.py
│ │ ├── mantenimientos_view.py
│ │ └── matriculas_view.py
│ │
│ └── modules/
│ └── (reservado / a futuro)
│
├── databases/
│ └── scripts/
│ ├── 009_auditoria_setup.sql
│ ├── 01_create_table_usuarios.sql
│ ├── 02_create_table_tipo_usuario.sql
│ ├── 03_create_table_estado_usuario.sql
│ └── 04_insert_usuarios_Usuarios.sql
│
├── docs/
│ └── mapa/
│ └── mapa_visual_estructura.txt
│
├── main.py
├── requirements.txt
└── README.TXT  

Autor

José Rodolfo Morales Calderón
Curso: Programación III
Institución: Colegio Universitario de Cartago (CUC)
Repositorio Github (Publico): https://github.com/JoseMoralesC/SIS_Universitario