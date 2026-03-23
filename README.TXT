Sistema de Gestión Académica
SIS-Universitario — Entregable No. 1 y Entregable No. 2

Curso: Programación III
Lenguaje: Python
Base de Datos: SQL Server Express
Base de datos utilizada: Universidad

Descripción General

El SIS-Universitario es un sistema de información académica desarrollado en Python, con conexión a SQL Server 
Express, cuyo objetivo es gestionarlos procesos académicos básicos de una universidad.

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
Las funcionalidades académicas (matrícula, notas, asistencia, reportes, etc.) serán implementadas en entregables 
posteriores.

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

El Entregable No. 2 amplía el sistema SIS-Universitario incorporando un menú principal moderno y la 
implementación de mantenimientos académicos mediante operaciones CRUD reales, conectados directamente a la 
base de datos SQL Server.

Este entregable introduce una arquitectura más robusta, orientada a la escalabilidad y reutilización de código, 
manteniendo separación estricta de responsabilidades por capas.

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

El Entregable No. 3 amplía el sistema SIS-Universitario incorporando la gestión completa del proceso de 
Matrículas Académicas, implementando reglas reales de negocio, validaciones preventivas y funcionalidades de 
consulta y reporte, manteniendo la arquitectura modular definida desde los entregables anteriores.

Este entregable consolida la separación por capas (UI, Endpoints, Services y Repositories) y refuerza la 
escalabilidad del sistema para futuros módulos académicos.

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

----------------------------------------------------------------
ENTREGABLE No. 4
----------------------------------------------------------------

Descripción General del Entregable No. 4

El Entregable No. 4 amplía el sistema SIS-Universitario incorporando el módulo de Matrícula por Materias, 
permitiendo gestionar la asignación académica detallada de materias a estudiantes previamente matriculados en 
curso, bajo reglas de negocio reales, validaciones de carga académica y control de consistencia con la 
estructura modular del sistema.

Este entregable extiende la arquitectura definida en los entregables anteriores, manteniendo la separación 
estricta por capas (UI, Endpoints, Services, Repositories y Core), e incorpora nuevos componentes 
especializados para consulta de matrícula del estudiante, asignación de materias, validación de horarios, 
relación docente-materia y apoyo al proceso de facturación académica.

Alcance del Entregable No. 4

- Implementación del módulo de Matrícula por Materias.
- Consulta de estudiantes con matrícula de curso activa.
- Validación de elegibilidad del estudiante antes de asignar materias.
- Carga dinámica del período académico correspondiente.
- Visualización de restricciones de carga académica.
- Asignación de materias al estudiante según matrícula activa.
- Consulta de docentes asociados a cada materia.
- Validación de horarios para evitar conflictos.
- Integración de apoyo al proceso de facturación de matrícula.
- Uso de ventanas emergentes especializadas para completar el proceso de matrícula.
- Integración con la arquitectura modular ya existente.
- Preparación del sistema para futuros módulos académicos relacionados.

Gestión de Matrícula por Materias

El módulo de Matrícula por Materias permite:

- Consultar estudiantes con matrícula académica activa.
- Verificar la información general de la matrícula del estudiante.
- Cargar el período correspondiente para el proceso.
- Mostrar restricciones asociadas a la carga académica.
- Consultar materias disponibles según el contexto académico.
- Consultar docentes vinculados a las materias ofertadas.
- Validar la viabilidad de la asignación antes de guardar.
- Completar el proceso de matrícula mediante una ventana emergente de confirmación y detalle.

Validaciones y Reglas de Negocio

El sistema aplica validaciones orientadas a garantizar la integridad del proceso académico, entre ellas:

- Verificación de existencia de matrícula activa del estudiante.
- Validación de datos requeridos antes de completar la matrícula.
- Prevención de inconsistencias en la asignación de materias.
- Control de selección de materia y docente según disponibilidad.
- Validación de horarios para evitar traslapes o conflictos.
- Control de restricciones de carga académica.
- Manejo de errores controlado desde interfaz, servicios y repositorios.

Interfaz Gráfica y Experiencia de Usuario

La interfaz del Entregable No. 4 incorpora:

- Nuevas pestañas especializadas para el proceso de matrícula por materias.
- Flujo guiado para consulta y asignación.
- Combobox dinámicos y dependientes.
- Grillas con información académica relevante.
- Ventanas emergentes para completar matrícula.
- Retroalimentación visual mediante mensajes, confirmaciones y validaciones.
- Navegación consistente con el menú principal del sistema.
- Reutilización de componentes visuales existentes para mantener uniformidad.

