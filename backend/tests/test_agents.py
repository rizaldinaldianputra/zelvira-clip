import pytest
from app.agents.chunker import ChunkerAgent
from app.agents.boundary_refiner import BoundaryRefinerAgent
from app.agents.ranker import RankerAgent, calculate_overlap_ratio
from app.schemas.agent import TranscriptData, SegmentTranscript, WordTimestamp, MomentCandidate

def test_chunker_agent():
    # Build 10 minutes of segments
    segments = []
    for i in range(20):
        start = float(i * 30)
        end = float((i + 1) * 30)
        segments.append(SegmentTranscript(
            start=start,
            end=end,
            text=f"Segment number {i} talking about gaming highlights.",
            words=[WordTimestamp(word=f"word{i}", start=start, end=end)]
        ))

    transcript = TranscriptData(language="id", duration=600.0, segments=segments)
    chunker = ChunkerAgent(target_chunk_sec=240.0, overlap_sec=30.0)
    chunks = chunker.run(transcript)

    assert len(chunks) >= 2
    assert "[00:00]" in chunks[0].formatted_text

def test_ranker_overlap_deduplication():
    # Two clips with high overlap (80%)
    c1 = MomentCandidate(start_sec=10.0, end_sec=50.0, score=9.5, category="funny", hook="Hook 1", reason="Reason 1")
    c2 = MomentCandidate(start_sec=15.0, end_sec=52.0, score=7.0, category="funny", hook="Hook 2", reason="Reason 2")
    # One separate clip
    c3 = MomentCandidate(start_sec=120.0, end_sec=160.0, score=8.0, category="epic", hook="Hook 3", reason="Reason 3")

    ranker = RankerAgent()
    ratio = calculate_overlap_ratio(c1, c2)
    assert ratio > 0.40

    deduped = ranker.deduplicate([c1, c2, c3], max_overlap=0.40)
    assert len(deduped) == 2
    # Ensure higher scoring c1 is kept over c2
    assert c1 in deduped
    assert c2 not in deduped
    assert c3 in deduped

def test_boundary_refiner_pads_and_avoids_conjunctions():
    words = [
        WordTimestamp(word="halo", start=10.1, end=10.5),
        WordTimestamp(word="semuanya", start=10.6, end=11.2),
        WordTimestamp(word="hari", start=11.3, end=11.6),
        WordTimestamp(word="ini", start=11.7, end=12.0),
        WordTimestamp(word="kita", start=12.1, end=12.4),
        WordTimestamp(word="menang", start=12.5, end=13.0),
        WordTimestamp(word="tapi", start=13.1, end=13.4), # conjunction
        WordTimestamp(word="susah", start=13.5, end=14.0)
    ]
    transcript = TranscriptData(
        language="id",
        duration=30.0,
        segments=[SegmentTranscript(start=10.0, end=14.0, text="halo semuanya hari ini kita menang tapi susah", words=words)]
    )

    candidate = MomentCandidate(
        start_sec=10.0,
        end_sec=13.2, # Near "tapi"
        score=9.0,
        category="highlight",
        hook="Win moment",
        reason="Good finish"
    )

    refiner = BoundaryRefinerAgent(max_shift_sec=2.0, start_pad_sec=0.3, end_pad_sec=0.5)
    refined = refiner.run([candidate], transcript, video_duration=30.0)

    assert len(refined) == 1
    # Check that padding was applied
    assert refined[0].refined_start <= candidate.start_sec
    assert refined[0].refined_end > candidate.start_sec
