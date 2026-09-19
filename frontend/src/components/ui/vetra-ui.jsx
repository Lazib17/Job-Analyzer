import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export function VetraButton({
  children,
  variant = 'primary',
  className,
  loading,
  disabled,
  ...props
}) {
  const isPrimary = variant === 'primary';

  return (
    <motion.button
      whileHover={disabled || loading ? {} : { scale: 1.02 }}
      whileTap={disabled || loading ? {} : { scale: 0.98 }}
      disabled={disabled || loading}
      className={cn(
        'relative overflow-hidden inline-flex items-center justify-center gap-2 font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed',
        isPrimary
          ? 'px-5 py-2.5 rounded-xl bg-brand-gradient text-surface-950 text-sm font-semibold shadow-glow-sm hover:brightness-110'
          : 'px-5 py-2.5 rounded-xl bg-white/[0.04] text-white/80 text-sm border border-white/[0.08] hover:bg-white/[0.07] hover:border-white/[0.12] hover:text-white backdrop-blur-sm',
        className
      )}
      {...props}
    >
      {isPrimary && !loading && (
        <motion.span
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -skew-x-12"
          initial={{ x: '-150%' }}
          animate={{ x: '250%' }}
          transition={{ duration: 2.5, repeat: Infinity, repeatDelay: 4, ease: 'easeInOut' }}
        />
      )}
      <span className="relative flex items-center gap-2">
        {loading ? (
          <span className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
        ) : null}
        {children}
      </span>
    </motion.button>
  );
}

export function VetraCard({ children, className, hover = false }) {
  return (
    <div
      className={cn(
        'rounded-3xl border border-white/[0.06] bg-white/[0.02] backdrop-blur-sm p-6 shadow-soft',
        hover && 'transition-all duration-soft hover:border-brand-500/20 hover:bg-white/[0.035] hover:shadow-lift',
        className
      )}
    >
      {children}
    </div>
  );
}

export function VetraInput({ label, className, ...props }) {
  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-[11px] uppercase tracking-[0.12em] text-white/35 font-medium">
          {label}
        </label>
      )}
      <input
        className={cn(
          'w-full px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.07]',
          'text-white text-sm placeholder:text-white/25',
          'transition-all duration-300',
          'focus:outline-none focus:border-brand-500/40 focus:bg-white/[0.05]',
          'focus:shadow-[0_0_0_3px_rgba(20,184,166,0.12)]',
          className
        )}
        {...props}
      />
    </div>
  );
}

export function VetraSelect({ label, children, className, ...props }) {
  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-[11px] uppercase tracking-[0.12em] text-white/35 font-medium">
          {label}
        </label>
      )}
      <select
        className={cn(
          'w-full px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.07]',
          'text-white text-sm',
          'transition-all duration-300',
          'focus:outline-none focus:border-white/15 focus:bg-white/[0.05]',
          className
        )}
        {...props}
      >
        {children}
      </select>
    </div>
  );
}
