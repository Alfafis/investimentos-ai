import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def store(tmp_path, monkeypatch):
    """app.experiment.store apontando para um banco temporário."""
    from app.experiment import store as s

    db = tmp_path / "data" / "experiment.db"
    monkeypatch.setattr(s, "_DB_PATH", str(db))
    monkeypatch.setattr(s, "_DATA_DIR", str(db.parent))
    monkeypatch.setattr(s, "_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setattr(s, "_IDEMPOTENCY_INDEX_WARNED", False)
    return s


def count_trades(store_module) -> int:
    with store_module._db() as conn:
        return conn.execute("SELECT COUNT(*) FROM paper_trades").fetchone()[0]


def insert_trade(store_module, ts, action, ticker, price, qty):
    """Insere linha crua com timestamp controlado (evita empates de relógio)."""
    store_module.init_db()
    with store_module._db() as conn:
        conn.execute(
            "INSERT INTO paper_trades (timestamp, action, ticker, price, quantity) "
            "VALUES (?, ?, ?, ?, ?)",
            (ts, action, ticker, price, qty),
        )


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Garante que nenhum teste (yfinance, brapi, BCB, RSS) saia para a rede."""
    import socket

    def _blocked(*a, **k):
        raise RuntimeError("acesso à rede bloqueado nos testes")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
