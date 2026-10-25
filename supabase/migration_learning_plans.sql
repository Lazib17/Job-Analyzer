-- Study plans and task progress.
-- Supabase SQL Editor → New query → paste → Run.

CREATE TABLE IF NOT EXISTS public.learning_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    duration_weeks INTEGER NOT NULL,
    hours_per_week INTEGER NOT NULL,
    start_date DATE,
    study_days JSONB,
    japanese_level TEXT,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.learning_plan_weeks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES public.learning_plans(id) ON DELETE CASCADE,
    week_number INTEGER NOT NULL,
    goal TEXT NOT NULL,
    UNIQUE (plan_id, week_number)
);

CREATE TABLE IF NOT EXISTS public.learning_plan_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES public.learning_plans(id) ON DELETE CASCADE,
    week_id UUID NOT NULL REFERENCES public.learning_plan_weeks(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    title TEXT NOT NULL,
    resource_id TEXT,
    resource_snapshot JSONB,
    estimated_minutes INTEGER NOT NULL,
    done BOOLEAN DEFAULT FALSE
);