Arquitectura y Diseño

El Entregable No. 4 refuerza la arquitectura modular del sistema mediante la incorporación de un nuevo bloque 
funcional completo para matrícula por materias:

- UI: vistas, pestañas, formularios, popups y validaciones visuales.
- Endpoints: coordinación del flujo entre interfaz, servicios y base de datos.
- Services: reglas de negocio, validaciones académicas y control del proceso.
- Repositories: acceso estructurado a la información de matrícula, materias, docentes, horarios y facturación.
- Core: reutilización de manejo de errores, sesión, conexión y auditoría.

Módulos y Componentes Incorporados en el Entregable No. 4

Se incorporan nuevos componentes organizados por capa para el módulo de matrícula por materias, incluyendo:

- Consulta de matrícula del estudiante.
- Gestión de asignación de materias.
- Relación docente-materia.
- Validación y consulta de horario por materia.
- Apoyo al proceso de facturación de matrícula.
- Popup de completado de matrícula.
- Nueva vista integrada al menú principal para el módulo de matrícula por materias.

Estado del Proyecto

Con la finalización del Entregable No. 4:

- El sistema amplía su cobertura funcional sobre el proceso académico.
- La arquitectura se mantiene estable, modular y escalable.
- El proyecto queda preparado para continuar con módulos posteriores como:
  - Notas académicas
  - Asistencia
  - Reportes avanzados
  - Procesos académicos complementarios

Estructura del Proyecto (Entregable No. 4)

SIS_Universitario/
├── app/
│   ├── endpoints/
│   │   ├── mantenimiento/
│   │   │   └── periodos_endpoints.py
│   │   ├── matriculas/
│   │   │   └── matriculas_endpoints.py
│   │   └── matriculas_materia/
│   │       ├── __init__.py
│   │       ├── consulta_matricula_estudiante_endpoints.py
│   │       ├── docente_materia_endpoints.py
│   │       ├── facturacion_matricula_endpoints.py
│   │       ├── materia_horario_endpoints.py
│   │       └── matricula_materia_endpoints.py
│   │
│   ├── repositories/
│   │   ├── mantenimiento/
│   │   │   └── periodos_repo.py
│   │   ├── matriculas/
│   │   │   └── matriculas_repo.py
│   │   └── matriculas_materia/
│   │       ├── __init__.py
│   │       ├── consulta_matricula_estudiante_repo.py
│   │       ├── docente_materia_repo.py
│   │       ├── facturacion_matricula_repo.py
│   │       ├── materia_horario_repo.py
│   │       └── matricula_materia_repo.py
│   │
│   ├── services/
│   │   ├── mantenimiento/
│   │   │   └── periodos_service.py
│   │   ├── matriculas/
│   │   │   └── matriculas_service.py
│   │   └── matriculas_materia/
│   │       ├── __init__.py
│   │       ├── consulta_matricula_estudiante_service.py
│   │       ├── docente_materia_service.py
│   │       ├── facturacion_matricula_service.py
│   │       ├── materia_horario_service.py
│   │       └── matricula_materia_service.py
│   │
│   ├── ui/
│   │   ├── mantenimientos/
│   │   │   └── periodos_tab.py
│   │   ├── matriculas/
│   │   │   ├── consulta_matriculas_tab.py
│   │   │   ├── listado_matriculas_tab.py
│   │   │   └── reporte_estudiantes_tab.py
│   │   ├── matriculas_materia/
│   │   │   ├── __init__.py
│   │   │   ├── completar_matricula_popup.py
│   │   │   ├── consulta_matricula_estudiante_tab.py
│   │   │   ├── docente_materia_tab.py
│   │   │   ├── materia_horario_tab.py
│   │   │   └── matricula_materia_tab.py
│   │   ├── transitions/
│   │   │   └── popup_slide.py
│   │   └── views/
│   │       └── matriculas_materia_view.py

Observaciones Finales

El Entregable No. 4 fortalece el SIS-Universitario al incorporar un módulo académico más específico y 
alineado con los procesos reales de matrícula universitaria.

La implementación mantiene coherencia con la arquitectura definida desde los entregables anteriores, 
favoreciendo la mantenibilidad, reutilización de código y escalabilidad del sistema.

