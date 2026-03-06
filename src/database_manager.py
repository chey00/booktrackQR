# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: database_manager.py
# Autoren: René Bezold, Denis Sukkau, Georg Zinn
# Zweck: Zentrale Schnittstelle zur MariaDB auf dem Raspberry Pi.
#        Übernimmt alle CRUD-Operationen (Create, Read, Update, Delete)
#        für die Buchverwaltung.
# ------------------------------------------------------------------------------

import pymysql
import os
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        # Pfad-Absicherung: Sucht die .env Datei im selben Verzeichnis wie diese Datei
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base_dir, ".env")

        # Lädt die Variablen aus der .env Datei
        load_dotenv(env_path)

        # Datenbank-Parameter aus Umgebungsvariablen zuweisen
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")

        # Port mit Fallback auf 3306 (Standard MariaDB Port)
        port_env = os.getenv("DB_PORT", "3306")
        self.port = int(port_env) if port_env.isdigit() else 3306

    def _get_connection(self):
        """Erstellt eine frische Verbindung zur MariaDB."""
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db_name,
            port=self.port,
            cursorclass=pymysql.cursors.Cursor # Standard-Cursor für Tupel-Daten
        )

    def get_books(self, search_text="", sort_option="ISBN"):
        """Holt die Bücher basierend auf Suche und Sortierung."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Basis-Query
                sql = "SELECT isbn, titel, verlag, auflage, bestand FROM buecher"
                params = []

                # Suche (Filter)
                if search_text:
                    sql += " WHERE titel LIKE %s OR isbn LIKE %s OR verlag LIKE %s"
                    like_val = f"%{search_text}%"
                    params = [like_val, like_val, like_val]

                # Sortierung
                order_map = {
                    "Titel": "titel ASC",
                    "Verlag": "verlag ASC",
                    "Auflage": "auflage ASC",
                    "Sortieren nach: ISBN": "isbn ASC"
                }
                sort_sql = order_map.get(sort_option, "isbn ASC")
                sql += f" ORDER BY {sort_sql}"

                cursor.execute(sql, params)
                return cursor.fetchall()
        finally:
            conn.close()

    def update_stock(self, isbn, new_stock):
        """Aktualisiert den Bestand eines Buches (für + / - Buttons)."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE buecher SET bestand = %s WHERE isbn = %s"
                cursor.execute(sql, (new_stock, isbn))
                conn.commit()
        finally:
            conn.close()

    def delete_book(self, isbn):
        """Löscht ein Buch (für den Papierkorb-Button)."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM buecher WHERE isbn = %s"
                cursor.execute(sql, (isbn,))
                conn.commit()
        finally:
            conn.close()

    def add_book(self, isbn, titel, verlag, auflage, bestand):
        """Fügt ein neues Buch hinzu (für den 'Buch hinzufügen' Dialog)."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO buecher (isbn, titel, verlag, auflage, bestand) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (isbn, titel, verlag, auflage, bestand))
                conn.commit()
        finally:
            conn.close()