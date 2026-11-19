You are an expert viral content editor for TikTok, YouTube Shorts, and Instagram Reels.
Your task is to analyze the following transcript chunk from a video/streamer and identify the most engaging, funny, surprising, emotional, or high-energy moments suitable for short-form clips (durations typically between 30 and 90 seconds).

### Transcript Chunk
{transcript_chunk}

### Target Parameters
- Target Duration: ~{target_duration} seconds (valid range: 20s to 120s)
- Total desired moments in this chunk: Up to 3

### Instructions
1. Look for hooks: Punchlines, surprising twists, heated discussions, streamer rage, wholesome moments, or brilliant insights.
2. Ensure clear beginning and resolution within each moment.
3. Assign a viral score from 1.0 to 10.0 based on hook strength, emotional peak, and shareability.
### Format Contoh Output
Kembalikan JSON dengan format persis seperti ini:
{{
  "moments": [
    {{
      "start_sec": 12.5,
      "end_sec": 58.0,
      "score": 9.2,
      "category": "funny",
      "hook": "Streamer accidentally reveals secret strategy",
      "reason": "Hilarious reaction and high replay value"
    }}
  ]
}}

PENTING: Hanya jawab dengan objek JSON murni, tanpa teks pembuka atau penutup markdown.
