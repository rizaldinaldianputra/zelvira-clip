"""
Database seed script for demo and testing.
Creates a demo user and a sample completed job with ready clips.
Run with: python -m scripts.seed
"""
import uuid
import sys
import os
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import get_sync_db
from app.core.security import get_password_hash
from app.core.crypto import encrypt_api_key, create_key_hint
from app.models.user import User
from app.models.job import Job
from app.models.clip import Clip
from app.models.key import UserAIKey, UserAgentModel
from app.models.usage import UsageLog

def seed():
    print("🌱 Seeding database with demo data...")
    with get_sync_db() as db:
        # Check if demo user already exists
        demo_user = db.query(User).filter(User.email == "demo@zelvira.com").first()
        if not demo_user:
            demo_user = User(
                id=str(uuid.uuid4()),
                email="demo@zelvira.com",
                password_hash=get_password_hash("password123")
            )
            db.add(demo_user)
            db.commit()
            print(f"✅ Created demo user: demo@zelvira.com (password: password123)")
        else:
            print("ℹ️ Demo user already exists.")

        # Seed sample OpenAI key placeholder
        existing_key = db.query(UserAIKey).filter(UserAIKey.user_id == demo_user.id).first()
        if not existing_key:
            sample_key_str = "sk-demo1234567890abcdefghijklmnopqrstuvwxyz"
            new_key = UserAIKey(
                user_id=demo_user.id,
                provider="openai",
                encrypted_key=encrypt_api_key(sample_key_str),
                key_hint=create_key_hint(sample_key_str)
            )
            db.add(new_key)
            db.commit()

            # Seed agent models
            db.add(UserAgentModel(user_id=demo_user.id, agent_name="moment_finder", key_id=new_key.id, model="gpt-4o-mini"))
            db.add(UserAgentModel(user_id=demo_user.id, agent_name="ranker", key_id=new_key.id, model="gpt-4o"))
            db.add(UserAgentModel(user_id=demo_user.id, agent_name="metadata", key_id=new_key.id, model="gpt-4o-mini"))
            db.commit()
            print("✅ Seeded sample AI key and agent model settings.")

        # Seed sample completed job
        existing_job = db.query(Job).filter(Job.user_id == demo_user.id).first()
        if not existing_job:
            sample_job = Job(
                id=str(uuid.uuid4()),
                user_id=demo_user.id,
                source_type="youtube",
                source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                title="Never Gonna Give You Up (Streamer Reaction)",
                duration_sec=212.0,
                status="done",
                progress=100,
                settings={"clip_count": 3, "target_duration": 60, "layout": "focus", "subtitle_preset": "bold_yellow", "language": "en"}
            )
            db.add(sample_job)
            db.commit()

            # Add sample clips
            clip1 = Clip(
                job_id=sample_job.id,
                start_sec=18.5,
                end_sec=58.2,
                score=9.4,
                category="funny",
                hook="Streamer realizes he got rickrolled on live stream",
                reason="Peak facial reaction and instant chat engagement",
                title="HE ACTUALLY FELL FOR IT AGAIN 💀",
                caption="I can't believe this still works in 2026 lmao. Watch his face drop when the beat hits!",
                hashtags=["#streamer", "#rickroll", "#reaction", "#funny", "#shorts"],
                file_path=None,
                thumbnail_path=None
            )
            clip2 = Clip(
                job_id=sample_job.id,
                start_sec=90.0,
                end_sec=135.0,
                score=8.7,
                category="highlight",
                hook="Unexpected singing along with chat",
                reason="Wholesome high energy moment",
                title="Bro started singing the whole verse 🔥",
                caption="Chat made him sing the whole song and it was actually fire 😂",
                hashtags=["#streamer", "#karaoke", "#wholesome", "#viral", "#clips"],
                file_path=None,
                thumbnail_path=None
            )
            db.add_all([clip1, clip2])

            # Add sample usage log
            usage = UsageLog(
                job_id=sample_job.id,
                agent_name="moment_finder",
                model="gpt-4o-mini",
                tokens_in=1250,
                tokens_out=340,
                cost_usd=0.00035,
                latency_ms=1240
            )
            db.add(usage)
            db.commit()
            print("✅ Seeded sample completed job with clips and usage metrics.")

    print("🎉 Seeding complete!")

if __name__ == "__main__":
    seed()
