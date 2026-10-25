-- Japanese level on the user profile.
-- Supabase SQL Editor → New query → paste → Run.
-- (project jemwudtkxbmcyqwzkhcx)

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS japanese_level TEXT;
