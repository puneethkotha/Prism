/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        prism: {
          50: '#f0f4ff',
          100: '#dde6ff',
          200: '#c4d1ff',
          300: '#a0b3ff',
          400: '#7b8dff',
          500: '#5a65f8',
          600: '#4347ed',
          700: '#3836d2',
          800: '#2f2eaa',
          900: '#2c2c86',
        },
      },
    },
  },
  plugins: [],
}
