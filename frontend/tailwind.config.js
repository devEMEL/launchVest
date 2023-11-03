/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    fontFamily: { Montserrat: ['"Montserrat"'] },
    extend: {},
  },
  daisyui: {
    themes: ['lofi'],
  },
  plugins: [require('daisyui')],
}
