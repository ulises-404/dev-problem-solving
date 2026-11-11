"""Persistencia de conversaciones ficticias con SQLite."""

import argparse
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL
        REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages(conversation_id, id);
"""


class PersistenceError(Exception):
    """Una operación no pudo respetar la integridad de los datos."""


class RecordNotFoundError(LookupError):
    """No existe el registro solicitado."""


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)


@contextmanager
def open_database(path: str | Path) -> Iterator[sqlite3.Connection]:
    """Abre una base, activa claves foráneas y garantiza el cierre."""
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        create_schema(connection)
        yield connection
    finally:
        connection.close()


class ConversationRepository:
    """Operaciones SQL; no contiene reglas de negocio."""

    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def create_conversation(self, title: str) -> int:
        cursor = self._connection.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title,),
        )
        return int(cursor.lastrowid)

    def get_conversation(self, conversation_id: int) -> dict | None:
        row = self._connection.execute(
            """
            SELECT id, title, created_at
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def list_conversations(self, title_filter: str | None = None) -> list[dict]:
        if title_filter is None:
            rows = self._connection.execute(
                """
                SELECT id, title, created_at
                FROM conversations
                ORDER BY id DESC
                """
            )
        else:
            rows = self._connection.execute(
                """
                SELECT id, title, created_at
                FROM conversations
                WHERE title LIKE ?
                ORDER BY id DESC
                """,
                (f"%{title_filter}%",),
            )
        return [dict(row) for row in rows.fetchall()]

    def update_title(self, conversation_id: int, title: str) -> None:
        cursor = self._connection.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (title, conversation_id),
        )
        if cursor.rowcount == 0:
            raise RecordNotFoundError("No existe la conversación.")

    def delete_conversation(self, conversation_id: int) -> None:
        cursor = self._connection.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        if cursor.rowcount == 0:
            raise RecordNotFoundError("No existe la conversación.")

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content),
        )
        return int(cursor.lastrowid)

    def update_message(self, message_id: int, role: str, content: str) -> None:
        cursor = self._connection.execute(
            "UPDATE messages SET role = ?, content = ? WHERE id = ?",
            (role, content, message_id),
        )
        if cursor.rowcount == 0:
            raise RecordNotFoundError("No existe el mensaje.")

    def delete_message(self, message_id: int) -> None:
        cursor = self._connection.execute(
            "DELETE FROM messages WHERE id = ?",
            (message_id,),
        )
        if cursor.rowcount == 0:
            raise RecordNotFoundError("No existe el mensaje.")

    def list_messages(self, conversation_id: int) -> list[dict]:
        rows = self._connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        )
        return [dict(row) for row in rows.fetchall()]

    def search_messages(self, text_filter: str) -> list[dict]:
        rows = self._connection.execute(
            """
            SELECT
                m.id AS message_id,
                c.id AS conversation_id,
                c.title AS conversation_title,
                m.role,
                m.content,
                m.created_at
            FROM messages AS m
            JOIN conversations AS c ON c.id = m.conversation_id
            WHERE m.content LIKE ?
            ORDER BY c.id DESC, m.id ASC
            """,
            (f"%{text_filter}%",),
        )
        return [dict(row) for row in rows.fetchall()]


class ConversationService:
    """Validación de negocio y coordinación de transacciones."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        repository: ConversationRepository,
    ):
        self._connection = connection
        self._repository = repository

    def create_conversation(
        self,
        title: str,
        initial_messages: Iterable[tuple[str, str]] = (),
    ) -> int:
        self._validate_text(title, "title")
        try:
            with self._connection:
                conversation_id = self._repository.create_conversation(title)
                for role, content in initial_messages:
                    self._validate_message(role, content)
                    self._repository.add_message(conversation_id, role, content)
        except sqlite3.IntegrityError as error:
            raise PersistenceError(
                "No se pudo crear la conversación por una restricción de datos."
            ) from error
        return conversation_id

    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        self._validate_message(role, content)
        try:
            with self._connection:
                return self._repository.add_message(
                    conversation_id, role, content
                )
        except sqlite3.IntegrityError as error:
            raise PersistenceError(
                "No se pudo guardar el mensaje por una restricción de datos."
            ) from error

    def update_message(self, message_id: int, role: str, content: str) -> None:
        self._validate_message(role, content)
        with self._connection:
            self._repository.update_message(message_id, role, content)

    def delete_message(self, message_id: int) -> None:
        with self._connection:
            self._repository.delete_message(message_id)

    def update_title(self, conversation_id: int, title: str) -> None:
        self._validate_text(title, "title")
        with self._connection:
            self._repository.update_title(conversation_id, title)

    def delete_conversation(self, conversation_id: int) -> None:
        with self._connection:
            self._repository.delete_conversation(conversation_id)

    def _validate_message(self, role: str, content: str) -> None:
        if role not in ("user", "assistant"):
            raise ValueError("role debe ser user o assistant")
        self._validate_text(content, "content")

    @staticmethod
    def _validate_text(value: str, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} debe ser texto no vacío")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "database",
        nargs="?",
        type=Path,
        default=Path("conversations.sqlite3"),
        help="archivo SQLite (predeterminado: conversations.sqlite3)",
    )
    arguments = parser.parse_args()

    with open_database(arguments.database) as connection:
        repository = ConversationRepository(connection)
        service = ConversationService(connection, repository)
        conversation_id = service.create_conversation(
            "Plan de huerta",
            [
                ("user", "Organizar un calendario de riego."),
                ("assistant", "Separar las tareas por semana."),
            ],
        )
        print(f"Conversación creada: {conversation_id}")
        for message in repository.list_messages(conversation_id):
            print(f"{message['role']}: {message['content']}")


if __name__ == "__main__":
    main()
