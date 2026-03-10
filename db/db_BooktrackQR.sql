-- =========================================================
-- BookTrackQR - Datenbankskript
-- Bereinigte Abgabe-Version
-- Änderungen von Batuhan Aktürk:
-- - Zustand eines Buches auf Exemplar-Ebene eingeführt
-- - Standardwert für neue Bücher definiert
-- - Foreign Key Beziehung auf ISBN umgestellt
-- - QR-Code als eindeutiger Identifikator definiert
-- =========================================================

PRAGMA foreign_keys = OFF;

DROP VIEW  IF EXISTS v_exemplar_status;
DROP VIEW  IF EXISTS v_studierende_ausleihen;
DROP VIEW  IF EXISTS v_bestand_titel;
DROP VIEW  IF EXISTS v_schulklasse_uebersicht;

DROP TABLE IF EXISTS Ausleihe_Aktuell;
DROP TABLE IF EXISTS BuchExemplar;
DROP TABLE IF EXISTS BuchTitel;
DROP TABLE IF EXISTS Studierende;
DROP TABLE IF EXISTS Schulklasse;
DROP TABLE IF EXISTS Schuljahr;

PRAGMA foreign_keys = ON;

-- =========================================================
-- TABELLEN
-- =========================================================

CREATE TABLE Schuljahr (
  schuljahr_id INTEGER PRIMARY KEY,
  jahr TEXT NOT NULL
);

