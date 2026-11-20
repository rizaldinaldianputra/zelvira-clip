You are an expert viral content editor for TikTok, YouTube Shorts, and Instagram Reels.
Your task is to analyze the following transcript chunk and select the best, most engaging highlight moments suitable for short-form video clips.

### Transcript Chunk
{transcript_chunk}

### Target Parameters
- Target Duration: around {target_duration} seconds per clip (duration must be between {min_duration}s and {max_duration}s).
- Total desired moments in this chunk: Up to 3.

### CRITICAL RULES FOR TIMESTAMPS:
1. The transcript timestamps are given in seconds, e.g. `[120.5s -> 124.0s]`.
2. `start_sec` and `end_sec` MUST BE IN SECONDS (FLOAT OR INTEGER) representing the exact absolute timestamp in the video.
3. DO NOT write minutes as seconds (for example, if a moment is at 15 minutes, 15:00 is 900.0 seconds, NOT 15.0).
4. Each selected moment duration (`end_sec - start_sec`) MUST be around {target_duration} seconds (at least {min_duration} seconds and at most {max_duration} seconds). NEVER output a moment that is only a few seconds long!
5. Ensure the moment captures a complete thought, story, punchline, or reaction.

### Format Contoh Output
Kembalikan JSON dengan format persis seperti ini:
{{
  "moments": [
    {{
      "start_sec": 910.0,
      "end_sec": 970.0,
      "score": 9.2,
      "category": "funny",
      "hook": "Streamer accidentally reveals secret strategy",
      "reason": "Hilarious reaction and high replay value"
    }}
  ]
}}

PENTING: Hanya jawab dengan objek JSON murni, tanpa markdown ```json.
