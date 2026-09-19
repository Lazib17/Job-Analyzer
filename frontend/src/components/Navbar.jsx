import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Briefcase, ChevronDown, FileText, LayoutDashboard, LogOut, Search, Settings, User } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';

const APP_NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/upload', label: 'Upload CV', icon: FileText },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/results', label: 'Results', icon: Briefcase },
];

const PUBLIC_LINKS = [
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How it works' },
];

function PublicNavbar() {
  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <nav className="border-b border-white/[0.08] bg-[#07070e]/75 backdrop-blur-xl">
        <div className="relative mx-auto flex h-[72px] w-full max-w-[1280px] items-center px-4 sm:px-6 lg:px-8">
          <Link to="/" className="relative z-10 shrink-0 font-display text-base font-semibold tracking-tight text-white">
            Job Analyzer
          </Link>
          <div className="pointer-events-none absolute inset-0 hidden items-center justify-center md:flex">
            <div className="pointer-events-auto flex items-center gap-8">
              {PUBLIC_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-white/55 transition-colors duration-soft hover:text-white"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>
          <div className="relative z-10 ml-auto flex shrink-0 items-center gap-2 sm:gap-3">
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Link
                to="/login"
                className="inline-flex items-center rounded-xl border border-white/20 bg-transparent px-3.5 py-2 text-sm font-medium text-white/90 hover:border-white/40 hover:bg-white/[0.06] sm:px-4"
              >
                Sign In
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Link
                to="/register"
                className="inline-flex items-center rounded-xl bg-accent-gradient px-3.5 py-2 text-sm font-semibold text-white shadow-accent-glow sm:px-4"
              >
                Get Started
              </Link>
            </motion.div>
          </div>
        </div>
      </nav>
    </header>
  );
}

function initials(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'U';
}

export default function Navbar({ user, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  if (!user) return <PublicNavbar />;

  const handleLogout = () => {
    setMenuOpen(false);
    onLogout();
    navigate('/login');
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50 px-4 pt-4 sm:px-6 lg:px-8">
      <motion.nav
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mx-auto flex h-16 max-w-7xl items-center justify-between rounded-2xl border border-white/[0.08] bg-[#07070e]/75 px-3 shadow-glass backdrop-blur-xl sm:px-5"
      >
        <Link to="/" className="shrink-0 font-display text-sm font-semibold tracking-tight text-white sm:text-base">
          Job Analyzer
        </Link>

        <div className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-1 md:flex">
          {APP_NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to;
            return (
              <Link
                key={to}
                to={to}
                className={`relative flex items-center gap-1.5 rounded-full px-3 py-2 text-xs font-medium transition-colors ${
                  active ? 'text-white' : 'text-white/45 hover:text-white/80'
                }`}
              >
                {active && (
                  <motion.span
                    layoutId="nav-active-pill"
                    className="absolute inset-0 rounded-full bg-white/[0.08]"
                    transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                  />
                )}
                <Icon className="relative z-10 h-3.5 w-3.5" strokeWidth={1.75} />
                <span className="relative z-10">{label}</span>
              </Link>
            );
          })}
        </div>

        <div className="relative ml-auto" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] py-1 pl-1 pr-2 hover:bg-white/[0.08]"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-gradient text-xs font-semibold text-white">
              {initials(user.name)}
            </span>
            <span className="hidden max-w-[100px] truncate text-xs text-white/70 sm:block">{user.name}</span>
            <ChevronDown className={`h-3.5 w-3.5 text-white/40 transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
          </button>

          <AnimatePresence>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, y: 6, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.98 }}
                transition={{ duration: 0.16 }}
                className="absolute right-0 mt-2 w-48 overflow-hidden rounded-xl border border-white/[0.08] bg-[#101018]/95 py-1 shadow-lift backdrop-blur-xl"
              >
                <Link
                  to="/upload"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:bg-white/[0.05] hover:text-white"
                >
                  <User className="h-4 w-4" /> Profile
                </Link>
                <Link
                  to="/upload"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:bg-white/[0.05] hover:text-white"
                >
                  <Settings className="h-4 w-4" /> Settings
                </Link>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-white/70 hover:bg-white/[0.05] hover:text-white"
                >
                  <LogOut className="h-4 w-4" /> Logout
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.nav>
    </header>
  );
}
