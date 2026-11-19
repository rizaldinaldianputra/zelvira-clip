import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.agents.base import BaseAgent
from app.schemas.agent import MomentCandidate, RankerOutput
from app.core.llm import call_llm
from app.core.logging import logger

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "ranker.md"

def calculate_overlap_ratio(m1: MomentCandidate, m2: MomentCandidate) -> float:
    start = max(m1.start_sec, m2.start_sec)
    end = min(m1.end_sec, m2.end_sec)
    overlap = max(0.0, end - start)
    if overlap <= 0:
        return 0.0
    len1 = m1.end_sec - m1.start_sec
    len2 = m2.end_sec - m2.start_sec
    min_len = min(len1, len2)
    return overlap / min_len if min_len > 0 else 0.0

class RankerAgent(BaseAgent):
    def __init__(self):
        super().__init__("ranker")
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()

    def deduplicate(self, candidates: List[MomentCandidate], max_overlap: float = 0.40) -> List[MomentCandidate]:
        # Sort by viral score descending
        sorted_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)
        kept: List[MomentCandidate] = []

        for cand in sorted_candidates:
            has_high_overlap = False
            for existing in kept:
                if calculate_overlap_ratio(cand, existing) > max_overlap:
                    has_high_overlap = True
                    break
            if not has_high_overlap:
                kept.append(cand)

        return kept

    def run(
        self,
        candidates: List[MomentCandidate],
        top_n: int,
        user_key: str,
        model: str,
        provider: str,
        base_url: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> tuple[List[MomentCandidate], List[Dict[str, Any]]]:
        deduped = self.deduplicate(candidates, max_overlap=0.40)
        logger.info(f"Deduplication reduced candidates from {len(candidates)} to {len(deduped)}")

        if not deduped:
            return [], []

        if len(deduped) <= top_n:
            return deduped[:top_n], []

        # Convert candidates to compact JSON for prompt
        candidates_data = [
            {
                "start_sec": c.start_sec,
                "end_sec": c.end_sec,
                "score": c.score,
                "category": c.category,
                "hook": c.hook,
                "reason": c.reason
            }
            for c in deduped
        ]

        prompt = self.prompt_template.format(
            candidates_json=json.dumps(candidates_data, indent=2),
            top_n=top_n
        )

        messages = [
            {"role": "system", "content": "You are a professional content ranker. Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ]

        usage_records = []
        try:
            output, metrics = call_llm(
                user_key=user_key,
                model=model,
                messages=messages,
                provider=provider,
                base_url=base_url,
                json_mode=True
            )
            usage_records.append({
                "agent_name": self.name,
                "model": metrics.get("model_used", model),
                "tokens_in": metrics.get("tokens_in", 0),
                "tokens_out": metrics.get("tokens_out", 0),
                "cost_usd": metrics.get("cost_usd", 0.0),
                "latency_ms": metrics.get("latency_ms", 0),
                "job_id": job_id
            })

            if isinstance(output, str):
                output = json.loads(output)

            validated = RankerOutput.model_validate(output)
            selected = validated.selected_moments[:top_n]
            return selected, usage_records

        except Exception as e:
            logger.warning(f"Ranker LLM call failed: {e}. Falling back to top score selection.")
            return deduped[:top_n], usage_records
