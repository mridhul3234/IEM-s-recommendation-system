/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        bgBase: '#0B0F15',
        bgSurface: '#11161F',
        bgBorder: '#1F2736',
        accentPrimary: '#D2F85B',
        accentSecondary: '#2A3442',
        textPrimary: '#E5E9F0',
        textMuted: '#8F9BAC',
      },
      fontFamily: {
        display: ['Outfit', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
