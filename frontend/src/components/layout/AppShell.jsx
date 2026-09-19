import { motion } from 'framer-motion';

export function AtmosphericBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div className="absolute inset-0 bg-[#07070e]" />

      <motion.div
        className="absolute -top-[20%] left-1/2 h-[50vh] w-[90vw] max-w-[900px] -translate-x-1/2 rounded-full bg-indigo-700/[0.14] blur-[120px]"
        animate={{ opacity: [0.4, 0.7, 0.4], x: ['-50%', '-48%', '-50%'] }}
        transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute -bottom-[15%] -right-[10%] h-[45vh] w-[60vw] max-w-[600px] rounded-full bg-violet-600/[0.1] blur-[100px]"
        animate={{ opacity: [0.3, 0.55, 0.3], scale: [1, 1.05, 1] }}
        transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
      />
      <motion.div
        className="absolute top-[30%] -left-[15%] h-[35vh] w-[40vw] rounded-full bg-blue-600/[0.08] blur-[90px]"
        animate={{ opacity: [0.25, 0.45, 0.25] }}
        transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut', delay: 4 }}
      />

      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,#07070e_75%)] opacity-60" />
    </div>
  );
}

export function AppShell({ children }) {
  return (
    <div className="min-h-screen relative">
      <AtmosphericBackground />
      <motion.main
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative pt-24 pb-16 px-4 sm:px-6 lg:px-8"
      >
        {children}
      </motion.main>
    </div>
  );
}

export function PageHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <motion.header
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 mb-12 lg:mb-16"
    >
      <div className="max-w-2xl">
        {eyebrow && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="text-[11px] uppercase tracking-[0.2em] text-white/35 font-medium mb-3"
          >
            {eyebrow}
          </motion.p>
        )}
        <motion.h1
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="heading-display text-display-sm sm:text-display-md lg:text-[2.75rem] font-semibold leading-[1.15]"
        >
          {title}
        </motion.h1>
        {subtitle && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25, duration: 0.45 }}
            className="mt-3 text-base text-white/45 leading-relaxed max-w-xl"
          >
            {subtitle}
          </motion.p>
        )}
      </div>
      {actions && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="flex flex-wrap gap-3 shrink-0"
        >
          {actions}
        </motion.div>
      )}
    </motion.header>
  );
}

export function SectionTitle({ children, action }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <h2 className="text-sm uppercase tracking-[0.15em] text-white/40 font-medium">{children}</h2>
      {action}
    </div>
  );
}

export function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
      <div className="w-5 h-5 border border-white/10 border-t-white/60 rounded-full animate-spin" />
      <p className="text-sm text-white/40 tracking-wide">{message}</p>
    </div>
  );
}

export function FadeInSection({ children, delay = 0, className = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
