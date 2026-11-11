import sqlite3
import tempfile
import unittest
from pathlib import Path

from examples.database import (
    ConversationRepository,
    ConversationService,
    PersistenceError,
    RecordNotFoundError,
    create_schema,
    open_database,
)


class ConversationDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        create_schema(self.connection)
        self.addCleanup(self.connection.close)
        self.repository = ConversationRepository(self.connection)
        self.service = ConversationService(self.connection, self.repository)

    def test_create_and_retrieve_conversation_and_messages(self):
        conversation_id = self.service.create_conversation(
            "Recetas ficticias",
            [
                ("user", "Probar una receta de sopa."),
                ("assistant", "Anotar ingredientes y pasos."),
            ],
        )

        conversation = self.repository.get_conversation(conversation_id)
        messages = self.repository.list_messages(conversation_id)

        self.assertEqual(conversation["title"], "Recetas ficticias")
        self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
        self.assertEqual(messages[0]["conversation_id"], conversation_id)

    def test_filtered_conversations_are_ordered_by_id_descending(self):
        older_id = self.service.create_conversation("Ideas de jardín")
        newer_id = self.service.create_conversation("Jardín de invierno")
        self.service.create_conversation("Lista de lectura")

        results = self.repository.list_conversations("Jardín")

        self.assertEqual(
            [row["id"] for row in results],
            [newer_id, older_id],
        )

    def test_update_and_delete_cascade_messages(self):
        conversation_id = self.service.create_conversation(
            "Título inicial",
            [("user", "Mensaje de prueba.")],
        )

        self.service.update_title(conversation_id, "Título actualizado")
        self.assertEqual(
            self.repository.get_conversation(conversation_id)["title"],
            "Título actualizado",
        )

        self.service.delete_conversation(conversation_id)
        self.assertIsNone(self.repository.get_conversation(conversation_id))
        self.assertEqual(self.repository.list_messages(conversation_id), [])

    def test_update_and_delete_message(self):
        conversation_id = self.service.create_conversation(
            "Mensajes editables",
            [("user", "Texto inicial.")],
        )
        message_id = self.repository.list_messages(conversation_id)[0]["id"]

        self.service.update_message(message_id, "assistant", "Texto actualizado.")
        updated = self.repository.list_messages(conversation_id)[0]
        self.assertEqual(updated["role"], "assistant")
        self.assertEqual(updated["content"], "Texto actualizado.")

        self.service.delete_message(message_id)
        self.assertEqual(self.repository.list_messages(conversation_id), [])

    def test_join_search_returns_conversation_title(self):
        self.service.create_conversation(
            "Proyecto de cerámica",
            [("user", "Buscar esmaltes azules.")],
        )

        results = self.repository.search_messages("azules")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["conversation_title"], "Proyecto de cerámica")
        self.assertEqual(results[0]["role"], "user")

    def test_database_constraints_reject_invalid_rows(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.create_conversation(" ")

        conversation_id = self.repository.create_conversation("Válida")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.add_message(conversation_id, "system", "Contenido")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.add_message(999, "user", "Mensaje huérfano")

    def test_service_wraps_foreign_key_violation(self):
        with self.assertRaises(PersistenceError) as raised:
            self.service.add_message(999, "user", "Mensaje sin conversación")

        self.assertIsInstance(raised.exception.__cause__, sqlite3.IntegrityError)

    def test_failed_initial_message_rolls_back_conversation_and_messages(self):
        with self.assertRaises(ValueError):
            self.service.create_conversation(
                "Operación atómica",
                [
                    ("user", "Este mensaje se insertaría primero."),
                    ("unknown", "Este mensaje no es válido."),
                ],
            )

        self.assertEqual(self.repository.list_conversations(), [])
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            0,
        )

    def test_invalid_inputs_and_missing_records_raise_clear_errors(self):
        with self.assertRaises(ValueError):
            self.service.create_conversation(" ")
        with self.assertRaises(ValueError):
            self.service.add_message(1, "user", " ")
        with self.assertRaises(RecordNotFoundError):
            self.service.update_title(999, "Nuevo título")
        with self.assertRaises(RecordNotFoundError):
            self.service.delete_conversation(999)

    def test_parameterized_search_treats_sql_as_data(self):
        self.service.create_conversation(
            "Conversación segura",
            [("user", "Texto ordinario.")],
        )

        results = self.repository.search_messages("' OR 1=1 --")
        tables = self.connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name IN ('conversations', 'messages')
            """
        ).fetchall()

        self.assertEqual(results, [])
        self.assertEqual({row["name"] for row in tables}, {"conversations", "messages"})

    def test_file_database_persists_after_reopening(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = Path(temporary) / "conversations.sqlite3"
            with open_database(database_path) as connection:
                repository = ConversationRepository(connection)
                service = ConversationService(connection, repository)
                conversation_id = service.create_conversation(
                    "Persistencia temporal",
                    [("assistant", "El archivo se puede reabrir.")],
                )

            with open_database(database_path) as connection:
                repository = ConversationRepository(connection)
                conversation = repository.get_conversation(conversation_id)
                messages = repository.list_messages(conversation_id)

            self.assertEqual(conversation["title"], "Persistencia temporal")
            self.assertEqual(len(messages), 1)


if __name__ == "__main__":
    unittest.main()
