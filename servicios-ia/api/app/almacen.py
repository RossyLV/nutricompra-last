"""Almacén de votos ("me gusta / no me gusta") en una base de datos SQLite.

SQLite viene incluida con Python: no hay que instalar nada. Todo se guarda en
un solo archivo (por defecto datos/preferencias.db).

Hay dos tablas:
- votos: el voto ACTUAL de cada usuario por alimento. Un voto nuevo sobre el mismo
  alimento reemplaza al anterior (el último voto manda).
- historial: cada voto que se emitió, en orden. Sirve para el dashboard
  (por ejemplo, para graficar cómo evolucionan las preferencias).

Seguridad: todas las consultas usan parámetros (?) y nunca se pegan textos del
usuario dentro del SQL. Así se evita la "inyección SQL".
"""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app import config

_CREAR_TABLAS = (
    """
    CREATE TABLE IF NOT EXISTS votos (
        usuario_id  TEXT NOT NULL,
        alimento    TEXT NOT NULL,
        voto        TEXT NOT NULL CHECK (voto IN ('me_gusta', 'no_me_gusta')),
        actualizado TEXT NOT NULL,
        PRIMARY KEY (usuario_id, alimento)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS historial (
        orden       INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id  TEXT NOT NULL,
        alimento    TEXT NOT NULL,
        voto        TEXT NOT NULL,
        fecha       TEXT NOT NULL
    )
    """,
)


def _ahora() -> str:
    """Fecha y hora actual en UTC, como texto (ej. 2026-11-04T20:15:00+00:00)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Almacen:
    """Guarda y consulta los votos de los usuarios.

    Crear un Almacen NO toca el disco: el archivo se crea la primera vez que se usa.
    Los datos que llegan aquí ya deben estar validados (ver app.validacion).
    """

    def __init__(self, ruta: Path | str | None = None):
        self.ruta = Path(ruta) if ruta else config.RUTA_BASE_DATOS

    def _conectar(self) -> sqlite3.Connection:
        """Abre la base (y la prepara si es la primera vez)."""
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        conexion = sqlite3.connect(self.ruta)
        for sentencia in _CREAR_TABLAS:
            conexion.execute(sentencia)
        return conexion

    def registrar_voto(self, usuario_id: str, alimento: str, voto: str) -> int:
        """Guarda el voto (reemplaza el anterior sobre el mismo alimento).

        Devuelve cuántos alimentos tiene votados ese usuario en total.
        """
        ahora = _ahora()
        # "with conexion" confirma los cambios (commit) o los deshace si hay error
        with closing(self._conectar()) as conexion, conexion:
            conexion.execute(
                """
                INSERT INTO votos (usuario_id, alimento, voto, actualizado)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (usuario_id, alimento)
                DO UPDATE SET voto = excluded.voto, actualizado = excluded.actualizado
                """,
                (usuario_id, alimento, voto, ahora),
            )
            conexion.execute(
                "INSERT INTO historial (usuario_id, alimento, voto, fecha) VALUES (?, ?, ?, ?)",
                (usuario_id, alimento, voto, ahora),
            )
            (total,) = conexion.execute(
                "SELECT COUNT(*) FROM votos WHERE usuario_id = ?", (usuario_id,)
            ).fetchone()
        return total

    def obtener_votos(self, usuario_id: str) -> dict[str, str]:
        """Votos actuales del usuario: {alimento: "me_gusta" | "no_me_gusta"}."""
        with closing(self._conectar()) as conexion:
            filas = conexion.execute(
                "SELECT alimento, voto FROM votos WHERE usuario_id = ? ORDER BY alimento",
                (usuario_id,),
            ).fetchall()
        return dict(filas)

    def obtener_historial(self, usuario_id: str) -> list[dict]:
        """Todos los votos emitidos, del primero al último (numerados 1, 2, 3...)."""
        with closing(self._conectar()) as conexion:
            filas = conexion.execute(
                "SELECT alimento, voto, fecha FROM historial WHERE usuario_id = ? ORDER BY orden",
                (usuario_id,),
            ).fetchall()
        return [
            {"numero": i, "alimento": alimento, "voto": voto, "fecha": fecha}
            for i, (alimento, voto, fecha) in enumerate(filas, start=1)
        ]

    def reiniciar(self, usuario_id: str) -> int:
        """Borra los votos y el historial del usuario. Devuelve cuántos votos tenía."""
        with closing(self._conectar()) as conexion, conexion:
            borrados = conexion.execute(
                "DELETE FROM votos WHERE usuario_id = ?", (usuario_id,)
            ).rowcount
            conexion.execute("DELETE FROM historial WHERE usuario_id = ?", (usuario_id,))
        return borrados
