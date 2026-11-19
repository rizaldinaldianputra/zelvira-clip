from pydantic import BaseModel, Field
from typing import List, Optional

# --- TranscribeAgent Schemas ---
class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float

class SegmentTranscript(BaseModel):
    start: float
    end: float
    text: str
    words: List[WordTimestamp] = []

class TranscriptData(BaseModel):
    language: str
    duration: float
    segments: List[SegmentTranscript] = []

# --- ChunkerAgent Schemas ---
class TranscriptChunk(BaseModel):
    chunk_index: int
    start_sec: float
    end_sec: float
    formatted_text: str # "[mm:ss] text"
    segments: List[SegmentTranscript] = []

# --- MomentFinderAgent & RankerAgent Schemas ---
class MomentCandidate(BaseModel):
    start_sec: float = Field(..., description="Start time in seconds")
    end_sec: float = Field(..., description="End time in seconds")
    score: float = Field(..., ge=1, le=10, description="Viral/engagement score from 1-10")
    category: str = Field(..., description="Category, e.g. funny, epic_play, revelation, rage, discussion")
    hook: str = Field(..., description="Attention-grabbing reason in first 3 seconds")
    reason: str = Field(..., description="Why this segment is engaging")

class MomentFinderOutput(BaseModel):
    moments: List[MomentCandidate] = []

class RankerOutput(BaseModel):
    selected_moments: List[MomentCandidate] = []

# --- BoundaryRefiner & ClipCutter Schemas ---
class RefinedClip(BaseModel):
    original_start: float
    original_end: float
    refined_start: float
    refined_end: float
    score: float
    category: str
    hook: str
    reason: str

# --- MetadataAgent Schemas ---
class ClipMetadataOutput(BaseModel):
    title: str = Field(..., max_length=60, description="Catchy viral title under 60 chars")
    caption: str = Field(..., description="Engaging social media caption")
    hashtags: List[str] = Field(..., min_length=3, max_length=8, description="Trending hashtags")
