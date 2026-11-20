import os
import json
import subprocess
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel
from app.agents.base import BaseAgent
from app.schemas.agent import TranscriptData, SegmentTranscript, WordTimestamp
from app.core.config import settings
from app.core.logging import logger
from app.core.storage import storage

class TranscribeAgent(BaseAgent):
    def __init__(self, model_size: Optional[str] = None):
        super().__init__("transcribe")
        self.model_size = model_size or settings.WHISPER_MODEL
        self._model: Optional[WhisperModel] = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            logger.info(f"Loading faster-whisper model: {self.model_size} with multithreading...")
            # Use CPU with int8 and 4 threads for high performance
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
                num_workers=2
            )
        return self._model

    def run(self, job_id: str, video_path: str, language_hint: str = "auto") -> TranscriptData:
        job_dir = Path(storage.get_full_path(f"jobs/{job_id}"))
        audio_path = str(job_dir / "audio.wav")
        transcript_json_path = str(job_dir / "transcript.json")

        # Step 1: Extract mono 16kHz audio using ffmpeg
        logger.info(f"[{job_id}] Extracting 16kHz mono audio from video...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_path
        ]
        try:
            subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg audio extraction failed: {e.stderr.decode('utf-8', errors='ignore')}")
            raise RuntimeError("Failed to extract audio from video.") from None

        # Step 2: Transcribe using faster-whisper with word timestamps
        logger.info(f"[{job_id}] Transcribing audio with faster-whisper...")
        model = self._get_model()

        # Language selection
        whisper_lang = None
        if language_hint in ("id", "en"):
            whisper_lang = language_hint

        segments_iter, info = model.transcribe(
            audio_path,
            language=whisper_lang,
            word_timestamps=True,
            vad_filter=True, # Voice activity detection to skip silence
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        detected_lang = info.language if hasattr(info, "language") else "id"
        logger.info(f"[{job_id}] Detected language: {detected_lang} (prob: {getattr(info, 'language_probability', 1.0):.2f})")

        segments_data = []
        for seg in segments_iter:
            words_data = []
            if seg.words:
                for w in seg.words:
                    words_data.append(WordTimestamp(
                        word=w.word.strip(),
                        start=round(w.start, 2),
                        end=round(w.end, 2)
                    ))
            
            segments_data.append(SegmentTranscript(
                start=round(seg.start, 2),
                end=round(seg.end, 2),
                text=seg.text.strip(),
                words=words_data
            ))

        transcript_output = TranscriptData(
            language=detected_lang,
            duration=round(info.duration if hasattr(info, "duration") else 0.0, 2),
            segments=segments_data
        )

        # Step 3: Save to transcript.json in job folder
        with open(transcript_json_path, "w", encoding="utf-8") as f:
            json.dump(transcript_output.model_dump(), f, indent=2, ensure_ascii=False)

        logger.info(f"[{job_id}] Transcription complete. Saved to {transcript_json_path}")
        return transcript_output
