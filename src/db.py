# src/db.py
# ─────────────────────────────────────────────────────────────────────────────
# Neo4j connection wrapper. Import this in every module that needs database
# access. Never instantiate the driver directly in application code.
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class Neo4jConnection:
    """
    Thread-safe connection wrapper around the Neo4j Python driver.

    The driver manages a pool of Bolt connections internally. One instance
    per application process is the recommended pattern.

    Usage (as context manager — preferred):
        with Neo4jConnection() as db:
            rows = db.read("MATCH (m:Movie) RETURN m.title AS title")

    Usage (manual lifecycle):
        db = Neo4jConnection()
        db.write("MERGE (m:Movie {title: $title})", {"title": "Dangal"})
        db.close()
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        _uri  = uri      or os.getenv("NEO4J_URI",      "bolt://localhost:7687")
        _user = user     or os.getenv("NEO4J_USER",     "neo4j")
        _pass = password or os.getenv("NEO4J_PASSWORD", "bollywood2024!")

        self._driver = GraphDatabase.driver(_uri, auth=(_user, _pass))
        self._driver.verify_connectivity()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def write(self, query: str, params: Optional[dict] = None) -> None:
        """Execute a write query (MERGE, CREATE, SET, DELETE)."""
        with self._driver.session() as session:
            session.run(query, params or {})

    def read(self, query: str, params: Optional[dict] = None) -> list[dict]:
        """Execute a read query and return results as a list of dicts."""
        with self._driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def write_batch(self, query: str, rows: list[dict], batch_size: int = 200) -> int:
        """
        Bulk-write using UNWIND. The query must accept $rows as a list.

        Example query:
            UNWIND $rows AS row
            MERGE (m:Movie {title: row.title})
            SET m.year = row.year
        """
        total = 0
        with self._driver.session() as session:
            for i in range(0, len(rows), batch_size):
                batch = rows[i: i + batch_size]
                session.run(query, {"rows": batch})
                total += len(batch)
        return total

    def close(self) -> None:
        self._driver.close()
