from typing import List
from app.agents.base import BaseAgent
from app.schemas.agent import TranscriptData, MomentCandidate, RefinedClip, WordTimestamp

CONJUNCTIONS = {
    # Indonesian
    "dan", "tapi", "tetapi", "jadi", "lalu", "kemudian", "karena", "sebab",
    "atau", "namun", "sehingga", "padahal", "sedangkan", "bahwa",
    # English
    "and", "but", "so", "or", "because", "then", "however", "although", "yet"
}

class BoundaryRefinerAgent(BaseAgent):
    def __init__(self, max_shift_sec: float = 3.0, start_pad_sec: float = 0.3, end_pad_sec: float = 0.5):
        super().__init__("boundary_refiner")
        self.max_shift_sec = max_shift_sec
        self.start_pad_sec = start_pad_sec
        self.end_pad_sec = end_pad_sec

    def run(
        self,
        moments: List[MomentCandidate],
        transcript: TranscriptData,
        video_duration: float
    ) -> List[RefinedClip]:
        # Collect all words in sequential order
        all_words: List[WordTimestamp] = []
        for seg in transcript.segments:
            for w in seg.words:
                all_words.append(w)

        refined_clips: List[RefinedClip] = []

        for m in moments:
            orig_start = m.start_sec
            orig_end = m.end_sec

            best_start = orig_start
            best_end = orig_end

            if all_words:
                # 1. Refine Start: find closest word start within [orig_start - max_shift, orig_start + max_shift]
                start_candidates = [
                    w for w in all_words
                    if abs(w.start - orig_start) <= self.max_shift_sec
                ]
                if start_candidates:
                    # Choose candidate that starts a sentence or isn't a trailing fragment
                    closest_start_word = min(start_candidates, key=lambda w: abs(w.start - orig_start))
                    best_start = closest_start_word.start

                # 2. Refine End: find closest word end within [orig_end - max_shift, orig_end + max_shift]
                end_candidates = [
                    w for w in all_words
                    if abs(w.end - orig_end) <= self.max_shift_sec
                ]
                if end_candidates:
                    # Filter out candidates whose word is an dangling conjunction
                    valid_end_words = [
                        w for w in end_candidates
                        if w.word.lower().strip(".,!?\"'") not in CONJUNCTIONS
                    ]
                    target_pool = valid_end_words if valid_end_words else end_candidates
                    closest_end_word = min(target_pool, key=lambda w: abs(w.end - orig_end))
                    best_end = closest_end_word.end

            # 3. Apply padding
            final_start = max(0.0, best_start - self.start_pad_sec)
            final_end = min(video_duration, best_end + self.end_pad_sec) if video_duration > 0 else best_end + self.end_pad_sec

            # Ensure minimum duration of at least 3 seconds
            if final_end - final_start < 3.0:
                final_end = min(video_duration, final_start + 3.0)

            refined_clips.append(RefinedClip(
                original_start=orig_start,
                original_end=orig_end,
                refined_start=round(final_start, 2),
                refined_end=round(final_end, 2),
                score=m.score,
                category=m.category,
                hook=m.hook,
                reason=m.reason
            ))

        return refined_clips
