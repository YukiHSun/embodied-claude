"""Auto-start voicevox-core-server (sibling project) if needed."""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)


def _is_responding(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/version", timeout=timeout):
            return True
    except Exception:
        return False


class VoicevoxCoreRunner:
    """Manage a local voicevox-core-server subprocess.

    Launches `uv run --directory <project_dir> voicevox-core-server` when the
    configured VOICEVOX_URL is not reachable. The child's venv carries the
    voicevox_core wheel; we don't need to import it from this process.
    """

    def __init__(
        self,
        project_dir: Path,
        url: str,
        startup_timeout: float = 60.0,
    ) -> None:
        self._project_dir = project_dir
        self._url = url.rstrip("/")
        self._timeout = startup_timeout
        self._process: subprocess.Popen | None = None

    async def start(self) -> bool:
        """Ensure the server is reachable. Returns True if it's now running."""
        if _is_responding(self._url):
            logger.info("voicevox-core-server already running at %s", self._url)
            return True

        if not self._project_dir.exists():
            logger.warning(
                "voicevox-core-server project not found at %s; skipping autostart",
                self._project_dir,
            )
            return False

        uv_bin = shutil.which("uv")
        if not uv_bin:
            logger.warning("`uv` not found in PATH; cannot autostart voicevox-core-server")
            return False

        parsed = urllib.parse.urlparse(self._url)
        env_overrides = {
            "VOICEVOX_HOST": parsed.hostname or "127.0.0.1",
            "VOICEVOX_PORT": str(parsed.port or 50021),
        }

        import os

        env = os.environ.copy()
        env.update(env_overrides)

        logger.info(
            "Starting voicevox-core-server: uv run --directory %s voicevox-core-server",
            self._project_dir,
        )
        self._process = subprocess.Popen(
            [uv_bin, "run", "--directory", str(self._project_dir), "voicevox-core-server"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )

        deadline = asyncio.get_event_loop().time() + self._timeout
        while asyncio.get_event_loop().time() < deadline:
            if self._process.poll() is not None:
                logger.warning("voicevox-core-server exited prematurely")
                return False
            if _is_responding(self._url):
                logger.info(
                    "voicevox-core-server ready at %s (pid=%d)",
                    self._url,
                    self._process.pid,
                )
                return True
            await asyncio.sleep(1.0)

        logger.warning("voicevox-core-server did not become ready within %.1fs", self._timeout)
        return False

    def stop(self) -> None:
        if self._process is None or self._process.poll() is not None:
            return
        logger.info("Stopping voicevox-core-server (pid=%d)", self._process.pid)
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=2)
