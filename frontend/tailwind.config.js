/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        /* Semantic bridges → CSS vars in index.css */
        border: 'hsl(var(--border) / <alpha-value>)',
        input: 'hsl(var(--input) / <alpha-value>)',
        ring: 'hsl(var(--ring) / <alpha-value>)',
        background: 'hsl(var(--background) / <alpha-value>)',
        foreground: 'hsl(var(--foreground) / <alpha-value>)',
        primary: {
          DEFAULT: 'hsl(var(--primary) / <alpha-value>)',
          foreground: 'hsl(var(--primary-foreground) / <alpha-value>)',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted) / <alpha-value>)',
          foreground: 'hsl(var(--muted-foreground) / <alpha-value>)',
        },
        card: {
          DEFAULT: 'hsl(var(--card) / <alpha-value>)',
          foreground: 'hsl(var(--card-foreground) / <alpha-value>)',
        },

        /* App surfaces — cool charcoal (dark premium base) */
        surface: {
          950: '#06080a',
          900: '#0b0f12',
          800: '#12181d',
          700: '#1a2229',
          600: '#243039',
          500: '#334155',
        },

        /*
         * Brand: slate → teal → emerald
         * Use for CTAs, active nav, score accents, chart strokes — not every surface.
         */
        brand: {
          DEFAULT: '#14b8a6',
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
          glow: 'rgba(20, 184, 166, 0.35)',
          soft: 'rgba(20, 184, 166, 0.12)',
        },
        emerald: {
          accent: '#34d399',
        },

        /* Job-platform badge accents (distinct, small chips only) */
        platform: {
          mynavi: '#3b82f6',
          careercross: '#f59e0b',
          wantedly: '#f43f5e',
          gaijinpot: '#22c55e',
        },

        /* Legacy aliases so existing classes keep compiling during staged redesign */
        dark: {
          900: '#06080a',
          800: '#0b0f12',
          700: '#12181d',
          600: '#1a2229',
          500: '#243039',
        },
        accent: {
          DEFAULT: '#14b8a6',
          light: '#2dd4bf',
          dark: '#0d9488',
        },
      },

      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Inter Tight"', 'Inter', 'system-ui', 'sans-serif'],
      },

      fontSize: {
        'display-2xl': ['4.5rem', { lineHeight: '1.05', letterSpacing: '-0.04em', fontWeight: '700' }],
        'display-xl': ['3.75rem', { lineHeight: '1.08', letterSpacing: '-0.035em', fontWeight: '700' }],
        'display-lg': ['3rem', { lineHeight: '1.1', letterSpacing: '-0.03em', fontWeight: '650' }],
        'display-md': ['2.25rem', { lineHeight: '1.15', letterSpacing: '-0.025em', fontWeight: '650' }],
        'display-sm': ['1.875rem', { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '600' }],
      },

      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },

      boxShadow: {
        soft: '0 4px 24px -4px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(255, 255, 255, 0.04)',
        lift: '0 12px 40px -8px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.06)',
        glow: '0 0 32px -4px rgba(20, 184, 166, 0.45)',
        'glow-sm': '0 0 20px -2px rgba(20, 184, 166, 0.35)',
        'accent-glow': '0 8px 28px -6px rgba(99, 102, 241, 0.55)',
        glass: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.06), 0 8px 32px -8px rgba(0, 0, 0, 0.5)',
      },

      backgroundImage: {
        'accent-gradient':
          'linear-gradient(135deg, #312e81 0%, #2563eb 48%, #7c3aed 100%)',
        'brand-gradient':
          'linear-gradient(135deg, #0f766e 0%, #14b8a6 45%, #34d399 100%)',
        'brand-gradient-soft':
          'linear-gradient(135deg, rgba(15, 118, 110, 0.2) 0%, rgba(20, 184, 166, 0.12) 50%, rgba(52, 211, 153, 0.08) 100%)',
        'mesh-dark':
          'radial-gradient(ellipse 80% 60% at 20% 10%, rgba(20, 184, 166, 0.18), transparent 50%), radial-gradient(ellipse 60% 50% at 80% 20%, rgba(52, 211, 153, 0.1), transparent 45%), radial-gradient(ellipse 50% 40% at 50% 90%, rgba(15, 118, 110, 0.12), transparent 50%)',
        shimmer:
          'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.06) 50%, transparent 100%)',
      },

      transitionDuration: {
        micro: '180ms',
        soft: '220ms',
      },

      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'fade-up': 'fadeUp 0.55s cubic-bezier(0.22, 1, 0.36, 1)',
        shimmer: 'shimmer 1.6s ease-in-out infinite',
        'pulse-glow': 'pulseGlow 3.5s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.45' },
          '50%': { opacity: '0.85' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
};
