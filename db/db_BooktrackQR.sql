SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS v_exemplar_status;
DROP VIEW IF EXISTS v_studierende_ausleihen;
DROP VIEW IF EXISTS v_bestand_titel;
DROP VIEW IF EXISTS v_schulklasse_uebersicht;

DROP TABLE IF EXISTS Ausleihe_Aktuell;
DROP TABLE IF EXISTS BuchExemplar;
DROP TABLE IF EXISTS BuchTitel;
DROP TABLE IF EXISTS Studierende;
DROP TABLE IF EXISTS Schulklasse;
DROP TABLE IF EXISTS Schuljahr;

SET FOREIGN_KEY_CHECKS = 1;


CREATE TABLE Schuljahr (
  schuljahr_id INT PRIMARY KEY,
  jahr VARCHAR(50) NOT NULL
);

CREATE TABLE Schulklasse (
  schulklasse_id INT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  schuljahr_id INT NOT NULL,
  CONSTRAINT fk_sk_sj FOREIGN KEY (schuljahr_id) REFERENCES Schuljahr(schuljahr_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE Studierende (
  studierende_id INT PRIMARY KEY,
  vorname VARCHAR(100) NOT NULL,
  nachname VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL,
  schulklasse_id INT NOT NULL,
  CONSTRAINT fk_s_sk FOREIGN KEY (schulklasse_id) REFERENCES Schulklasse(schulklasse_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE BuchTitel (
  titel_id INT PRIMARY KEY,
  titel VARCHAR(255) NOT NULL,
  verlag VARCHAR(255) NOT NULL,
  auflage INT NOT NULL CHECK (auflage > 0),
  isbn VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE BuchExemplar (
  exemplar_id INT PRIMARY KEY,
  isbn VARCHAR(50) NOT NULL,
  exemplar_nr INT NOT NULL CHECK (exemplar_nr > 0),
  qr_code VARCHAR(100) NOT NULL UNIQUE,
  zustand VARCHAR(50) NOT NULL DEFAULT 'i.O.'
    CHECK (zustand IN ('i.O.', 'beschädigt', 'stark beschädigt', 'verloren')),
  CONSTRAINT fk_be_bt FOREIGN KEY (isbn) REFERENCES BuchTitel(isbn) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE Ausleihe_Aktuell (
  exemplar_id INT PRIMARY KEY,
  studierende_id INT NOT NULL,
  CONSTRAINT fk_aa_be FOREIGN KEY (exemplar_id) REFERENCES BuchExemplar(exemplar_id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_aa_s FOREIGN KEY (studierende_id) REFERENCES Studierende(studierende_id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- TESTDATEN

INSERT INTO Schuljahr VALUES (1,'25/26'), (2,'26/27');
INSERT INTO Schulklasse VALUES (1,'FSWI-1',1), (2,'FSWI-2',2);
INSERT INTO Studierende VALUES
(1,'Max','Müller','AKTIV',2), (2,'Lisa','Schmidt','AKTIV',2), (3,'Ali','Yilmaz','AKTIV',2),
(4,'Jonas','Becker','AKTIV',2), (5,'Mia','Wagner','AKTIV',2), (6,'Noah','Weber','AKTIV',2),
(7,'Sara','Kaya','INAKTIV',2), (8,'Can','Öztürk','AKTIV',2), (9,'Laura','Maier','AKTIV',2),
(10,'Tim','Schulz','AKTIV',2), (11,'Ayse','Kara','AKTIV',2), (12,'David','Lang','AKTIV',2),
(13,'Sophie','Brandt','AKTIV',1), (14,'Kevin','Wolf','AKTIV',1), (15,'Nina','Roth','INAKTIV',1);

INSERT INTO BuchTitel VALUES
(1,'Datenbanken Grundlagen','Springer',3,'9781234567890'),
(2,'Java für Einsteiger','Rheinwerk',2,'9789876543210'),
(3,'SQL kompakt','Pearson',1,'9781111111111'),
(4,'Netzwerke Basics','Hanser',2,'9782222222222'),
(5,'Projektmanagement','Hanser',1,'9784444444444');

INSERT INTO BuchExemplar (exemplar_id, isbn, exemplar_nr, qr_code, zustand) VALUES
(1,'9781234567890',1,'DB-001','i.O.'),
(2,'9781234567890',2,'DB-002','i.O.'),
(3,'9781234567890',3,'DB-003','i.O.'),
(4,'9781234567890',4,'DB-004','beschädigt'),
(5,'9781234567890',5,'DB-005','i.O.'),
(6,'9781234567890',6,'DB-006','i.O.');

CREATE VIEW v_exemplar_status AS
SELECT e.exemplar_id, e.qr_code, e.exemplar_nr, e.zustand, t.titel, t.verlag, t.auflage, t.isbn,
  CASE WHEN a.exemplar_id IS NULL THEN 'VERFUEGBAR' ELSE 'AUSGELIEHEN' END AS ausleih_status
FROM BuchExemplar e
JOIN BuchTitel t ON t.isbn = e.isbn
LEFT JOIN Ausleihe_Aktuell a ON a.exemplar_id = e.exemplar_id;

CREATE VIEW v_studierende_ausleihen AS
SELECT s.studierende_id, s.vorname, s.nachname, s.status AS schueler_status, sk.name AS schulklasse, sj.jahr AS schuljahr,
       e.qr_code, e.zustand, t.titel, t.isbn
FROM Studierende s
JOIN Schulklasse sk ON sk.schulklasse_id = s.schulklasse_id
JOIN Schuljahr sj ON sj.schuljahr_id = sk.schuljahr_id
LEFT JOIN Ausleihe_Aktuell a ON a.studierende_id = s.studierende_id
LEFT JOIN BuchExemplar e ON e.exemplar_id = a.exemplar_id
LEFT JOIN BuchTitel t ON t.isbn = e.isbn; -- Korrigiert: Join über ISBN

CREATE VIEW v_bestand_titel AS
SELECT t.titel_id, t.titel, t.isbn, t.verlag, t.auflage,
  COUNT(e.exemplar_id) AS anzahl_exemplare,
  SUM(CASE WHEN a.exemplar_id IS NULL THEN 0 ELSE 1 END) AS aktuell_ausgeliehen
FROM BuchTitel t
LEFT JOIN BuchExemplar e ON e.isbn = t.isbn -- Korrigiert: Join über ISBN
LEFT JOIN Ausleihe_Aktuell a ON a.exemplar_id = e.exemplar_id
GROUP BY t.titel_id, t.titel, t.isbn, t.verlag, t.auflage;

CREATE VIEW v_schulklasse_uebersicht AS
SELECT sj.jahr AS schuljahr, sk.name AS schulklasse, COUNT(s.studierende_id) AS anzahl_schueler
FROM Schulklasse sk
JOIN Schuljahr sj ON sj.schuljahr_id = sk.schuljahr_id
LEFT JOIN Studierende s ON s.schulklasse_id = sk.schulklasse_id
GROUP BY sj.jahr, sk.name;