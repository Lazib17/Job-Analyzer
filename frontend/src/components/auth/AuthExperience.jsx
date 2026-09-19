import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRight, Check, Eye, EyeOff, Lock, Mail, User } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import GoogleSignInButton from '@/components/auth/GoogleSignInButton';
import { cn } from '@/lib/utils';

const focusGlow = 'shadow-[0_0_0_3px_rgba(99,102,241,0.28)]';
const successGlow = 'shadow-[0_0_0_3px_rgba(129,140,248,0.22)]';

function Field({
  id,
  label,
  icon: Icon,
  type = 'text',
  value,
  onChange,
  onBlur,
  error,
  success,
  autoComplete,
  required,
  showToggle,
  revealed,
  onToggleReveal,
}) {
  const [focused, setFocused] = useState(false);

  return (
    <motion.div
      animate={error ? { x: [0, -7, 7, -4, 4, 0] } : { x: 0 }}
      transition={{ duration: 0.35 }}
      className="relative"
    >
      <label htmlFor={id} className="mb-1.5 block text-xs font-medium text-white/55">
        {label}
      </label>
      <div
        className={cn(
          'relative rounded-xl border bg-white/[0.04] transition-all duration-soft',
          error
            ? 'border-red-400/50 shadow-[0_0_0_3px_rgba(248,113,113,0.14)]'
            : success
              ? `border-indigo-400/50 ${successGlow}`
              : focused
                ? `border-indigo-400/60 ${focusGlow} bg-white/[0.06]`
                : 'border-white/[0.1] hover:border-white/[0.18]'
        )}
      >
        <Icon
          className={cn(
            'pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2',
            error ? 'text-red-400/80' : focused || success ? 'text-indigo-300' : 'text-white/30'
          )}
          strokeWidth={1.75}
        />
        <input
          id={id}
          type={showToggle ? (revealed ? 'text' : 'password') : type}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          required={required}
          onFocus={() => setFocused(true)}
          onBlur={() => {
            setFocused(false);
            onBlur?.();
          }}
          className="w-full bg-transparent py-3 pl-10 pr-11 text-sm text-white outline-none placeholder:text-white/25"
          placeholder={label}
        />
        <div className="absolute right-2.5 top-1/2 flex -translate-y-1/2 items-center gap-0.5">
          {success && (
            <Check className="h-4 w-4 text-indigo-300" strokeWidth={2} />
          )}
          {showToggle && (
            <button
              type="button"
              onClick={onToggleReveal}
              className="rounded-lg p-1 text-white/35 hover:bg-white/[0.06] hover:text-white/70"
              tabIndex={-1}
            >
              {revealed ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            </button>
          )}
        </div>
      </div>
      {error && <p className="mt-1.5 text-xs text-red-400/90">{error}</p>}
    </motion.div>
  );
}

/**
 * Shared Sign In / Sign Up UI.
 * Auth API calls stay in Login.jsx / Register.jsx — this is presentation only.
 */
export function AuthExperience({
  mode = 'login',
  onSubmit,
  onGoogle,
  onGoogleError,
  loading = false,
  googleLoading = false,
  serverError = '',
}) {
  const navigate = useNavigate();
  const isLogin = mode === 'login';

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [touched, setTouched] = useState({});

  const emailOk = useMemo(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email), [form.email]);
  const passwordOk = form.password.length >= 6;
  const confirmOk = !isLogin && form.confirmPassword.length > 0 && form.password === form.confirmPassword;
  const nameOk = !isLogin && form.name.trim().length >= 2;

  const markTouched = (key) => setTouched((prev) => ({ ...prev, [key]: true }));

  const set = (key) => (e) => {
    setForm((prev) => ({ ...prev, [key]: e.target.value }));
    if (fieldErrors[key]) setFieldErrors((prev) => ({ ...prev, [key]: '' }));
  };

  const validate = () => {
    const next = {};
    if (!isLogin && form.name.trim().length < 2) next.name = 'Enter your full name';
    if (!emailOk) next.email = 'Enter a valid email';
    if (!passwordOk) next.password = 'Password must be at least 6 characters';
    if (!isLogin && form.password !== form.confirmPassword) {
      next.confirmPassword = 'Passwords do not match';
    }
    setFieldErrors(next);
    setTouched({ name: true, email: true, password: true, confirmPassword: true });
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit({
      name: form.name.trim(),
      email: form.email.trim(),
      password: form.password,
    });
  };

  const switchMode = (next) => {
    navigate(next === 'login' ? '/login' : '/register');
  };

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-[#07070e] font-sans text-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-[#07070e]" />
        <motion.div
          className="absolute -left-24 top-10 h-80 w-80 rounded-full bg-indigo-700/30 blur-[110px]"
          animate={{ y: [0, -22, 0], opacity: [0.45, 0.75, 0.45] }}
          transition={{ duration: 9, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute right-[-4rem] top-24 h-96 w-96 rounded-full bg-violet-600/25 blur-[120px]"
          animate={{ y: [0, 18, 0], opacity: [0.35, 0.6, 0.35] }}
          transition={{ duration: 11, repeat: Infinity, ease: 'easeInOut', delay: 0.8 }}
        />
        <motion.div
          className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-blue-600/20 blur-[100px]"
          animate={{ x: [0, 24, 0], opacity: [0.3, 0.55, 0.3] }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut', delay: 1.4 }}
        />
      </div>

      <header className="relative z-10 mx-auto flex w-full max-w-[440px] items-center px-4 pt-8">
        <Link to="/" className="font-display text-sm font-semibold tracking-tight text-white">
          Job Analyzer
        </Link>
      </header>

      <div className="relative z-10 flex flex-1 items-center justify-center px-4 py-10 sm:py-14">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-[440px]"
        >
          <div className="relative overflow-hidden rounded-3xl border border-white/[0.1] bg-white/[0.05] p-7 shadow-lift backdrop-blur-xl sm:p-9">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-400/50 to-transparent" />

            <h1 className="font-display text-2xl font-bold tracking-tight text-white sm:text-[1.75rem]">
              {isLogin ? 'Welcome back' : 'Create your account'}
            </h1>
            <p className="mt-1.5 text-sm text-white/45">
              {isLogin
                ? 'Sign in to see ranked Japan tech matches.'
                : 'Start matching your resume to jobs across four boards.'}
            </p>

            <div className="relative mt-6 mb-7 grid grid-cols-2 rounded-xl border border-white/[0.08] bg-black/25 p-1">
              <motion.div
                className="absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-lg bg-accent-gradient shadow-accent-glow"
                animate={{ x: isLogin ? 0 : '100%' }}
                transition={{ type: 'spring', stiffness: 380, damping: 32 }}
              />
              {['login', 'register'].map((tab) => {
                const active = (tab === 'login') === isLogin;
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => switchMode(tab)}
                    className={cn(
                      'relative z-10 rounded-lg py-2 text-sm font-semibold transition-colors duration-soft',
                      active ? 'text-white' : 'text-white/45 hover:text-white/75'
                    )}
                  >
                    {tab === 'login' ? 'Sign In' : 'Sign Up'}
                  </button>
                );
              })}
            </div>

            <AnimatePresence mode="wait">
              {serverError ? (
                <motion.div
                  key={serverError}
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mb-5 rounded-xl border border-red-400/25 bg-red-500/10 px-4 py-3 text-sm text-red-300"
                >
                  {serverError}
                </motion.div>
              ) : null}
            </AnimatePresence>

            {onGoogle && (
              <>
                <GoogleSignInButton
                  loading={googleLoading}
                  onSuccess={onGoogle}
                  onError={(message) => onGoogleError?.(message)}
                />
                <div className="my-5 flex items-center gap-3">
                  <div className="h-px flex-1 bg-white/10" />
                  <span className="text-[11px] font-medium uppercase tracking-[0.16em] text-white/35">or</span>
                  <div className="h-px flex-1 bg-white/10" />
                </div>
              </>
            )}

            <AnimatePresence mode="wait">
              <motion.form
                key={mode}
                initial={{ opacity: 0, x: isLogin ? -12 : 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: isLogin ? 12 : -12 }}
                transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                onSubmit={handleSubmit}
                className="space-y-3.5"
              >
                {!isLogin && (
                  <Field
                    id="auth-name"
                    label="Full name"
                    icon={User}
                    value={form.name}
                    onChange={set('name')}
                    onBlur={() => markTouched('name')}
                    error={touched.name ? fieldErrors.name || (form.name && !nameOk ? 'Enter your full name' : '') : ''}
                    success={nameOk}
                    autoComplete="name"
                    required
                  />
                )}

                <Field
                  id="auth-email"
                  label="Email"
                  icon={Mail}
                  type="email"
                  value={form.email}
                  onChange={set('email')}
                  onBlur={() => markTouched('email')}
                  error={touched.email ? fieldErrors.email || (form.email && !emailOk ? 'Enter a valid email' : '') : ''}
                  success={emailOk}
                  autoComplete="email"
                  required
                />

                <Field
                  id="auth-password"
                  label="Password"
                  icon={Lock}
                  value={form.password}
                  onChange={set('password')}
                  onBlur={() => markTouched('password')}
                  error={
                    touched.password
                      ? fieldErrors.password || (form.password && !passwordOk ? 'Password must be at least 6 characters' : '')
                      : ''
                  }
                  success={passwordOk}
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  required
                  showToggle
                  revealed={showPassword}
                  onToggleReveal={() => setShowPassword((v) => !v)}
                />

                {!isLogin && (
                  <Field
                    id="auth-confirm"
                    label="Confirm password"
                    icon={Lock}
                    value={form.confirmPassword}
                    onChange={set('confirmPassword')}
                    onBlur={() => markTouched('confirmPassword')}
                    error={
                      touched.confirmPassword
                        ? fieldErrors.confirmPassword ||
                          (form.confirmPassword && !confirmOk ? 'Passwords do not match' : '')
                        : ''
                    }
                    success={confirmOk}
                    autoComplete="new-password"
                    required
                    showToggle
                    revealed={showConfirm}
                    onToggleReveal={() => setShowConfirm((v) => !v)}
                  />
                )}

                <motion.button
                  type="submit"
                  disabled={loading}
                  whileHover={loading ? {} : { scale: 1.02 }}
                  whileTap={loading ? {} : { scale: 0.98 }}
                  className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-accent-gradient py-3.5 text-[15px] font-semibold text-white shadow-accent-glow disabled:opacity-70"
                >
                  {loading ? (
                    <>
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      {isLogin ? 'Signing in…' : 'Creating account…'}
                    </>
                  ) : (
                    <>
                      {isLogin ? 'Sign in' : 'Create account'}
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </motion.button>
              </motion.form>
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
