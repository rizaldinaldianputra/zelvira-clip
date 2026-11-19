import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import ValidationError
from app.agents.base import BaseAgent
from app.schemas.agent import TranscriptChunk, MomentCandidate, MomentFinderOutput
from app.core.llm import call_llm
from app.core.logging import logger

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "moment_finder.md"

class MomentFinderAgent(BaseAgent):
    def __init__(self):
        super().__init__("moment_finder")
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()

    def _analyze_single_chunk(
        self,
        chunk: TranscriptChunk,
        target_duration: int,
        user_key: str,
        model: str,
        provider: str,
        base_url: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> tuple[List[MomentCandidate], List[Dict[str, Any]]]:
        prompt = self.prompt_template.format(
            transcript_chunk=chunk.formatted_text,
            target_duration=target_duration
        )

        messages = [
            {"role": "system", "content": "You are a professional video editor and viral short content finder. Respond strictly in JSON format."},
            {"role": "user", "content": prompt}
        ]

        usage_records = []
        max_retries = 2
        for attempt in range(max_retries + 1):
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

                # Validate with Pydantic
                if isinstance(output, str):
                    output = json.loads(output)
                
                validated = MomentFinderOutput.model_validate(output)
                return validated.moments, usage_records

            except (ValidationError, Exception) as err:
                logger.warning(f"MomentFinder parse attempt {attempt + 1} failed for chunk {chunk.chunk_index}: {err}")
                if attempt < max_retries:
                    # Provide corrective feedback to the LLM
                    messages.append({"role": "assistant", "content": json.dumps(output) if isinstance(output, dict) else str(output)})
                    messages.append({
                        "role": "user",
                        "content": f"The response was invalid: {str(err)}. Please re-format strictly as JSON matching {{\"moments\": [{{start_sec, end_sec, score, category, hook, reason}}]}}."
                    })
                else:
                    logger.error(f"Failed to find moments for chunk {chunk.chunk_index} after retries.")
                    return [], usage_records

        return [], usage_records

    def run(
        self,
        chunks: List[TranscriptChunk],
        target_duration: int,
        user_key: str,
        model: str,
        provider: str,
        base_url: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> tuple[List[MomentCandidate], List[Dict[str, Any]]]:
        all_moments: List[MomentCandidate] = []
        all_usages: List[Dict[str, Any]] = []

        if not chunks:
            return all_moments, all_usages

        logger.info(f"Finding moments across {len(chunks)} chunks with model {model} (max 3 concurrent)...")

        # Concurrency limit: 3 chunks at a time
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_chunk = {
                executor.submit(
                    self._analyze_single_chunk,
                    chunk,
                    target_duration,
                    user_key,
                    model,
                    provider,
                    base_url,
                    job_id
                ): chunk for chunk in chunks
            }

            for future in as_completed(future_to_chunk):
                try:
                    moments, usages = future.result()
                    all_moments.extend(moments)
                    all_usages.extend(usages)
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")

        logger.info(f"Discovered {len(all_moments)} candidate moments.")
        return all_moments, all_usages
