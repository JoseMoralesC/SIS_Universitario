Entregable No. 1  
## Sistema de Gestión Académica — SIS-Universitario

**Curso:** Programación III  
**Lenguaje:** Python  
**Motor de Base de Datos:** SQL Server Express  
**Base de Datos:** Universidad  
**Estudiante:** José Rodolfo Morales Calderón  
**Institución:** Colegio Universitario de Cartago (CUC)

---

# 1. Descripción General

El **Sistema de Gestión Académica (SIS-Universitario)** es un proyecto desarrollado en Python que utiliza **SQL Server Express** como motor de base de datos, con el objetivo de administrar procesos académicos universitarios.

Este **Entregable No. 1** se enfoca exclusivamente en la **conexión, autenticación y validación de usuarios**, cumpliendo con los requisitos establecidos en el enunciado del proyecto.

---

# 2. Objetivo del Entregable No. 1

- Establecer conexión segura entre Python y SQL Server Express.
- Validar credenciales mediante autenticación SQL.
- Verificar la existencia del usuario en la tabla `Usuarios`.
- Implementar una ventana de login funcional con interfaz gráfica.
- Manejar correctamente errores y mensajes solicitados.
- Preparar la base estructural para entregables posteriores.

---

# 3. Alcance del Entregable

# Incluido en este entregable

- Conexión a SQL Server Express  
- Autenticación por usuario y contraseña  
- Validación de usuarios en SQL Server  
- Validación de usuarios en tabla `Usuarios`  
- Mensaje obligatorio cuando el usuario no está registrado en la tabla  
- Interfaz gráfica de Login (Tkinter)  
- Imagen dinámica por tipo de usuario  
- Manejo de errores controlado  
- Estructura modular del proyecto  

 No incluido (corresponde a entregables posteriores)

- Matrícula de estudiantes  
- Registro de notas  
- Control de asistencia  
- Facturación  
- Reportes académicos  

---

## 4. Seguridad del Sistema

El acceso al sistema se realiza mediante **SQL Authentication**, validando:

1. Que el usuario y contraseña existan en SQL Server.
2. Que el usuario exista en la tabla `Usuarios`.

Si el usuario existe en SQL Server pero **no** en la tabla `Usuarios`, el sistema muestra el mensaje exacto solicitado:

> **“Usuario con permiso en SQL, pero, no registrado en la tabla de la Base de Datos”**

---

## 5. Interfaz Gráfica de Login

La ventana de login incluye:

- Campo Usuario
- Campo Contraseña
- Botón Validar
- Botón Cancelar
- Imagen dinámica según el usuario digitado

### Imágenes utilizadas

- `Administrador.jpg`
- `Auditor.jpg`
- `Operador.jpg`
- `default.png` (imagen por defecto)

La imagen cambia automáticamente al escribir el nombre de usuario.

---

## 6. Base de Datos

- **Nombre:** Universidad  
- **Motor:** SQL Server Express  
- **Instancia:** localhost\SQLEXPRESS  

### Tablas creadas para cumplir el entregable

- Usuarios  
- Tipo_Usuario  
- Profesiones  
- Docentes  
- Cursos_Programas  
- Materias  
- Estudiantes  
- Matricula_Curso  
- Matricula_Materia  
- Formas_Pago  
- Auditoria  
- Movimientos_Auditoria  

El diseño de la base de datos sigue criterios de normalización y está preparado para ampliarse en entregables futuros.

---

## 7. Usuarios del Sistema

Se crearon usuarios en SQL Server con autenticación SQL:

- Administrador
- Auditor
- Operador
- Estandar

Cada usuario:
- Existe como Login en SQL Server.
- Existe en la tabla `Usuarios`.
- Tiene permisos controlados según su rol.

---

## 8. Estructura del Proyecto