Este entregable consolida al proyecto como una base funcional robusta para continuar con los siguientes 
módulos académicos del sistema.

----------------------------------------------------------------
ENTREGABLE No. 5
----------------------------------------------------------------

Descripción General del Entregable No. 5

El Entregable No. 5 amplía el sistema SIS-Universitario incorporando el módulo de Asistencias Académicas, 
permitiendo registrar, editar, consultar y visualizar listas de asistencia dentro del contexto académico real 
de cada grupo, materia, docente y período.

Este entregable fortalece la cobertura funcional del sistema al integrar el proceso de asistencia dentro del 
flujo académico general, reutilizando la arquitectura modular ya establecida en el proyecto y manteniendo la 
separación por capas (UI, Endpoints, Services, Repositories y Core).

A diferencia de una implementación básica de asistencias, este entregable incorpora un flujo más completo, 
permitiendo no solo registrar listas, sino también consultar listas previamente guardadas, cargarlas en modo 
edición, visualizar su detalle y trabajar con filtros académicos consistentes con la matrícula por materias.

Alcance del Entregable No. 5

- Implementación completa del módulo de Asistencias Académicas.
- Registro de listas de asistencia por período, curso, materia, docente y fecha.
- Separación del módulo en dos pestañas principales:
  - Registrar / Editar
  - Consultar listas
- Carga dinámica de períodos activos.
- Carga dependiente de cursos, materias y docentes según el contexto académico seleccionado.
- Visualización del grupo real de estudiantes matriculados en la combinación académica seleccionada.
- Clasificación de estudiantes en asistentes y ausentes.
- Control visual de estudiantes pendientes por clasificar.
- Carga de listas existentes mediante contexto académico y fecha.
- Edición de listas ya registradas.
- Consulta de listas de asistencia por filtros académicos y rango de fechas.
- Visualización de detalle completo de una lista seleccionada.
- Integración con el sistema de auditoría de movimientos.
- Integración del módulo con la navegación principal del sistema.

Gestión de Asistencias

El módulo de Asistencias permite:

- Seleccionar el período académico activo.
- Seleccionar el curso asociado al período.
- Seleccionar la materia correspondiente al curso.
- Seleccionar el docente asociado a la materia dentro del contexto académico real.
- Cargar el grupo de estudiantes matriculados en esa combinación.
- Marcar estudiantes como asistentes.
- Marcar estudiantes como ausentes.
- Mantener estudiantes pendientes si aún no han sido clasificados.
- Guardar listas nuevas de asistencia.
- Cargar listas previamente existentes para continuar o corregir su edición.
- Consultar listas generadas dentro de un contexto académico específico.
- Ver el detalle completo de una lista desde la pestaña de consulta.
- Enviar una lista desde la pestaña de consulta hacia la pestaña de edición.

Validaciones y Reglas de Negocio

El sistema aplica validaciones orientadas a garantizar la integridad del proceso de asistencias, entre ellas:

- Verificación de existencia del período seleccionado.
- Validación de existencia real del curso, materia y docente.
- Validación del contexto académico antes de cargar estudiantes.
- Consulta de estudiantes únicamente desde grupos realmente matriculados.
- Prevención de guardado sin contexto académico completo.
- Validación de fecha obligatoria para la lista.
- Validación de que exista al menos un estudiante clasificado antes de guardar.
- Confirmación de guardado cuando todavía existan estudiantes pendientes.
- Control de carga de listas existentes por llave de negocio:
  - período
  - curso
  - materia
  - docente
  - fecha de clase
- Control de errores desde interfaz, endpoints, services y repositories.
- Protección del flujo mediante manejo controlado de excepciones.

Interfaz Gráfica y Experiencia de Usuario

La interfaz del Entregable No. 5 incorpora:

- Un módulo principal de asistencias integrado al menú lateral del sistema.
- Un contenedor principal con pestañas para separar el flujo de registro y consulta.
- Pestaña "Registrar / Editar" con:
  - filtros académicos
  - resumen del grupo
  - lista de estudiantes disponibles
  - lista de asistentes
  - lista de ausentes
  - acciones para guardar, limpiar y refrescar
- Pestaña "Consultar listas" con:
  - filtros por período, curso, materia, docente y rango de fechas
  - grilla de resultados
  - resumen contextual de la lista seleccionada
  - acciones para ver detalle, cargar en edición y refrescar
