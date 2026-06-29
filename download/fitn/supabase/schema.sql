-- Fitn — Supabase SQL schema. See spec §5.2.
--
-- Apply via Supabase SQL editor. Every table is RLS-protected with a
-- `USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)` policy.

-- === Tables ===

-- profiles (1:1 with auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  data JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- plans (1:N with users; one isActive per user)
CREATE TABLE IF NOT EXISTS plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  data JSONB NOT NULL,
  profile_snapshot JSONB NOT NULL,
  preferences_snapshot JSONB NOT NULL,
  engine_version TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT false,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS plans_user_active_generated_idx
  ON plans(user_id, is_active, generated_at DESC);
CREATE INDEX IF NOT EXISTS plans_user_generated_idx
  ON plans(user_id, generated_at DESC);

-- workout_logs (1:N with users + plans)
CREATE TABLE IF NOT EXISTS workout_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES plans(id) ON DELETE SET NULL,
  day_number INT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,
  workout_name TEXT NOT NULL,
  data JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS workout_logs_user_started_idx
  ON workout_logs(user_id, started_at DESC);

-- weight_logs (1:N with users, unique per day)
CREATE TABLE IF NOT EXISTS weight_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  weight_kg NUMERIC(5,1) NOT NULL CHECK (weight_kg BETWEEN 30 AND 300),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, date)
);
CREATE INDEX IF NOT EXISTS weight_logs_user_date_idx
  ON weight_logs(user_id, date DESC);

-- intake_logs (1:N with users, unique per day)
CREATE TABLE IF NOT EXISTS intake_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  intake_kcal INT NOT NULL CHECK (intake_kcal BETWEEN 0 AND 10000),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, date)
);
CREATE INDEX IF NOT EXISTS intake_logs_user_date_idx
  ON intake_logs(user_id, date DESC);

-- === RLS policies (apply to every table) ===

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY profiles_owner ON profiles
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY plans_owner ON plans
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

ALTER TABLE workout_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY workout_logs_owner ON workout_logs
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

ALTER TABLE weight_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY weight_logs_owner ON weight_logs
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

ALTER TABLE intake_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY intake_logs_owner ON intake_logs
  FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- === Triggers (keep updated_at fresh) ===

CREATE OR REPLACE FUNCTION touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS profiles_touch ON profiles;
CREATE TRIGGER profiles_touch BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

DROP TRIGGER IF EXISTS plans_touch ON plans;
CREATE TRIGGER plans_touch BEFORE UPDATE ON plans
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

DROP TRIGGER IF EXISTS workout_logs_touch ON workout_logs;
CREATE TRIGGER workout_logs_touch BEFORE UPDATE ON workout_logs
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

DROP TRIGGER IF EXISTS weight_logs_touch ON weight_logs;
CREATE TRIGGER weight_logs_touch BEFORE UPDATE ON weight_logs
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

DROP TRIGGER IF EXISTS intake_logs_touch ON intake_logs;
CREATE TRIGGER intake_logs_touch BEFORE UPDATE ON intake_logs
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
