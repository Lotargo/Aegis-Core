/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aegis: {
          green: '#00ff41',
          dark: '#0d1117',
          panel: '#161b22',
        }
      }
    },
  },
  plugins: [],
}
