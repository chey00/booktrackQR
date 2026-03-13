# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: database_manager.py
# Autoren: René Bezold, Denis Sukkau, Georg Zinn
# Sprint 4: Mustafa Demiral (Intelligente Get-or-Create DB Logik & ID-Handling)
# Zweck: Zentrale Schnittstelle zur MariaDB auf dem Raspberry Pi.
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

    # --- MUSTAFA DEMIRAL: Sichere Automatik-Funktionen für den Import ---
    def get_or_create_school_year(self, jahr_text):
        """Sucht das Schuljahr oder legt es automatisch an."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT schuljahr_id FROM Schuljahr WHERE jahr = %s", (jahr_text,))
                res = cursor.fetchone()
                if res: return res[0]

                cursor.execute("SELECT IFNULL(MAX(schuljahr_id), 0) + 1 FROM Schuljahr")
                new_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO Schuljahr (schuljahr_id, jahr) VALUES (%s, %s)", (new_id, jahr_text))
                return new_id
        finally:
            conn.close()

    def get_or_create_class(self, name, jahr_text):
        """Sucht die Klasse oder legt sie sicher an, damit NIE ein NULL-Fehler entsteht."""
        sj_id = self.get_or_create_school_year(jahr_text)
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT schulklasse_id FROM Schulklasse WHERE name = %s AND schuljahr_id = %s LIMIT 1",
                               (name, sj_id))
                res = cursor.fetchone()
                if res: return res[0]

                cursor.execute("SELECT IFNULL(MAX(schulklasse_id), 0) + 1 FROM Schulklasse")
                new_kid = cursor.fetchone()[0]
                cursor.execute("INSERT INTO Schulklasse (schulklasse_id, name, schuljahr_id) VALUES (%s, %s, %s)",
                               (new_kid, name, sj_id))
                return new_kid
        finally:
            conn.close()

    # ---------------------------------------------------------------------

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

                    sql_ex = "INSERT INTO BuchExemplar (exemplar_id, isbn, exemplar_nr, qr_code) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql_ex, (e_id, isbn, i, qr))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
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
                cursor.execute("DELETE FROM BuchTitel WHERE isbn = %s", (isbn,))
        finally:
            conn.close()

    # --- SCHÜLERVERWALTUNG ---

    # MUSTAFA DEMIRAL: Berechnet die formatierte ID (z.B. MB_2024-25_001) dynamisch pro Klasse!
    def get_students(self, search_text=""):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Holt IMMER alle Schüler sortiert nach ihrer Eintragungs-Reihenfolge
                sql = """
                      SELECT DISTINCT studierende_id, nachname, vorname, schulklasse, schuljahr
                      FROM v_studierende_ausleihen
                      ORDER BY studierende_id ASC \
                      """
                cursor.execute(sql)
                all_students = cursor.fetchall()
        finally:
            conn.close()

        class_counters = {}
        processed_students = []

        # 1. Fortlaufende Nummer PRO KLASSE berechnen!
        for row in all_students:
            db_id, nachname, vorname, klasse, jahr = row
            key = f"{klasse}_{jahr}"

            class_counters[key] = class_counters.get(key, 0) + 1
            lfd_nr = class_counters[key]

            safe_jahr = str(jahr).replace('/', '-')
            formatted_id = f"{klasse}_{safe_jahr}_{lfd_nr:03d}"

            # Hängt die neu berechnete, perfekt formatierte ID als 6. Spalte an
            processed_students.append((db_id, nachname, vorname, klasse, jahr, formatted_id))

        # 2. Jetzt erst den Suchfilter anwenden (inklusive der neuen schönen ID)
        if search_text:
            filtered = []
            st = search_text.lower()
            for s in processed_students:
                if (st in s[5].lower() or st in s[1].lower() or
                        st in s[2].lower() or st in s[3].lower() or st in str(s[4]).lower()):
                    filtered.append(s)
            return filtered

        return processed_students

    def get_classes(self):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT schuljahr, schulklasse, anzahl_schueler FROM v_schulklasse_uebersicht ORDER BY schuljahr DESC, schulklasse ASC")
                return cursor.fetchall()
        finally:
            conn.close()

    def get_school_years(self):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT schuljahr_id, jahr FROM Schuljahr ORDER BY jahr DESC")
                return cursor.fetchall()
        finally:
            conn.close()

    def delete_student(self, student_id):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Studierende WHERE studierende_id = %s", (student_id,))
        finally:
            conn.close()

    def get_student_by_id(self, student_id):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                      SELECT s.studierende_id, s.nachname, s.vorname, sk.name, sj.jahr
                      FROM Studierende s
                               JOIN Schulklasse sk ON s.schulklasse_id = sk.schulklasse_id
                               JOIN Schuljahr sj ON sk.schuljahr_id = sj.schuljahr_id
                      WHERE s.studierende_id = %s \
                      """
                cursor.execute(sql, (student_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    def add_student(self, nachname, vorname, klasse, schuljahr):
        klasse_id = self.get_or_create_class(klasse, schuljahr)
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT IFNULL(MAX(studierende_id), 0) + 1 FROM Studierende")
                new_id = cursor.fetchone()[0]

                sql = """
                      INSERT INTO Studierende (studierende_id, vorname, nachname, status, schulklasse_id)
                      VALUES (%s, %s, %s, 'AKTIV', %s) \
                      """
                cursor.execute(sql, (new_id, vorname, nachname, klasse_id))
        finally:
            conn.close()

    def update_student(self, student_id, nachname, vorname, klasse, schuljahr):
        klasse_id = self.get_or_create_class(klasse, schuljahr)
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                      UPDATE Studierende
                      SET vorname        = %s, \
                          nachname       = %s, \
                          schulklasse_id = %s
                      WHERE studierende_id = %s \
                      """
                cursor.execute(sql, (vorname, nachname, klasse_id, student_id))
        finally:
            conn.close()

    def add_class(self, name, jahr_text):
        try:
            self.get_or_create_class(name, jahr_text)
            return True
        except:
            return False

    def delete_class(self, klasse_name, jahr_text):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM Schulklasse WHERE name = %s AND schuljahr_id = (SELECT schuljahr_id FROM Schuljahr WHERE jahr = %s LIMIT 1)"
                cursor.execute(sql, (klasse_name, jahr_text))
        finally:
            conn.close()

    def add_school_year(self, jahr_text):
        try:
            self.get_or_create_school_year(jahr_text)
            return True
        except:
            return False