from typing import List
from app.agents.base import BaseAgent
from app.schemas.agent import TranscriptData, TranscriptChunk, SegmentTranscript

def format_seconds_to_mmss(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

class ChunkerAgent(BaseAgent):
    def __init__(self, target_chunk_sec: float = 480.0, overlap_sec: float = 30.0):
        super().__init__("chunker")
        self.target_chunk_sec = target_chunk_sec
        self.overlap_sec = overlap_sec

    def run(self, transcript: TranscriptData) -> List[TranscriptChunk]:
        segments = transcript.segments
        if not segments:
            return []

        chunks: List[TranscriptChunk] = []
        chunk_idx = 0
        current_chunk_segments: List[SegmentTranscript] = []
        chunk_start_sec = segments[0].start

        i = 0
        n = len(segments)

        while i < n:
            seg = segments[i]
            current_chunk_segments.append(seg)
            chunk_duration = seg.end - chunk_start_sec

            # Check if chunk reached target duration or is the last segment
            if chunk_duration >= self.target_chunk_sec or i == n - 1:
                # Format chunk as [timestamp_sec] text so LLM knows absolute seconds accurately
                formatted_lines = []
                for s in current_chunk_segments:
                    time_label_mmss = format_seconds_to_mmss(s.start)
                    formatted_lines.append(f"[{time_label_mmss} | {s.start:.1f}s] {s.text}")

                chunks.append(TranscriptChunk(
                    chunk_index=chunk_idx,
                    start_sec=chunk_start_sec,
                    end_sec=seg.end,
                    formatted_text="\n".join(formatted_lines),
                    segments=current_chunk_segments
                ))
                chunk_idx += 1

                if i == n - 1:
                    break

                # Calculate overlap: rewind index to first segment within (seg.end - overlap_sec)
                overlap_target = seg.end - self.overlap_sec
                rewind_idx = i
                while rewind_idx > 0 and segments[rewind_idx].start > overlap_target:
                    rewind_idx -= 1

                # If rewind didn't move backwards, advance at least 1 segment to prevent infinite loop
                if rewind_idx >= i:
                    i += 1
                else:
                    i = rewind_idx + 1

                if i < n:
                    chunk_start_sec = segments[i].start
                    current_chunk_segments = []
            else:
                i += 1

        return chunks