CREATE TABLE Schulklasse (
  schulklasse_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  schuljahr_id INTEGER NOT NULL,
  FOREIGN KEY (schuljahr_id)
    REFERENCES Schuljahr(schuljahr_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE TABLE Studierende (
  studierende_id INTEGER PRIMARY KEY,
  vorname TEXT NOT NULL,
  nachname TEXT NOT NULL,
  status TEXT NOT NULL,
  schulklasse_id INTEGER NOT NULL,
  FOREIGN KEY (schulklasse_id)
    REFERENCES Schulklasse(schulklasse_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

-- =========================================================
-- Änderung Batuhan:
-- ISBN wurde als UNIQUE definiert, damit sie als
-- Referenzschlüssel für BuchExemplar verwendet werden kann
-- =========================================================

CREATE TABLE BuchTitel (
  titel_id INTEGER PRIMARY KEY,
  titel TEXT NOT NULL,
  verlag TEXT NOT NULL,
  auflage INTEGER NOT NULL CHECK (auflage > 0),
  isbn TEXT NOT NULL UNIQUE
);

-- =========================================================
-- Änderungen Batuhan:
-- 1. Zustand eines Buches ergänzt
-- 2. Standardwert für neue Bücher = "i.O."
-- 3. Zustand wird über CHECK eingeschränkt
-- 4. Verbindung zu BuchTitel über ISBN statt titel_id
-- 5. QR-Code eindeutig definiert
-- =========================================================

CREATE TABLE BuchExemplar (
  exemplar_id INTEGER PRIMARY KEY,
  isbn TEXT NOT NULL,
  exemplar_nr INTEGER NOT NULL CHECK (exemplar_nr > 0),

  -- QR-Code identifiziert jedes physische Buch eindeutig
  qr_code TEXT NOT NULL UNIQUE,

  -- Zustand eines Buches (neu hinzugefügt)
  zustand TEXT NOT NULL DEFAULT 'i.O.'
    CHECK (zustand IN ('i.O.', 'beschädigt', 'stark beschädigt', 'verloren')),

  FOREIGN KEY (isbn)
    REFERENCES BuchTitel(isbn)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

-- Aktuelle Ausleihe eines Buches
CREATE TABLE Ausleihe_Aktuell (
  exemplar_id INTEGER PRIMARY KEY,
  studierende_id INTEGER NOT NULL,

  FOREIGN KEY (exemplar_id)
    REFERENCES BuchExemplar(exemplar_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  FOREIGN KEY (studierende_id)
    REFERENCES Studierende(studierende_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

-- =========================================================
-- TESTDATEN
-- =========================================================

INSERT INTO Schuljahr (schuljahr_id, jahr) VALUES
(1,'25/26'),
(2,'26/27');

INSERT INTO Schulklasse (schulklasse_id, name, schuljahr_id) VALUES
(1,'FSWI-1',1),
--
(2,'FSWI-2',2);

INSERT INTO Studierende (studierende_id, vorname, nachname, status, schulklasse_id) VALUES
(1,'Max','Müller','AKTIV',2),
(2,'Lisa','Schmidt','AKTIV',2),
(3,'Ali','Yilmaz','AKTIV',2),
(4,'Jonas','Becker','AKTIV',2),
(5,'Mia','Wagner','AKTIV',2),
(6,'Noah','Weber','AKTIV',2),
(7,'Sara','Kaya','INAKTIV',2),
(8,'Can','Öztürk','AKTIV',2),
(9,'Laura','Maier','AKTIV',2),
(10,'Tim','Schulz','AKTIV',2),
(11,'Ayse','Kara','AKTIV',2),
(12,'David','Lang','AKTIV',2),
(13,'Sophie','Brandt','AKTIV',1),
(14,'Kevin','Wolf','AKTIV',1),
(15,'Nina','Roth','INAKTIV',1);

INSERT INTO BuchTitel (titel_id, titel, verlag, auflage, isbn) VALUES
(1,'Datenbanken Grundlagen','Springer',3,'9781234567890'),
(2,'Java für Einsteiger','Rheinwerk',2,'9789876543210'),
(3,'SQL kompakt','Pearson',1,'9781111111111'),
(4,'Netzwerke Basics','Hanser',2,'9782222222222'),
(5,'Projektmanagement','Hanser',1,'9784444444444');

-- =========================================================
-- Testdaten für Buchexemplare
-- Zustand wird teilweise bewusst gesetzt, um unterschiedliche
-- Szenarien (beschädigt / verloren) zu simulieren
-- =========================================================

INSERT INTO BuchExemplar (exemplar_id, isbn, exemplar_nr, qr_code, zustand) VALUES
(1,'9781234567890',1,'DB-001','i.O.'),
(2,'9781234567890',2,'DB-002','i.O.'),
(3,'9781234567890',3,'DB-003','i.O.'),
(4,'9781234567890',4,'DB-004','beschädigt'),
(5,'9781234567890',5,'DB-005','i.O.'),
(6,'9781234567890',6,'DB-006','i.O.');

-- =========================================================
-- VIEWS
-- =========================================================

-- =========================================================
-- Änderung Batuhan:
-- JOIN erfolgt über ISBN statt über titel_id
-- =========================================================

CREATE VIEW v_exemplar_status AS
SELECT
  e.exemplar_id,
  e.qr_code,
  e.exemplar_nr,
  e.zustand,
  t.titel,
  t.verlag,
  t.auflage,
  t.isbn,

  CASE
    WHEN a.exemplar_id IS NULL THEN 'VERFUEGBAR'
    ELSE 'AUSGELIEHEN'
  END AS ausleih_status

FROM BuchExemplar e
JOIN BuchTitel t ON t.isbn = e.isbn
LEFT JOIN Ausleihe_Aktuell a ON a.exemplar_id = e.exemplar_id;

-- View: zeigt welche Bücher von welchen Schülern ausgeliehen sind
CREATE VIEW v_studierende_ausleihen AS
SELECT
  s.studierende_id,
  s.vorname,
  s.nachname,
  s.status AS schueler_status,
  sk.name AS schulklasse,
  sj.jahr AS schuljahr,
  e.qr_code,
  e.zustand,
  t.titel,
  t.isbn
FROM Studierende s
JOIN Schulklasse sk ON sk.schulklasse_id = s.schulklasse_id
JOIN Schuljahr sj ON sj.schuljahr_id = sk.schuljahr_id
LEFT JOIN Ausleihe_Aktuell a ON a.studierende_id = s.studierende_id
LEFT JOIN BuchExemplar e ON e.exemplar_id = a.exemplar_id
LEFT JOIN BuchTitel t ON t.isbn = e.isbn;

-- =========================================================
-- BEWEIS-ABFRAGEN
-- =========================================================

-- Struktur der Tabelle anzeigen (Beweis für Zustand-Spalte)
PRAGMA table_info(BuchExemplar);

-- Test: neues Buch ohne Zustand einfügen
-- Erwartung: Zustand wird automatisch "i.O."
INSERT INTO BuchExemplar (exemplar_id, isbn, exemplar_nr, qr_code)
VALUES (31, '9784444444444', 3, 'PM-003');

SELECT
  exemplar_id,
  isbn,
  qr_code,
  zustand
FROM BuchExemplar
WHERE exemplar_id = 31;

-- =========================================================