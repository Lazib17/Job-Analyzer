import { animate, motion, useMotionValue, useTransform } from 'framer-motion';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

export default function StatCard({ icon: Icon, label, value, suffix = '', isText = false }) {
  const motionVal = useMotionValue(0);
  const rounded = useTransform(motionVal, (latest) => Math.round(latest));
  const [display, setDisplay] = useState(0);

  useEffect(() => rounded.on('change', (v) => setDisplay(v)), [rounded]);

  useEffect(() => {
    if (isText || typeof value !== 'number') return undefined;
    const controls = animate(motionVal, value, {
      duration: 1.2,
      ease: [0.22, 1, 0.36, 1],
    });
    return () => controls.stop();
  }, [isText, motionVal, value]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-5 shadow-soft"
    >
      <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-accent-gradient text-white shadow-accent-glow">
        {Icon ? <Icon className="h-4.5 w-4.5 h-4 w-4" strokeWidth={1.75} /> : null}
      </div>
      <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-white/40">{label}</p>
      <p className={cn('mt-1 font-display text-2xl font-bold tracking-tight text-white sm:text-3xl')}>
        {isText ? value : `${display.toLocaleString()}${suffix}`}
      </p>
    </motion.div>
  );
}
