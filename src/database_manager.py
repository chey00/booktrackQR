# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: database_manager.py
# Autoren: René Bezold, Denis Sukkau, Georg Zinn
# Zweck: Zentrale Schnittstelle zur MariaDB auf dem Raspberry Pi.
#        CRUD-Operationen (Create, Read, Update, Delete)
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
            autocommit=True
        )

    # --- BUCHVERWALTUNG ---

    def get_books(self, search_text="", sort_option="ISBN"):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT isbn, titel, verlag, auflage, anzahl_exemplare FROM v_bestand_titel"
                params = []
                if search_text:
                    sql += " WHERE titel LIKE %s OR isbn LIKE %s OR verlag LIKE %s"
                    like_val = f"%{search_text}%"
                    params = [like_val, like_val, like_val]

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
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT IFNULL(MAX(titel_id), 0) + 1 FROM BuchTitel")
                t_id = cursor.fetchone()[0]
                sql_titel = "INSERT INTO BuchTitel (titel_id, titel, verlag, auflage, isbn) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_titel, (t_id, titel, verlag, auflage, isbn))

                for i in range(1, int(bestand) + 1):
                    cursor.execute("SELECT IFNULL(MAX(exemplar_id), 0) + 1 FROM BuchExemplar")
                    e_id = cursor.fetchone()[0]
                    qr = f"QR-{isbn}-{i}"
                    sql_ex = "INSERT INTO BuchExemplar (exemplar_id, titel_id, exemplar_nr, qr_code) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql_ex, (e_id, t_id, i, qr))
        finally:
            conn.close()

    def update_stock(self, isbn, delta_or_new):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT titel_id FROM BuchTitel WHERE isbn = %s", (isbn,))
                res = cursor.fetchone()
                if not res: return
                t_id = res[0]
                cursor.execute("SELECT COUNT(*) FROM BuchExemplar WHERE titel_id = %s", (t_id,))
                current_count = cursor.fetchone()[0]
                target = int(delta_or_new)

                if target > current_count:
                    for i in range(current_count + 1, target + 1):
                        cursor.execute("SELECT IFNULL(MAX(exemplar_id), 0) + 1 FROM BuchExemplar")
                        e_id = cursor.fetchone()[0]
                        qr = f"QR-{isbn}-{i}"
                        cursor.execute(
                            "INSERT INTO BuchExemplar (exemplar_id, titel_id, exemplar_nr, qr_code) VALUES (%s, %s, %s, %s)",
                            (e_id, t_id, i, qr))
                elif target < current_count:
                    diff = current_count - target
                    cursor.execute("DELETE FROM BuchExemplar WHERE titel_id = %s ORDER BY exemplar_id DESC LIMIT %s",
                                   (t_id, diff))
        finally:
            conn.close()

    def delete_book(self, isbn):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM BuchTitel WHERE isbn = %s"
                cursor.execute(sql, (isbn,))
        finally:
            conn.close()

    # --- SCHÜLERVERWALTUNG ---

    def get_students(self, search_text=""):
        """Holt Schülerdaten aus der View v_studierende_ausleihen."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT DISTINCT studierende_id, nachname, vorname, schulklasse, schuljahr 
                    FROM v_studierende_ausleihen
                """
                params = []
                if search_text:
                    sql += " WHERE nachname LIKE %s OR vorname LIKE %s OR schulklasse LIKE %s"
                    like_val = f"%{search_text}%"
                    params = [like_val, like_val, like_val]

                sql += " ORDER BY nachname ASC"
                cursor.execute(sql, params)
                return cursor.fetchall()
        finally:
            conn.close()

    def get_classes(self):
        """Holt alle Schulklassen für den 'Klassen'-Tab."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT schuljahr, schulklasse, anzahl_schueler FROM v_schulklasse_uebersicht ORDER BY schuljahr DESC, schulklasse ASC"
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            conn.close()

    def get_school_years(self):
        """Holt alle Schuljahre aus der Tabelle Schuljahr."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT schuljahr_id, jahr FROM Schuljahr ORDER BY jahr DESC"
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            conn.close()

    def delete_student(self, student_id):
        """Löscht einen Studenten anhand seiner ID."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM Studierende WHERE studierende_id = %s"
                cursor.execute(sql, (student_id,))
        finally:
            conn.close()

    def get_student_by_id(self, student_id):
        """Holt Details eines Schülers inklusive Klassenname."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT s.studierende_id, s.nachname, s.vorname, sk.name 
                    FROM Studierende s
                    JOIN Schulklasse sk ON s.schulklasse_id = sk.schulklasse_id
                    WHERE s.studierende_id = %s
                """
                cursor.execute(sql, (student_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    def add_student(self, nachname, vorname, klasse, schuljahr):
        """Legt einen neuen Schüler an (mit Status 'AKTIV')."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Neue ID holen
                cursor.execute("SELECT IFNULL(MAX(studierende_id), 0) + 1 FROM Studierende")
                new_id = cursor.fetchone()[0]

                # 2. Einfügen (Status 'AKTIV' ist Pflicht laut SQL)
                sql = """
                    INSERT INTO Studierende (studierende_id, vorname, nachname, status, schulklasse_id) 
                    VALUES (%s, %s, %s, 'AKTIV', 
                        (SELECT schulklasse_id FROM Schulklasse WHERE name = %s LIMIT 1))
                """
                cursor.execute(sql, (new_id, vorname, nachname, klasse))
        finally:
            conn.close()

    def update_student(self, student_id, nachname, vorname, klasse, schuljahr):
        """Aktualisiert Schülerdaten."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE Studierende 
                    SET vorname = %s, nachname = %s, 
                        schulklasse_id = (SELECT schulklasse_id FROM Schulklasse WHERE name = %s LIMIT 1)
                    WHERE studierende_id = %s
                """
                cursor.execute(sql, (vorname, nachname, klasse, student_id))
        finally:
            conn.close()

    def add_class(self, name, jahr_text):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT schuljahr_id FROM Schuljahr WHERE jahr = %s", (jahr_text,))
                res = cursor.fetchone()
                if not res: return False # Schuljahr existiert nicht
                sj_id = res[0]

                cursor.execute("SELECT IFNULL(MAX(schulklasse_id), 0) + 1 FROM Schulklasse")
                new_kid = cursor.fetchone()[0]

                sql = "INSERT INTO Schulklasse (schulklasse_id, name, schuljahr_id) VALUES (%s, %s, %s)"
                cursor.execute(sql, (new_kid, name, sj_id))
                return True
        finally:
            conn.close()

    def delete_class(self, klasse_name, jahr_text):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    DELETE FROM Schulklasse 
                    WHERE name = %s AND schuljahr_id = (SELECT schuljahr_id FROM Schuljahr WHERE jahr = %s)
                """
                cursor.execute(sql, (klasse_name, jahr_text))
        finally:
            conn.close()

    def add_school_year(self, jahr_text):
        """Legt ein neues Schuljahr an."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Prüfen, ob das Jahr schon existiert, um Duplikate zu vermeiden
                cursor.execute("SELECT 1 FROM Schuljahr WHERE jahr = %s", (jahr_text,))
                if cursor.fetchone():
                    return False

                cursor.execute("SELECT IFNULL(MAX(schuljahr_id), 0) + 1 FROM Schuljahr")
                new_id = cursor.fetchone()[0]
                sql = "INSERT INTO Schuljahr (schuljahr_id, jahr) VALUES (%s, %s)"
                cursor.execute(sql, (new_id, jahr_text))
                return True
        except Exception as e:
            print(f"DB Error: {e}")
            return False
        finally:
            conn.close()