- Popup de detalle de lista con encabezado, resumen y detalle por estudiante.
- Integración visual consistente con el resto del sistema.
- Mensajes de advertencia, confirmación e información para acompañar el flujo del usuario.

Arquitectura y Diseño

El Entregable No. 5 mantiene y refuerza la arquitectura modular del sistema mediante la incorporación de un 
bloque funcional completo para asistencias:

- UI:
  - contenedor principal del módulo de asistencias
  - tab de registro / edición
  - tab de consulta
  - popup de detalle
  - validaciones visuales y resumen de estado
- Endpoints:
  - coordinación entre interfaz, lógica de negocio, auditoría y acceso a datos
- Services:
  - validaciones académicas
  - reglas de negocio
  - normalización y control del proceso de asistencias
- Repositories:
  - acceso estructurado a períodos, cursos, materias, docentes, matrícula por materia y listas de asistencia
- Core:
  - conexión a base de datos
  - manejo de errores
  - auditoría
  - sesión

Módulos y Componentes Incorporados en el Entregable No. 5

Se incorporan nuevos componentes organizados por capa para el módulo de asistencias, incluyendo:

- Endpoint de asistencias.
- Repositorio de asistencias.
- Servicio de asistencias.
- Contenedor principal del módulo de asistencias.
- Tab de registro y edición de listas.
- Tab de consulta de listas.
- Popup de detalle de lista.
- Integración del módulo al menú principal del sistema.

Estructura del Proyecto (Entregable No. 5)

SIS_Universitario/
├── app/
│   ├── endpoints/
│   │   └── asistencias/
│   │       ├── __init__.py
│   │       └── asistencias_endpoints.py
│   │
│   ├── repositories/
│   │   └── asistencias/
│   │       ├── __init__.py
│   │       └── asistencias_repo.py
│   │
│   ├── services/
│   │   └── asistencias/
│   │       ├── __init__.py
│   │       └── asistencias_service.py
│   │
│   └── ui/
│       ├── asistencias/
│       │   ├── __init__.py
│       │   ├── asistencia_registro_tab.py
│       │   ├── asistencia_consulta_tab.py
│       │   └── asistencias_tab.py
│       │
│       └── views/
│           └── main_menu_view.py

Flujo Funcional del Módulo

El flujo principal del módulo de asistencias funciona de la siguiente manera:

1. El usuario accede al módulo desde el menú lateral principal.
2. Selecciona el contexto académico:
   - período
   - curso
   - materia
   - docente
3. El sistema carga los estudiantes del grupo real matriculado.
4. El usuario clasifica estudiantes como asistentes o ausentes.
5. El sistema actualiza el resumen:
   - total grupo
   - asistentes
   - ausentes
   - registrados
   - pendientes
6. El usuario guarda la lista.
7. Posteriormente puede:
   - cargar una lista existente
   - consultar listas del mismo contexto
   - abrir el detalle de una lista
   - enviar una lista a edición desde la pestaña de consulta

Estado del Proyecto

Con la finalización del Entregable No. 5:

- El sistema amplía su cobertura funcional sobre procesos académicos clave.
- El módulo de asistencias ya no se limita a registro básico, sino que incluye consulta y edición.
- La arquitectura se mantiene estable, modular y escalable.
- El proyecto continúa consolidándose como una solución académica integral.
- El sistema queda preparado para futuros módulos como:
  - Notas académicas
  - Reportes avanzados
  - Indicadores de rendimiento
  - Procesos complementarios de control académico

Observaciones Finales

El Entregable No. 5 fortalece significativamente el SIS-Universitario al incorporar un flujo completo de 
listas de asistencia, alineado con la lógica académica real del sistema y con integración directa a la 
matrícula por materias.

La implementación mantiene coherencia con la arquitectura definida desde los entregables anteriores, 
favoreciendo la mantenibilidad, reutilización de código, validación centralizada, trazabilidad mediante 
auditoría y escalabilidad del sistema.

Este entregable consolida aún más la base funcional del proyecto y deja preparado el sistema para continuar 
con módulos académicos de mayor profundidad y análisis.

Autor

José Rodolfo Morales Calderón
Curso: Programación III
Institución: Colegio Universitario de Cartago (CUC)
Repositorio Github (Publico): https://github.com/JoseMoralesC/SIS_Universitario