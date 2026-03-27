# Sistema de Gestión Académica

## SIS-Universitario

### Descripción General del Proyecto

El **SIS-Universitario** es un sistema de información académica desarrollado en Python, con integración directa a una base de datos en SQL Server Express, cuyo objetivo es gestionar de manera estructurada, segura y eficiente los procesos académicos fundamentales de una institución educativa.

El sistema ha sido diseñado bajo una arquitectura modular por capas, permitiendo una separación clara de responsabilidades entre la interfaz de usuario, la lógica de negocio, la orquestación de procesos y el acceso a datos. Esta estructura no solo facilita el mantenimiento del sistema, sino que también permite su escalabilidad hacia funcionalidades más complejas.

A lo largo de su desarrollo, el sistema ha evolucionado desde un módulo básico de autenticación hasta convertirse en una solución robusta que integra seguridad avanzada, control de accesos, auditoría completa de operaciones y múltiples módulos académicos interconectados.

---

### Propósito del Sistema

El propósito principal del SIS-Universitario es proporcionar una plataforma que permita:

* Gestionar usuarios y su acceso al sistema.
* Administrar información académica (docentes, estudiantes, cursos y materias).
* Controlar procesos de matrícula académica.
* Registrar y consultar asistencias.
* Mantener trazabilidad completa de las operaciones realizadas.
* Garantizar seguridad en el acceso y uso del sistema.

---

### Arquitectura del Sistema

El sistema está construido bajo una arquitectura en capas, lo que permite un alto nivel de organización y desacoplamiento:

* **UI (Interfaz de Usuario):** Manejo de ventanas, formularios, navegación y experiencia del usuario.
* **Endpoints:** Coordinación de las operaciones entre la interfaz y la lógica del sistema.
* **Services:** Implementación de reglas de negocio y validaciones.
* **Repositories:** Acceso directo a la base de datos mediante consultas estructuradas.
* **Core:** Configuración general, manejo de sesión, auditoría y control de errores.

Esta arquitectura permite que cada componente del sistema tenga una responsabilidad clara, mejorando la mantenibilidad y facilitando futuras extensiones.

---

### Seguridad del Sistema

Uno de los pilares más importantes del SIS-Universitario es su enfoque en la seguridad.

El sistema implementa un modelo de seguridad basado en múltiples capas que incluye:

#### Autenticación

* Validación de usuarios contra SQL Server.
* Verificación de existencia en la base de datos del sistema.
* Manejo de credenciales mediante mecanismos seguros.

#### Gestión de Usuarios

* Almacenamiento de contraseñas utilizando:

  * Hash
  * Salt
  * Algoritmos configurables
* Control de intentos fallidos de acceso.
* Bloqueo automático de cuentas ante múltiples intentos incorrectos.
* Control de expiración y cambio de contraseña.

#### Control de Accesos por Roles

El sistema implementa un modelo de seguridad basado en roles que permite:

* Asignar uno o múltiples roles a cada usuario.
* Definir un rol principal.
* Controlar el acceso a módulos y funcionalidades según permisos.

#### Seguridad en la Interfaz

A nivel de experiencia de usuario, la seguridad se refleja mediante:

* Ocultamiento dinámico de botones y opciones no autorizadas.
* Restricción de acceso a módulos según el rol.
* Prevención de ejecución de acciones sin permisos.

Este enfoque garantiza que el usuario solo pueda visualizar y ejecutar aquello que le corresponde, reduciendo riesgos y mejorando la integridad del sistema.

---

### Auditoría de Operaciones

El sistema incorpora un módulo de auditoría completamente integrado que permite registrar todas las acciones relevantes realizadas por los usuarios.

Cada operación importante genera un registro que incluye:

* Usuario que ejecutó la acción.
* Fecha y hora exacta.
* Tipo de movimiento realizado.
* Identificador del registro afectado.

La auditoría es gestionada desde la capa de endpoints, asegurando que todas las operaciones críticas queden registradas de forma automática y consistente.

Este mecanismo proporciona:

* Trazabilidad completa del sistema.
* Control sobre cambios realizados.
* Base para procesos de revisión o auditoría externa.

---

### Módulos Académicos

El sistema cuenta con múltiples módulos funcionales que interactúan entre sí:

#### Mantenimientos Académicos

Permiten la gestión de:

* Docentes
* Estudiantes
* Cursos / Programas
* Materias

Incluyen operaciones CRUD completas, validaciones y manejo de estados.

---

#### Gestión de Matrículas

El sistema permite:

* Registrar matrículas por curso.
* Validar estudiantes elegibles.
* Evitar duplicados.
* Consultar matrículas existentes.
* Generar reportes asociados.

---

#### Matrícula por Materias

Permite una gestión más detallada:

* Asignación de materias a estudiantes matriculados.
* Validación de horarios.
* Relación docente-materia.
* Control de carga académica.
* Apoyo al proceso de facturación.

---

#### Módulo de Asistencias

Permite registrar y consultar la asistencia de estudiantes:

* Registro por curso, materia y docente.
* Clasificación de estudiantes (asistencia/ausencia).
* Registro de observaciones.
* Consulta histórica de listas.

Este módulo sigue un flujo guiado que asegura la consistencia de los datos.

---

### Experiencia de Usuario (UI/UX)

El sistema ha sido diseñado con un enfoque claro en la experiencia del usuario.

Entre las principales características destacan:

* Interfaz gráfica desarrollada en Tkinter.
* Navegación mediante menús y pestañas.
* Formularios dinámicos con validaciones en tiempo real.
* Uso de combobox dependientes.
* Grillas (TreeView) para visualización de datos.
* Ventanas emergentes (popups) para interacción.

#### Perfil de Usuario

Se incorpora un componente de perfil que permite:

* Visualizar información del usuario activo.
* Mejorar la interacción con el sistema.
* Integrarse con el modelo de roles y permisos.

---

### Dinamismo de los Datos

El sistema se caracteriza por un manejo altamente dinámico de la información:

* Carga de datos en tiempo real desde la base de datos.
* Uso de lookups dinámicos para poblar interfaces.
* Filtrado de información según contexto (curso, docente, estudiante, etc.).
* Actualización automática de vistas según interacción del usuario.
* Prevención de inconsistencias mediante validaciones en múltiples capas.

Este dinamismo permite que el sistema responda de manera eficiente a las acciones del usuario, manteniendo siempre la integridad de los datos.

---

### Manejo de Errores

El sistema implementa un manejo estructurado de errores:

* Captura de excepciones en todas las capas.
* Mensajes claros para el usuario.
* Separación entre errores técnicos y errores de negocio.
* Prevención de fallos críticos en la aplicación.

---

### Estado del Proyecto

El SIS-Universitario ha alcanzado un nivel de madurez alto, integrando:

* Seguridad avanzada.
* Control de accesos por roles.
* Auditoría completa.
* Múltiples módulos académicos.
* Interfaz dinámica y orientada al usuario.

El sistema se encuentra preparado para:

* Escalar hacia nuevos módulos.
* Integrarse con otros sistemas.
* Evolucionar hacia una solución empresarial completa.

---

### Conclusión

El SIS-Universitario representa una solución integral para la gestión académica, destacándose por su arquitectura modular, su enfoque en la seguridad y su capacidad de adaptación a diferentes escenarios.

Su diseño permite no solo cumplir con los requerimientos actuales, sino también servir como base sólida para desarrollos futuros, posicionándolo como un sistema escalable, mantenible y alineado con buenas prácticas de desarrollo de software.
