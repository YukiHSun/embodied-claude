"""voicevox_engine-compatible HTTP wrapper around voicevox_core.

Exposes a minimal subset of the voicevox_engine REST API so existing clients
(e.g. tts-mcp's VoicevoxEngine) can connect without modification:

    GET  /version
    GET  /speakers
    POST /audio_query?text=...&speaker=ID
    POST /synthesis?speaker=ID  (body: AudioQuery JSON)
"""

from __future__ import annotations

import dataclasses
import logging
import multiprocessing
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from voicevox_core import AccentPhrase, AudioQuery, Mora
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
VOICEVOX_CORE_DIR = ROOT / "voicevox_core"
DEFAULT_ONNXRUNTIME = (
    VOICEVOX_CORE_DIR / "onnxruntime" / "lib" / Onnxruntime.LIB_VERSIONED_FILENAME
)
DEFAULT_DICT_DIR = VOICEVOX_CORE_DIR / "dict" / "open_jtalk_dic_utf_8-1.11"
DEFAULT_VVM_DIR = VOICEVOX_CORE_DIR / "models" / "vvms"

VERSION = "0.16.4"

# camelCase <-> snake_case mappings used by voicevox_engine REST API.
_AUDIO_QUERY_CAMEL = {
    "accent_phrases": "accent_phrases",
    "speed_scale": "speedScale",
    "pitch_scale": "pitchScale",
    "intonation_scale": "intonationScale",
    "volume_scale": "volumeScale",
    "pre_phoneme_length": "prePhonemeLength",
    "post_phoneme_length": "postPhonemeLength",
    "output_sampling_rate": "outputSamplingRate",
    "output_stereo": "outputStereo",
    "kana": "kana",
}
_AUDIO_QUERY_SNAKE = {v: k for k, v in _AUDIO_QUERY_CAMEL.items()}

_MORA_CAMEL = {
    "text": "text",
    "consonant": "consonant",
    "consonant_length": "consonant_length",
    "vowel": "vowel",
    "vowel_length": "vowel_length",
    "pitch": "pitch",
}
_ACCENT_PHRASE_CAMEL = {
    "moras": "moras",
    "accent": "accent",
    "pause_mora": "pause_mora",
    "is_interrogative": "is_interrogative",
}


_AUDIO_QUERY_S2C = {
    "speed_scale": "speedScale",
    "pitch_scale": "pitchScale",
    "intonation_scale": "intonationScale",
    "volume_scale": "volumeScale",
    "pre_phoneme_length": "prePhonemeLength",
    "post_phoneme_length": "postPhonemeLength",
    "output_sampling_rate": "outputSamplingRate",
    "output_stereo": "outputStereo",
}
_AUDIO_QUERY_C2S = {v: k for k, v in _AUDIO_QUERY_S2C.items()}


def audio_query_to_json(q: AudioQuery) -> dict[str, Any]:
    d = dataclasses.asdict(q)
    return {_AUDIO_QUERY_S2C.get(k, k): v for k, v in d.items()}


def _mora_from_dict(d: dict[str, Any]) -> Mora:
    return Mora(
        text=d["text"],
        consonant=d.get("consonant"),
        consonant_length=d.get("consonant_length"),
        vowel=d["vowel"],
        vowel_length=d["vowel_length"],
        pitch=d["pitch"],
    )


def _accent_phrase_from_dict(d: dict[str, Any]) -> AccentPhrase:
    return AccentPhrase(
        moras=[_mora_from_dict(m) for m in d["moras"]],
        accent=d["accent"],
        pause_mora=_mora_from_dict(d["pause_mora"]) if d.get("pause_mora") else None,
        is_interrogative=d.get("is_interrogative", False),
    )


