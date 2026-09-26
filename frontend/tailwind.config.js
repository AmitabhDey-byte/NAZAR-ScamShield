/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#06111f',
        panel: '#0b1728',
        ink: '#f8fafc',
        muted: '#93a4ba',
        bronze: '#22d3ee',
        gold: '#3b82f6',
        safe: '#25c281',
        warning: '#f5a524',
        danger: '#ff5d73',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        signal: '0 0 48px rgba(34, 211, 238, 0.12)',
      },
    },
  },
  plugins: [],
}
