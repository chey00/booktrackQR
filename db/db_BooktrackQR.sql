-- =========================================================

-- -------------------------
-- 0) RESET
-- -------------------------
SET FOREIGN_KEY_CHECKS = 0;

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

SET FOREIGN_KEY_CHECKS = 1;

-- =========================================================
-- PROGRAMMIERT VON BATUHAN
-- Teil: Datenbank-Schema / Tabellen / Primary Keys / Foreign Keys / Constraints
-- =========================================================

CREATE TABLE Schuljahr (
  schuljahr_id INT PRIMARY KEY,
  jahr VARCHAR(10) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE Schulklasse (
  schulklasse_id INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  schuljahr_id INT NOT NULL,
  CONSTRAINT fk_schulklasse_schuljahr
    FOREIGN KEY (schuljahr_id)
    REFERENCES Schuljahr(schuljahr_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE Studierende (
  studierende_id INT PRIMARY KEY,
  vorname VARCHAR(50) NOT NULL,
  nachname VARCHAR(50) NOT NULL,
  status VARCHAR(10) NOT NULL, -- AKTIV / INAKTIV
  schulklasse_id INT NOT NULL,
  CONSTRAINT fk_studierende_schulklasse
    FOREIGN KEY (schulklasse_id)
    REFERENCES Schulklasse(schulklasse_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- Stammdaten pro Titel/Edition
CREATE TABLE BuchTitel (
  titel_id INT PRIMARY KEY,
  titel  VARCHAR(200) NOT NULL,
  verlag VARCHAR(100) NOT NULL,
  auflage INT NOT NULL,
  isbn   VARCHAR(20) NOT NULL,
  CONSTRAINT chk_auflage_pos CHECK (auflage > 0)
) ENGINE=InnoDB;

-- Physische Exemplare (QR-Code identifiziert genau 1 Exemplar)
-- exemplar_nr = "Buch 1", "Buch 2", ... pro Titel
CREATE TABLE BuchExemplar (
  exemplar_id INT PRIMARY KEY,
  titel_id INT NOT NULL,
  exemplar_nr INT NOT NULL,
  qr_code VARCHAR(50) NOT NULL,
  CONSTRAINT chk_exemplar_nr_pos CHECK (exemplar_nr > 0),
  CONSTRAINT fk_exemplar_titel
    FOREIGN KEY (titel_id)
    REFERENCES BuchTitel(titel_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- Keine Historie: nur aktueller Zustand
-- PK(exemplar_id) verhindert doppelte gleichzeitige Ausleihe eines Exemplars
CREATE TABLE Ausleihe_Aktuell (
  exemplar_id INT PRIMARY KEY,
  studierende_id INT NOT NULL,
  CONSTRAINT fk_ausleihe_exemplar
    FOREIGN KEY (exemplar_id)
    REFERENCES BuchExemplar(exemplar_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_ausleihe_studierende
    FOREIGN KEY (studierende_id)
    REFERENCES Studierende(studierende_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================
-- PROGRAMMIERT VON AHMET
-- Teil: Testdaten / Seeds / realistische Datensätze
-- =========================================================

INSERT INTO Schuljahr (schuljahr_id, jahr) VALUES
(1,'25/26'),
(2,'26/27');

INSERT INTO Schulklasse (schulklasse_id, name, schuljahr_id) VALUES
(1,'FSWI-1',1),
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

INSERT INTO BuchExemplar (exemplar_id, titel_id, exemplar_nr, qr_code) VALUES
(1,1,1,'DB-001'),
(2,1,2,'DB-002'),
(3,1,3,'DB-003'),
(4,1,4,'DB-004'),
(5,1,5,'DB-005'),
(6,1,6,'DB-006'),
(14,1,7,'DB-007'),
(15,1,8,'DB-008'),
(16,1,9,'DB-009'),
(17,1,10,'DB-010'),
(18,1,11,'DB-011'),
(19,1,12,'DB-012'),

(7,2,1,'JAVA-001'),
(8,2,2,'JAVA-002'),
(9,2,3,'JAVA-003'),
(10,2,4,'JAVA-004'),
(20,2,5,'JAVA-005'),
(21,2,6,'JAVA-006'),
(22,2,7,'JAVA-007'),
(23,2,8,'JAVA-008'),

(11,3,1,'SQL-001'),
(12,3,2,'SQL-002'),
(13,3,3,'SQL-003'),
(24,3,4,'SQL-004'),
(25,3,5,'SQL-005'),

(26,4,1,'NET-001'),
(27,4,2,'NET-002'),
(28,4,3,'NET-003'),

(29,5,1,'PM-001'),
(30,5,2,'PM-002');

INSERT INTO Ausleihe_Aktuell (exemplar_id, studierende_id) VALUES
(1,1),
(2,2),
(3,3),
(4,4),
(5,5),
(6,6),
(14,8),
(15,9),
(16,10),
(17,11),
(18,12),
(7,1),
(8,2),
(11,10),
(29,3);

-- =========================================================
-- PROGRAMMIERT VON JACLYN
-- Teil: Views + Beweis-Abfragen (JOIN, Aggregat, HAVING)
-- =========================================================

CREATE VIEW v_exemplar_status AS
SELECT
  e.exemplar_id,
  e.qr_code,
  e.exemplar_nr,
  t.titel,
  t.verlag,
  t.auflage,
  t.isbn,
  CASE
    WHEN a.exemplar_id IS NULL THEN 'VERFUEGBAR'
    ELSE 'AUSGELIEHEN'
  END AS ausleih_status
FROM BuchExemplar e
JOIN BuchTitel t ON t.titel_id = e.titel_id
LEFT JOIN Ausleihe_Aktuell a ON a.exemplar_id = e.exemplar_id;

CREATE VIEW v_studierende_ausleihen AS
SELECT
  s.studierende_id,
  s.vorname,
  s.nachname,
  s.status AS schueler_status,
  sk.name AS schulklasse,
  sj.jahr AS schuljahr,
  e.qr_code,
  t.titel,
  t.isbn
FROM Studierende s
JOIN Schulklasse sk ON sk.schulklasse_id = s.schulklasse_id
JOIN Schuljahr sj ON sj.schuljahr_id = sk.schuljahr_id
LEFT JOIN Ausleihe_Aktuell a ON a.studierende_id = s.studierende_id
LEFT JOIN BuchExemplar e ON e.exemplar_id = a.exemplar_id
LEFT JOIN BuchTitel t ON t.titel_id = e.titel_id;

CREATE VIEW v_bestand_titel AS
SELECT
  t.titel_id,
  t.titel,
  t.isbn,
  COUNT(e.exemplar_id) AS anzahl_exemplare,
  SUM(CASE WHEN a.exemplar_id IS NULL THEN 0 ELSE 1 END) AS aktuell_ausgeliehen
FROM BuchTitel t
LEFT JOIN BuchExemplar e ON e.titel_id = t.titel_id
LEFT JOIN Ausleihe_Aktuell a ON a.exemplar_id = e.exemplar_id
GROUP BY t.titel_id, t.titel, t.isbn;

CREATE VIEW v_schulklasse_uebersicht AS
SELECT
  sj.jahr AS schuljahr,
  sk.name AS schulklasse,
  COUNT(s.studierende_id) AS anzahl_schueler
FROM Schulklasse sk
JOIN Schuljahr sj ON sj.schuljahr_id = sk.schuljahr_id
LEFT JOIN Studierende s ON s.schulklasse_id = sk.schulklasse_id
GROUP BY sj.jahr, sk.name;

-- -------------------------
-- BEWEIS-ABFRAGEN
-- -------------------------

-- 1) Tabellen vorhanden? (MySQL)
SELECT table_name
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- 2) Schuljahr -> Schulklassen
SELECT sj.jahr AS schuljahr, sk.name AS schulklasse
FROM Schuljahr sj
JOIN Schulklasse sk ON sk.schuljahr_id = sj.schuljahr_id
ORDER BY sj.jahr, sk.name;

-- 3) Alle Schüler der Schulklasse FSWI-2
SELECT s.studierende_id, s.vorname, s.nachname, s.status
FROM Studierende s
JOIN Schulklasse sk ON sk.schulklasse_id = s.schulklasse_id
WHERE sk.name = 'FSWI-2'
ORDER BY s.nachname;

-- 4) FSWI-2: hat der Schüler "Datenbanken Grundlagen"? Wenn ja: welches QR?
SELECT
  s.vorname,
  s.nachname,
  CASE WHEN e.exemplar_id IS NULL THEN 'NEIN' ELSE 'JA' END AS hat_datenbanken_grundlagen,
  e.qr_code
FROM Studierende s
JOIN Schulklasse sk ON sk.schulklasse_id = s.schulklasse_id
LEFT JOIN Ausleihe_Aktuell a ON a.studierende_id = s.studierende_id
LEFT JOIN BuchExemplar e ON e.exemplar_id = a.exemplar_id
LEFT JOIN BuchTitel t ON t.titel_id = e.titel_id
  AND t.titel = 'Datenbanken Grundlagen'
WHERE sk.name = 'FSWI-2'
ORDER BY s.nachname;

-- 5) Bestandsübersicht je Titel
SELECT * FROM v_bestand_titel ORDER BY titel;

-- 6) Exemplarstatus
SELECT * FROM v_exemplar_status ORDER BY titel, exemplar_nr;

-- 7) Welche Bücher hat welcher Schüler?
SELECT * FROM v_studierende_ausleihen
ORDER BY schulklasse, nachname, vorname, titel, qr_code;

-- 8) Verfügbare Exemplare (nicht ausgeliehen)
SELECT e.qr_code, t.titel
FROM BuchExemplar e
JOIN BuchTitel t ON t.titel_id = e.titel_id
LEFT JOIN Ausleihe_Aktuell a ON a.exemplar_id = e.exemplar_id
WHERE a.exemplar_id IS NULL
ORDER BY t.titel, e.exemplar_nr;

-- 9) Schüler + Anzahl ausgeliehener Exemplare
SELECT s.vorname, s.nachname, COUNT(a.exemplar_id) AS anzahl_buecher
FROM Studierende s
LEFT JOIN Ausleihe_Aktuell a ON a.studierende_id = s.studierende_id
GROUP BY s.studierende_id, s.vorname, s.nachname
ORDER BY anzahl_buecher DESC, s.nachname;

-- 10) HAVING: Schüler mit mindestens 2 Büchern
SELECT s.vorname, s.nachname, COUNT(a.exemplar_id) AS anzahl_buecher
FROM Studierende s
JOIN Ausleihe_Aktuell a ON a.studierende_id = s.studierende_id
GROUP BY s.studierende_id, s.vorname, s.nachname
HAVING COUNT(a.exemplar_id) >= 2
ORDER BY anzahl_buecher DESC;

-- 11) HAVING: Titel mit mindestens 5 Exemplaren
SELECT t.titel, COUNT(e.exemplar_id) AS anzahl_exemplare
FROM BuchTitel t
JOIN BuchExemplar e ON e.titel_id = t.titel_id
GROUP BY t.titel
HAVING COUNT(e.exemplar_id) >= 5
ORDER BY anzahl_exemplare DESC;

-- =========================================================