def audio_query_from_json(d: dict[str, Any]) -> AudioQuery:
    snake = {_AUDIO_QUERY_C2S.get(k, k): v for k, v in d.items()}
    return AudioQuery(
        accent_phrases=[_accent_phrase_from_dict(a) for a in snake["accent_phrases"]],
        speed_scale=snake.get("speed_scale", 1.0),
        pitch_scale=snake.get("pitch_scale", 0.0),
        intonation_scale=snake.get("intonation_scale", 1.0),
        volume_scale=snake.get("volume_scale", 1.0),
        pre_phoneme_length=snake.get("pre_phoneme_length", 0.1),
        post_phoneme_length=snake.get("post_phoneme_length", 0.1),
        output_sampling_rate=snake.get("output_sampling_rate", 24000),
        output_stereo=snake.get("output_stereo", False),
        kana=snake.get("kana"),
    )


class SynthesizerHolder:
    def __init__(self) -> None:
        self.synthesizer: Synthesizer | None = None
        self.speakers: list[dict[str, Any]] = []

    def load(self) -> None:
        onnxruntime_path = os.environ.get(
            "VOICEVOX_ONNXRUNTIME", str(DEFAULT_ONNXRUNTIME)
        )
        dict_dir = os.environ.get("VOICEVOX_DICT_DIR", str(DEFAULT_DICT_DIR))
        vvm_dir = Path(os.environ.get("VOICEVOX_VVM_DIR", str(DEFAULT_VVM_DIR)))

        logger.info("Loading ONNX Runtime: %s", onnxruntime_path)
        ort = Onnxruntime.load_once(filename=onnxruntime_path)
        logger.info("Initializing Synthesizer (dict_dir=%s)", dict_dir)
        self.synthesizer = Synthesizer(
            ort,
            OpenJtalk(dict_dir),
            cpu_num_threads=max(multiprocessing.cpu_count(), 2),
        )

        def _vvm_sort_key(p: Path) -> tuple[int, str]:
            stem = p.stem
            return (int(stem), "") if stem.isdigit() else (10**9, stem)

        vvm_files = sorted(vvm_dir.glob("*.vvm"), key=_vvm_sort_key)
        logger.info("Loading %d voice models from %s", len(vvm_files), vvm_dir)
        for vvm in vvm_files:
            try:
                with VoiceModelFile.open(vvm) as model:
                    self.synthesizer.load_voice_model(model)
            except Exception as e:
                logger.warning("Skipped %s: %s", vvm.name, e)

        self.speakers = [dataclasses.asdict(m) for m in self.synthesizer.metas()]
        logger.info("Loaded %d speakers", len(self.speakers))


holder = SynthesizerHolder()


@asynccontextmanager
async def lifespan(app: FastAPI):
    holder.load()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/version")
def version() -> Response:
    # voicevox_engine returns a bare JSON string for /version.
    return JSONResponse(content=VERSION)


@app.get("/speakers")
def speakers() -> JSONResponse:
    return JSONResponse(content=holder.speakers)


@app.post("/audio_query")
def audio_query(text: str, speaker: int) -> JSONResponse:
    if holder.synthesizer is None:
        raise HTTPException(status_code=503, detail="Synthesizer not ready")
    try:
        q = holder.synthesizer.create_audio_query(text, speaker)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return JSONResponse(content=audio_query_to_json(q))


@app.post("/synthesis")
async def synthesis(request: Request, speaker: int) -> Response:
    if holder.synthesizer is None:
        raise HTTPException(status_code=503, detail="Synthesizer not ready")
    body = await request.json()
    try:
        q = audio_query_from_json(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid AudioQuery: {e}") from e
    try:
        wav = holder.synthesizer.synthesis(q, speaker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return Response(content=wav, media_type="audio/wav")


def main() -> None:
    import uvicorn

    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    host = os.environ.get("VOICEVOX_HOST", "127.0.0.1")
    port = int(os.environ.get("VOICEVOX_PORT", "50021"))
    uvicorn.run(
        "voicevox_core_server.server:app",
        host=host,
        port=port,
        log_level=os.environ.get("UVICORN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
