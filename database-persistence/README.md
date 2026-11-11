# Persistencia y gestión de datos con SQLite

## 1. Contexto

Una aplicación pequeña necesita conservar conversaciones y mensajes entre
ejecuciones, consultar su contenido y mantener la relación entre ambos tipos de
registro sin incorporar un ORM ni un servicio externo.

## 2. Problema

Guardar cada registro sin un esquema definido puede producir mensajes huérfanos,
datos incompletos y consultas difíciles de mantener. También es importante que
una operación compuesta no deje cambios parciales si uno de sus pasos falla.

## 3. Análisis

El ejemplo separa las sentencias SQL del flujo de negocio. Un repositorio
encapsula el acceso relacional y un servicio valida entradas y agrupa operaciones
que deben confirmarse o revertirse como una unidad.

## 4. Diseño de datos

```text
conversations
  id (PK)
  title
  created_at
       1
       |
       | conversation_id (FK)
       *
messages
  id (PK)
  conversation_id
  role
  content
  created_at
```

Cada conversación tiene cero o más mensajes. La clave foránea usa
`ON DELETE CASCADE`; las restricciones `NOT NULL` y `CHECK` impiden títulos o
contenidos vacíos y roles fuera del conjunto admitido.

## 5. Decisiones e implementación

[database.py](./examples/database.py) utiliza `sqlite3` de la biblioteca estándar.
`ConversationRepository` concentra SQL parametrizado para crear, consultar,
actualizar y borrar conversaciones y mensajes. `ConversationService` aplica
validaciones de negocio y coordina operaciones transaccionales.

Las búsquedas enlazan los valores como parámetros (`?`), incluida la consulta
`JOIN` que devuelve mensajes junto al título de su conversación. No se concatena
entrada del usuario en sentencias SQL. `open_database` activa las claves
foráneas y cierra la conexión incluso si ocurre un error.

La creación de una conversación con sus mensajes iniciales se ejecuta en una
transacción. Si un mensaje no es válido, SQLite revierte también la conversación
recién insertada. Las violaciones de integridad se exponen como
`PersistenceError`, conservando la excepción SQLite como causa; los registros
inexistentes producen `RecordNotFoundError`.

## 6. Consultas SQL utilizadas

- `INSERT` para conversaciones y mensajes.
- `SELECT ... WHERE ... ORDER BY ...` para filtrar títulos y ordenar mensajes.
- `JOIN` entre conversaciones y mensajes para buscar texto y mostrar su título.
- `UPDATE` para cambiar títulos.
- `DELETE` con borrado en cascada de mensajes relacionados.

## 7. Ejecución y validación

Desde la raíz del repositorio:

```powershell
python database-persistence/examples/database.py
python -m unittest discover -s database-persistence -p "test_*.py"
```

El programa de ejemplo crea `conversations.sqlite3` en el directorio actual y
agrega una conversación ficticia. Las pruebas utilizan bases en memoria o un
directorio temporal que se elimina al terminar; no modifican esa base de
demostración.

Las **11 pruebas** cubren CRUD de conversaciones y mensajes, filtros, orden,
`JOIN`, claves foráneas, restricciones, rollback, validación de entradas y
reapertura de un archivo SQLite temporal.

## 8. Aprendizajes

- Modelar una relación uno-a-muchos con claves y restricciones relacionales.
- Separar responsabilidades de acceso a datos y coordinación de negocio.
- Parametrizar consultas y usar transacciones para evitar escrituras parciales.
- Probar persistencia real sin dejar datos de prueba residuales.
