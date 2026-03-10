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
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base_dir, ".env")
        load_dotenv(env_path)

        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        port_env = os.getenv("DB_PORT", "3306")
        self.port = int(port_env) if port_env.isdigit() else 3306

    def _get_connection(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db_name,
            port=self.port,
            autocommit=True  # Wichtig für sofortige Updates
        )

    def get_books(self, search_text="", sort_option="ISBN"):
        """Holt Daten aus der View 'v_bestand_titel' (von Jaclyn)."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Wir nutzen die View, um Titel und die Summe der Exemplare zu erhalten
                sql = "SELECT isbn, titel, verlag, auflage, anzahl_exemplare FROM v_bestand_titel"
                params = []

                if search_text:
                    sql += " WHERE titel LIKE %s OR isbn LIKE %s OR verlag LIKE %s"
                    like_val = f"%{search_text}%"
                    params = [like_val, like_val, like_val]

                # Sortier-Mapping (Spaltennamen der View)
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

    def add_book(self, isbn, titel, verlag, auflage, bestand):
        """Fügt einen Titel ein und erstellt die gewünschte Anzahl an Exemplaren."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Neue Titel_ID generieren
                cursor.execute("SELECT IFNULL(MAX(titel_id), 0) + 1 FROM BuchTitel")
                t_id = cursor.fetchone()[0]

                # 2. In BuchTitel schreiben
                sql_titel = "INSERT INTO BuchTitel (titel_id, titel, verlag, auflage, isbn) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_titel, (t_id, titel, verlag, auflage, isbn))

                # 3. Physische Exemplare in BuchExemplar anlegen
                for i in range(1, int(bestand) + 1):
                    cursor.execute("SELECT IFNULL(MAX(exemplar_id), 0) + 1 FROM BuchExemplar")
                    e_id = cursor.fetchone()[0]
                    qr = f"QR-{isbn}-{i}"  # Beispielhafter QR-Code Generator
                    sql_ex = "INSERT INTO BuchExemplar (exemplar_id, titel_id, exemplar_nr, qr_code) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql_ex, (e_id, t_id, i, qr))
        finally:
            conn.close()

    def update_stock(self, isbn, delta_or_new):
        """Passt den Bestand an, indem Exemplare hinzugefügt oder entfernt werden."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Titel_ID zur ISBN finden
                cursor.execute("SELECT titel_id FROM BuchTitel WHERE isbn = %s", (isbn,))
                res = cursor.fetchone()
                if not res: return
                t_id = res[0]

                # Aktuellen Bestand zählen
                cursor.execute("SELECT COUNT(*) FROM BuchExemplar WHERE titel_id = %s", (t_id,))
                current_count = cursor.fetchone()[0]

                # Hier nehmen wir an, delta_or_new ist der NEUE Zielwert (wie aus deiner GUI)
                target = int(delta_or_new)

                if target > current_count:
                    # Exemplare hinzufügen
                    for i in range(current_count + 1, target + 1):
                        cursor.execute("SELECT IFNULL(MAX(exemplar_id), 0) + 1 FROM BuchExemplar")
                        e_id = cursor.fetchone()[0]
                        qr = f"QR-{isbn}-{i}"
                        cursor.execute(
                            "INSERT INTO BuchExemplar (exemplar_id, titel_id, exemplar_nr, qr_code) VALUES (%s, %s, %s, %s)",
                            (e_id, t_id, i, qr))
                elif target < current_count:
                    # Das neuste Exemplar löschen (einfachste Logik)
                    diff = current_count - target
                    cursor.execute("DELETE FROM BuchExemplar WHERE titel_id = %s ORDER BY exemplar_id DESC LIMIT %s",
                                   (t_id, diff))
        finally:
            conn.close()

    def delete_book(self, isbn):
        """Löscht den Titel (Kaskadierung in DB löscht automatisch Exemplare)."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Dank ON DELETE CASCADE im SQL-Skript löscht dies auch alle Exemplare
                sql = "DELETE FROM BuchTitel WHERE isbn = %s"
                cursor.execute(sql, (isbn,))
        finally:
            conn.close()