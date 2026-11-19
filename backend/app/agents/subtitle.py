import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.agents.base import BaseAgent
from app.schemas.agent import RefinedClip, TranscriptData, WordTimestamp
from app.core.logging import logger

PRESETS: Dict[str, Dict[str, str]] = {
    "bold_yellow": {
        "font_name": "Arial",
        "font_size": "56",
        "primary_color": "&H00FFFFFF",    # White (AABBGGRR)
        "highlight_color": "&H0000D7FF",  # Bright Yellow/Gold
        "outline_color": "&H00000000",    # Black outline
        "outline": "4",
        "shadow": "2",
        "margin_v": "360",
    },
    "classic": {
        "font_name": "Arial",
        "font_size": "52",
        "primary_color": "&H00FFFFFF",    # White
        "highlight_color": "&H00FFFF00",  # Cyan highlight
        "outline_color": "&H00000000",    # Black outline
        "outline": "3",
        "shadow": "1",
        "margin_v": "360",
    },
    "neon": {
        "font_name": "Arial",
        "font_size": "54",
        "primary_color": "&H00D0FF00",    # Vibrant Lime
        "highlight_color": "&H00FF00FF",  # Vibrant Magenta
        "outline_color": "&H00101010",    # Dark outline
        "outline": "4",
        "shadow": "3",
        "margin_v": "360",
    }
}

def format_ass_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

class SubtitleAgent(BaseAgent):
    def __init__(self):
        super().__init__("subtitle")

    def _generate_ass(
        self,
        words_in_clip: List[WordTimestamp],
        clip_start_offset: float,
        preset_name: str,
        ass_file_path: str
    ) -> None:
        style = PRESETS.get(preset_name, PRESETS["bold_yellow"])

        header = f"""[Script Info]
Title: TikTok Viral Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['font_name']},{style['font_size']},{style['primary_color']},&H00000000,{style['outline_color']},&H80000000,-1,0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},2,40,40,{style['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []

        # Group words into short lines of 3-4 words
        words_per_line = 3
        groups: List[List[WordTimestamp]] = []
        for i in range(0, len(words_in_clip), words_per_line):
            groups.append(words_in_clip[i:i + words_per_line])

        for grp in groups:
            if not grp:
                continue

            for active_idx, target_w in enumerate(grp):
                # Word relative timing in clip
                start_t = max(0.0, target_w.start - clip_start_offset)
                end_t = max(start_t + 0.1, target_w.end - clip_start_offset)

                line_parts = []
                for idx, w in enumerate(grp):
                    clean_word = w.word.upper().strip()
                    if idx == active_idx:
                        # Highlight active word
                        line_parts.append(f"{{\\c{style['highlight_color']}}}{clean_word}{{\\c{style['primary_color']}}}")
                    else:
                        line_parts.append(clean_word)

                dialogue_text = " ".join(line_parts)
                start_str = format_ass_timestamp(start_t)
                end_str = format_ass_timestamp(end_t)

                events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{dialogue_text}")

        with open(ass_file_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events) + "\n")

    def run(
        self,
        job_id: str,
        reframed_paths: List[str],
        refined_clips: List[RefinedClip],
        transcript: TranscriptData,
        preset: str = "bold_yellow"
    ) -> List[str]:
        all_words: List[WordTimestamp] = []
        for seg in transcript.segments:
            all_words.extend(seg.words)

        subtitled_paths: List[str] = []

        for idx, (reframed_path, clip_meta) in enumerate(zip(reframed_paths, refined_clips)):
            output_path = reframed_path.replace("_reframed.mp4", "_subtitled.mp4")
            ass_path = reframed_path.replace("_reframed.mp4", ".ass")

            # Filter words belonging to this clip
            clip_start = clip_meta.refined_start
            clip_end = clip_meta.refined_end
            clip_words = [
                w for w in all_words
                if w.start >= clip_start and w.end <= clip_end
            ]

            if not clip_words:
                # Fallback: segment words
                clip_words = [
                    WordTimestamp(word=seg.text, start=seg.start, end=seg.end)
                    for seg in transcript.segments
                    if seg.start >= clip_start and seg.end <= clip_end
                ]

            self._generate_ass(clip_words, clip_start, preset, ass_path)

            logger.info(f"[{job_id}] Burning ASS subtitles into clip #{idx}...")

            # Escape backslashes for FFmpeg subtitle filter
            escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
            cmd = [
                "ffmpeg", "-y",
                "-i", reframed_path,
                "-vf", f"subtitles='{escaped_ass}'",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-c:a", "copy",
                output_path
            ]

            try:
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                subtitled_paths.append(output_path)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed burning subtitles for clip #{idx}: {e.stderr.decode('utf-8', errors='ignore')}")
                # Fallback to reframed video if subtitle burning failed
                subtitled_paths.append(reframed_path)

        return subtitled_paths
