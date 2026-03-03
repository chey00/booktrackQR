import os
import pymysql
from dotenv import load_dotenv

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QProgressBar
)


class ConfigError(Exception):
    pass


def load_db_config(env_path: str) -> dict:
    if not os.path.exists(env_path):
        raise ConfigError(f"Konfigurationsdatei fehlt: {env_path}")

    load_dotenv(env_path, override=True)

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_CONNECT_TIMEOUT"]
    missing = [k for k in required if os.getenv(k) is None or os.getenv(k) == ""]
    if missing:
        raise ConfigError("Fehlende ENV Variablen: " + ", ".join(missing))

    try:
        port = int(os.environ["DB_PORT"].strip())
        timeout = int(os.environ["DB_CONNECT_TIMEOUT"].strip())
    except ValueError as e:
        raise ConfigError(f"DB_PORT/DB_CONNECT_TIMEOUT müssen Zahlen sein: {e}")

    return {
        "host": os.environ["DB_HOST"].strip(),
        "port": port,
        "db": os.environ["DB_NAME"].strip(),
        "user": os.environ["DB_USER"].strip(),
        "password": os.environ["DB_PASSWORD"],  #
        "timeout": timeout,
    }


def check_db_connection(cfg: dict) -> tuple[bool, str, str]:
    try:
        conn = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["db"],
            connect_timeout=cfg["timeout"],
            read_timeout=cfg["timeout"],
            write_timeout=cfg["timeout"],
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        conn.close()
        return True, "Verbindung erfolgreich", ""

    except pymysql.err.OperationalError as e:
        msg = str(e).lower()

        if (
            "can't connect" in msg
            or "connection refused" in msg
            or "timed out" in msg
            or "no route" in msg
            or "lost connection" in msg
        ):
            return False, "Server/DB nicht erreichbar", str(e)

        if "access denied" in msg:
            return False, "Verbindungsparameter prüfen", str(e)

        if "unknown database" in msg:
            return False, "Datenbankname prüfen", str(e)

        return False, "Datenbankfehler", str(e)

    except Exception as e:
        return False, "Unbekannter Fehler", str(e)


class DbWorker(QObject):
    finished = pyqtSignal(bool, str, str)

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg

    def run(self):
        ok, user_msg, tech_msg = check_db_connection(self.cfg)
        self.finished.emit(ok, user_msg, tech_msg)


class LoadingGate(QWidget):

    def __init__(self, on_success, env_filename: str = ".env"):
        super().__init__()
        self.on_success = on_success

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.env_path = os.path.join(base_dir, env_filename)

        self.setWindowTitle("Bücher App")
        self.setFixedSize(520, 320)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.MSWindowsFixedSizeDialogHint)


        self.title = QLabel("Bücher App")
        self.title.setObjectName("Title")

        self.subtitle = QLabel("Starte und verbinde zur Datenbank…")
        self.subtitle.setObjectName("SubTitle")

        self.status = QLabel("Initialisiere")
        self.status.setObjectName("Status")

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setObjectName("Progress")

        self.retry_btn = QPushButton("Erneut versuchen")
        self.retry_btn.setObjectName("PrimaryButton")
        self.retry_btn.setEnabled(False)
        self.retry_btn.clicked.connect(self.start_check)

        self.exit_btn = QPushButton("Beenden")
        self.exit_btn.setObjectName("GhostButton")
        self.exit_btn.clicked.connect(self.close)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.exit_btn)
        btn_row.addWidget(self.retry_btn)

        # Card layout
        card = QWidget()
        card.setObjectName("Card")
        card_layout = QVBoxLayout()
        card_layout.setSpacing(10)
        card_layout.addWidget(self.title)
        card_layout.addWidget(self.subtitle)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.status)
        card_layout.addWidget(self.progress)
        card_layout.addStretch(1)
        card_layout.addLayout(btn_row)
        card.setLayout(card_layout)

        root = QVBoxLayout()
        root.setContentsMargins(18, 18, 18, 18)
        root.addWidget(card)
        self.setLayout(root)


        self.setStyleSheet("""
            QWidget {
                background: #0b1220;
                color: #e8eefc;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial;
            }
            #Card {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 16px;
                padding: 18px;
            }
            #Title {
                font-size: 26px;
                font-weight: 700;
                letter-spacing: 0.3px;
            }
            #SubTitle {
                font-size: 13px;
                color: rgba(232, 238, 252, 0.75);
            }
            #Status {
                font-size: 14px;
                font-weight: 600;
            }
            #Progress {
                height: 10px;
                border-radius: 6px;
                background: rgba(255, 255, 255, 0.10);
            }
            #Progress::chunk {
                border-radius: 6px;
                background: rgba(142, 169, 255, 0.95);
            }
            QPushButton {
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }
            #PrimaryButton {
                background: rgba(142, 169, 255, 0.95);
                color: #0b1220;
                border: none;
            }
            #PrimaryButton:disabled {
                background: rgba(142, 169, 255, 0.35);
                color: rgba(11, 18, 32, 0.55);
            }
            #GhostButton {
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.16);
                color: rgba(232, 238, 252, 0.85);
            }
            #GhostButton:hover {
                border-color: rgba(255, 255, 255, 0.28);
            }
        """)


        self.thread: QThread | None = None
        self.worker: DbWorker | None = None
        self.cfg: dict | None = None


        self._dots = 0
        self._base_status_text = "Verbinde zur Datenbank"
        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(350)
        self._dot_timer.timeout.connect(self._tick_dots)

        self.start_check()

    def _tick_dots(self):
        self._dots = (self._dots + 1) % 4
        self.status.setText(self._base_status_text + ("." * self._dots))

    def _set_busy(self, busy: bool):
        self.progress.setVisible(busy)
        if busy:
            self.progress.setRange(0, 0)
            self._dot_timer.start()
        else:
            self._dot_timer.stop()
            self.progress.setRange(0, 1)
            self.progress.setValue(1)

    def start_check(self):
        self.retry_btn.setEnabled(False)


        self.subtitle.setText("Lese Konfiguration aus .env…")
        self.status.setText("Initialisiere")
        self._set_busy(True)

        try:
            self.cfg = load_db_config(self.env_path)
        except ConfigError as e:
            self._set_busy(False)
            self.subtitle.setText("Konfiguration prüfen")
            self.status.setText("❌ Konfigurationsfehler")
            QMessageBox.critical(self, "Config Fehler", str(e))
            self.retry_btn.setEnabled(True)
            return


        self.subtitle.setText("Prüfe Datenbankverbindung…")
        self._base_status_text = "Verbinde zur Datenbank"
        self.status.setText(self._base_status_text)

        self.thread = QThread()
        self.worker = DbWorker(self.cfg)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_result)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_result(self, ok: bool, user_msg: str, tech_msg: str):
        self._set_busy(False)

        if ok:
            self.subtitle.setText("Alles bereit")
            self.status.setText("✅ Verbindung erfolgreich")
            QTimer.singleShot(450, self._open_app)
        else:

            print("DB TECH ERROR:", tech_msg)
            self.subtitle.setText("Verbindung fehlgeschlagen")
            self.status.setText(f"❌ {user_msg}")
            QMessageBox.critical(self, "Verbindung fehlgeschlagen", user_msg)
            self.retry_btn.setEnabled(True)

    def _open_app(self):
        self.on_success()
        self.close()
