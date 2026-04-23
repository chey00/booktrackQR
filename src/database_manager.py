# ------------------------------------------------------------------------------
# Projekt: BooktrackQR
# Modul: database_manager.py
# Autoren: René Bezold, Denis Sukkau, Georg Zinn
# Sprint 4: Mustafa Demiral (Intelligente Get-or-Create DB Logik & ID-Handling)
# Sprint 5: Mustafa Demiral (Soft-Delete & Admin-Löschung für Schüler)
# Sprint 8: Datenbank-Befehle für Ausleihe & PBI 10.3.1 (Klassen-Buchlisten) von Mustafa Demiral & Ahmet Toplar
# Sprint 9: Mustafa Demiral (PBI 11.6 - Automatische ID-Vergabe & Rechtemanagement Bugfix)
# Zweck: Zentrale Schnittstelle zur MariaDB auf dem Raspberry Pi.
# ------------------------------------------------------------------------------

import pymysql
import os
from dotenv import load_dotenv
from app_paths import resource_path, user_data_path


class DatabaseManager:
    def __init__(self):
        env_path = resource_path(".env")
        if not os.path.exists(env_path):
            env_path = user_data_path(".env")
        load_dotenv(env_path)

        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        port_env = os.getenv("DB_PORT", "3306")
        self.port = int(port_env) if port_env.isdigit() else 3306

        # Automatische Tabellen-Erstellung beim Start (PBI 10.3.1)
        self.setup_buchlisten_table()

    def _get_connection(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db_name,
            port=self.port,
            autocommit=True
        )

    # ==============================================================================
    # PBI 10.3.1: KLASSEN-BUCHLISTEN (n:m Beziehung) - Mustafa & Ahmet (Sprint 8)
    # ==============================================================================
    def setup_buchlisten_table(self):
        """Erstellt die Verknüpfungstabelle für die Buchlisten (MariaDB kompatibel)."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                               CREATE TABLE IF NOT EXISTS KlassenBuchliste
                               (
                                   klasse_name
                                   VARCHAR
                               (
                                   100
                               ),
                                   schuljahr VARCHAR
                               (
                                   50
                               ),
                                   isbn VARCHAR
                               (
                                   50
                               ),
                                   PRIMARY KEY
                               (
                                   klasse_name,
                                   schuljahr,
                                   isbn
                               )
                                   )
                               """)
        except Exception as e:
            print(f"Fehler beim Erstellen der Buchlisten-Tabelle: {e}")
        finally:
            conn.close()

    def save_class_booklist(self, klasse, jahr, isbn_list):
        """Speichert die komplette Buchliste für eine Klasse."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Alte Liste der Klasse komplett löschen (verhindert Duplikate)
                cursor.execute("""
                               DELETE
                               FROM KlassenBuchliste
                               WHERE klasse_name = %s
                                 AND schuljahr = %s
                               """, (klasse, jahr))

                # 2. Neue Liste einfügen
                for isbn in isbn_list:
                    cursor.execute("""
                                   INSERT INTO KlassenBuchliste (klasse_name, schuljahr, isbn)
                                   VALUES (%s, %s, %s)
                                   """, (klasse, jahr, isbn))
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Buchliste: {e}")
            return False
        finally:
            conn.close()

    def get_class_booklist(self, klasse, jahr):
        """Gibt eine Liste aller ISBNs zurück, die die Klasse benötigt."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                               SELECT isbn
                               FROM KlassenBuchliste
                               WHERE klasse_name = %s
                                 AND schuljahr = %s
                               """, (klasse, jahr))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Fehler beim Laden der Buchliste: {e}")
            return []
        finally:
            conn.close()

    # ==============================================================================

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

    def delete_book(self, isbn):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM BuchTitel WHERE isbn = %s", (isbn,))
        finally:
            conn.close()

    def update_stock(self, isbn, delta_or_new):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM BuchExemplar WHERE isbn = %s", (isbn,))
                current_count = cursor.fetchone()[0]
                target = int(delta_or_new)

                if target > current_count:
                    for i in range(current_count + 1, target + 1):
                        cursor.execute("SELECT IFNULL(MAX(exemplar_id), 0) + 1 FROM BuchExemplar")
                        e_id = cursor.fetchone()[0]
                        qr = f"QR-{isbn}-{i}"
                        cursor.execute(
                            "INSERT INTO BuchExemplar (exemplar_id, isbn, exemplar_nr, qr_code) VALUES (%s, %s, %s, %s)",
                            (e_id, isbn, i, qr))

                elif target < current_count:
                    diff = current_count - target
                    cursor.execute(
                        "DELETE FROM BuchExemplar WHERE isbn = %s ORDER BY exemplar_id DESC LIMIT %s",
                        (isbn, diff))

            conn.commit()

        except Exception as e:
            if conn: conn.rollback()
            raise e
        finally:
            conn.close()

    def update_book(self, isbn, titel, verlag, auflage, bestand):
        """Aktualisiert die Text-Infos in BuchTitel UND passt den Bestand an."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                      UPDATE BuchTitel
                      SET titel   = %s,
                          verlag  = %s,
                          auflage = %s
                      WHERE isbn = %s
                      """
                cursor.execute(sql, (titel, verlag, auflage, isbn))

                self.update_stock(isbn, bestand)

            conn.commit()
        except Exception as e:
            if conn: conn.rollback()
            raise e
        finally:
            conn.close()

    # --- SCHÜLERVERWALTUNG ---

    # MUSTAFA DEMIRAL (Sprint 5): Holt alle Schüler, berechnet formatierte ID per Modulo
    def get_students(self, search_text=""):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                      SELECT DISTINCT studierende_id, nachname, vorname, schulklasse, schuljahr, schueler_status
                      FROM v_studierende_ausleihen
                      ORDER BY studierende_id ASC
                      """
                cursor.execute(sql)
                all_students = cursor.fetchall()
        finally:
            conn.close()

        processed_students = []

        for row in all_students:
            db_id, nachname, vorname, klasse, jahr, status = row
            safe_jahr = str(jahr).replace('/', '-')

            display_id = db_id % 10000
            formatted_id = f"{klasse}_{safe_jahr}_{display_id:03d}"

            if status == 'AKTIV':
                processed_students.append((db_id, nachname, vorname, klasse, jahr, formatted_id))

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

    def deactivate_student(self, student_id):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Studierende SET status = 'INAKTIV' WHERE studierende_id = %s", (student_id,))
        finally:
            conn.close()

    def delete_student(self, student_id):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Studierende WHERE studierende_id = %s", (student_id,))
        finally:
            conn.close()

    def delete_all_inactive_students(self):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Studierende WHERE status = 'INAKTIV'")
                return cursor.rowcount
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
                      WHERE s.studierende_id = %s
                      """
                cursor.execute(sql, (student_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    def add_student(self, nachname, vorname, klasse, schuljahr, manual_id=None):
        klasse_id = self.get_or_create_class(klasse, schuljahr)
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                if manual_id:
                    new_id = (klasse_id * 10000) + int(manual_id)
                    cursor.execute("SELECT studierende_id FROM Studierende WHERE studierende_id = %s", (new_id,))
                    if cursor.fetchone():
                        return False
                else:
                    cursor.execute("SELECT MAX(studierende_id) FROM Studierende WHERE schulklasse_id = %s",
                                   (klasse_id,))
                    max_id = cursor.fetchone()[0]
                    if max_id and max_id >= (klasse_id * 10000):
                        new_id = max_id + 1
                    else:
                        new_id = (klasse_id * 10000) + 1

                sql = """
                      INSERT INTO Studierende (studierende_id, vorname, nachname, status, schulklasse_id)
                      VALUES (%s, %s, %s, 'AKTIV', %s)
                      """
                cursor.execute(sql, (new_id, vorname, nachname, klasse_id))
                return True
        finally:
            conn.close()

    # MUSTAFA DEMIRAL (Sprint 9): PBI 11.6 - Komplett überarbeitetes rechtesicheres ID-Update (Kein FOREIGN_KEY_CHECKS nötig!)
    def update_student(self, student_id, nachname, vorname, klasse, schuljahr, manual_id=None):
        klasse_id = self.get_or_create_class(klasse, schuljahr)
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Alte Klasse und Status abfragen
                cursor.execute("SELECT schulklasse_id, status FROM Studierende WHERE studierende_id = %s",
                               (student_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                old_klasse_id = row[0]
                current_status = row[1]

                current_manual = int(student_id) % 10000

                # 2. Intelligente ID Logik für die Klasse
                if old_klasse_id != klasse_id:
                    # Der Schüler wechselt die Klasse
                    if manual_id and int(manual_id) != current_manual:
                        # Fall A: Der Nutzer hat absichtlich eine ganz neue ID (z.B. 420) ins Textfeld eingetippt
                        new_id = (klasse_id * 10000) + int(manual_id)
                    else:
                        # Fall B: Das Feld wurde nicht angefasst, wir vergeben automatisch die nächste freie Nummer
                        cursor.execute("SELECT MAX(studierende_id) FROM Studierende WHERE schulklasse_id = %s",
                                       (klasse_id,))
                        max_id = cursor.fetchone()[0]
                        if max_id and max_id >= (klasse_id * 10000):
                            new_id = max_id + 1
                        else:
                            new_id = (klasse_id * 10000) + 1
                else:
                    # Der Schüler bleibt in der gleichen Klasse (nur Name ändert sich z.B.)
                    new_manual = int(manual_id) if manual_id else current_manual
                    new_id = (klasse_id * 10000) + new_manual

                # 3. Das Umhängen in der sicheren Reihenfolge
                if new_id != student_id:
                    # Prüfen ob ID schon vergeben ist
                    cursor.execute("SELECT studierende_id FROM Studierende WHERE studierende_id = %s", (new_id,))
                    if cursor.fetchone():
                        return False

                    # Schritt 1: Klon anlegen (völlig ungefährlich)
                    sql_insert = """
                                 INSERT INTO Studierende (studierende_id, vorname, nachname, status, schulklasse_id)
                                 VALUES (%s, %s, %s, %s, %s) \
                                 """
                    cursor.execute(sql_insert, (new_id, vorname, nachname, current_status, klasse_id))

                    # Schritt 2 & 3: Kinder (Bücher) auf den neuen Klon umhängen
                    cursor.execute("UPDATE Ausleihe_Aktuell SET studierende_id = %s WHERE studierende_id = %s",
                                   (new_id, student_id))

                    try:
                        cursor.execute("UPDATE Ausleihe_Historie SET studierende_id = %s WHERE studierende_id = %s",
                                       (new_id, student_id))
                    except:
                        pass  # Falls es Historie auf dieser DB-Version nicht gibt, mach normal weiter

                    # Schritt 4: Das leere Original löschen (Da alle Kinder weg sind, greift kein Foreign Key Alarm mehr!)
                    cursor.execute("DELETE FROM Studierende WHERE studierende_id = %s", (student_id,))

                else:
                    # Normale Namensänderung
                    sql = """
                          UPDATE Studierende
                          SET vorname        = %s,
                              nachname       = %s,
                              schulklasse_id = %s
                          WHERE studierende_id = %s
                          """
                    cursor.execute(sql, (vorname, nachname, klasse_id, student_id))
                return True
        except Exception as e:
            print(f"Fehler beim Update des Schülers: {e}")
            return False
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
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                cursor.execute("""
                               SELECT schulklasse_id
                               FROM Schulklasse
                               WHERE name = %s
                                 AND schuljahr_id = (SELECT schuljahr_id FROM Schuljahr WHERE jahr = %s LIMIT 1)
                               """, (klasse_name, jahr_text))
                res = cursor.fetchone()
                if res:
                    kid = res[0]
                    cursor.execute(
                        "DELETE FROM Ausleihe_Aktuell WHERE studierende_id IN (SELECT studierende_id FROM Studierende WHERE schulklasse_id = %s)",
                        (kid,))
                    cursor.execute("DELETE FROM Studierende WHERE schulklasse_id = %s", (kid,))
                    cursor.execute("DELETE FROM Schulklasse WHERE schulklasse_id = %s", (kid,))
        finally:
            with conn.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.close()

    def add_school_year(self, jahr_text):
        try:
            self.get_or_create_school_year(jahr_text)
            return True
        except:
            return False

    def get_student_by_qr_id(self, qr_id):
        all_students = self.get_students()
        for s in all_students:
            if s[5] == qr_id:
                return {
                    "db_id": s[0],
                    "nachname": s[1],
                    "vorname": s[2],
                    "klasse": s[3],
                    "jahr": s[4],
                    "full_id": s[5]
                }
        return None

    def get_book_by_qr_data(self, isbn):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT isbn, titel, verlag, auflage FROM BuchTitel WHERE isbn = %s"
                cursor.execute(sql, (isbn,))
                res = cursor.fetchone()
                if res:
                    return {"isbn": res[0], "titel": res[1], "verlag": res[2], "auflage": res[3]}
                return None
        finally:
            conn.close()

    def get_current_loaner(self, isbn):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                      SELECT s.vorname, s.nachname
                      FROM Ausleihe_Aktuell a
                               JOIN Studierende s ON a.studierende_id = s.studierende_id
                               JOIN BuchExemplar e ON a.exemplar_id = e.exemplar_id
                               JOIN BuchTitel t ON e.isbn = t.isbn
                      WHERE t.isbn = %s
                        AND s.status = 'AKTIV' LIMIT 1
                      """
                cursor.execute(sql, (isbn,))
                res = cursor.fetchone()
                if res:
                    return f"{res[0]} {res[1]}"
                return None
        finally:
            conn.close()

    def delete_school_year(self, jid):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

                cursor.execute("SELECT schulklasse_id FROM Schulklasse WHERE schuljahr_id = %s", (jid,))
                klassen_rows = cursor.fetchall()

                for k in klassen_rows:
                    kid = k[0]
                    cursor.execute(
                        "DELETE FROM Ausleihe_Aktuell WHERE studierende_id IN (SELECT studierende_id FROM Studierende WHERE schulklasse_id = %s)",
                        (kid,))
                    cursor.execute("DELETE FROM Studierende WHERE schulklasse_id = %s", (kid,))

                cursor.execute("DELETE FROM Schulklasse WHERE schuljahr_id = %s", (jid,))
                cursor.execute("DELETE FROM Schuljahr WHERE schuljahr_id = %s", (jid,))
        finally:
            with conn.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.close()

    def get_active_loans_for_student(self, qr_id):
        student_info = self.get_student_by_qr_id(qr_id)
        if not student_info:
            return []

        real_db_id = student_info["db_id"]
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT isbn, titel FROM v_studierende_ausleihen WHERE studierende_id = %s"
                cursor.execute(sql, (real_db_id,))
                return cursor.fetchall()
        finally:
            conn.close()

    def add_loan(self, qr_id, isbn):
        student_info = self.get_student_by_qr_id(qr_id)
        if not student_info:
            raise Exception("Schüler-ID konnte in der Datenbank nicht aufgelöst werden.")

        real_db_id = student_info["db_id"]
        conn = self._get_connection()

        try:
            with conn.cursor() as cursor:
                sql_find_free = """
                                SELECT exemplar_id
                                FROM BuchExemplar
                                WHERE isbn = %s
                                  AND exemplar_id NOT IN (SELECT exemplar_id FROM Ausleihe_Aktuell) LIMIT 1
                                """
                cursor.execute(sql_find_free, (isbn,))
                result = cursor.fetchone()

                if not result:
                    raise Exception(f"Kein freies Exemplar für ISBN {isbn} mehr verfügbar!")

                free_exemplar_id = result[0]

                sql_insert = """
                             INSERT INTO Ausleihe_Aktuell (studierende_id, exemplar_id)
                             VALUES (%s, %s)
                             """
                cursor.execute(sql_insert, (real_db_id, free_exemplar_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def return_book_by_isbn(self, qr_id, isbn):
        student_info = self.get_student_by_qr_id(qr_id)
        if not student_info:
            return False

        real_db_id = student_info["db_id"]
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                      DELETE
                      FROM Ausleihe_Aktuell
                      WHERE studierende_id = %s
                        AND exemplar_id IN (SELECT exemplar_id FROM BuchExemplar WHERE isbn = %s)
                      """
                cursor.execute(sql, (real_db_id, isbn))
                return cursor.rowcount > 0
        finally:
            conn.close()