import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: '#0066FF',
          red: '#FF4444',
        },
        slate: {
          950: '#020617',
        },
      },
      backgroundImage: {
        'grid-glow':
          'radial-gradient(circle at center, rgba(0,102,255,0.25), transparent 55%), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(0deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
