-- Cache YouTube picks per skill and stage for 30 days.
-- Supabase SQL Editor → New query → paste → Run.

CREATE TABLE IF NOT EXISTS public.learning_video_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_key TEXT NOT NULL,
    stage TEXT NOT NULL,
    payload JSONB NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (skill_key, stage)
);
