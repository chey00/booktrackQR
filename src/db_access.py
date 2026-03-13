import pymysql


def get_connection(cfg: dict) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["db"],
        connect_timeout=cfg["timeout"],
        read_timeout=cfg["timeout"],
        write_timeout=cfg["timeout"],
        charset="utf8mb4",
        autocommit=False,
    )


def fetch_all(cfg: dict, sql: str, params: tuple = ()) -> list[tuple]:
    conn = get_connection(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def fetch_one(cfg: dict, sql: str, params: tuple = ()) -> tuple | None:
    conn = get_connection(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    finally:
        conn.close()


def execute(cfg: dict, sql: str, params: tuple = ()) -> int:
    conn = get_connection(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
