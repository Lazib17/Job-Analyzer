-- Google Sign-In columns. Run this in the Supabase SQL Editor
-- (project jemwudtkxbmcyqwzkhcx → SQL Editor → New query → Run).

ALTER TABLE public.users
    ALTER COLUMN password_hash DROP NOT NULL;

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS google_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id
    ON public.users (google_id)
    WHERE google_id IS NOT NULL;
