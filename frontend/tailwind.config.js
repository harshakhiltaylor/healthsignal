/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        softly: {
          bg: "#FDFCF8",
          sage: "#E8EFE8",
          lavender: "#EFEDF4",
          coral: "#FFB7B2",
          dark: "#292524",
          muted: "#78716C",
        }
      },
      fontFamily: {
        sans: ['var(--font-outfit)', 'sans-serif'],
        cursive: ['var(--font-reenie)', 'cursive'],
      },
      animation: {
        'blob': 'blob 6s infinite',
        'reveal': 'reveal 0.8s ease-out forwards',
      },
      keyframes: {
        blob: {
          '0%, 100%': { transform: 'translateY(-10px)' },
          '50%': { transform: 'translateY(10px)' },
        },
        reveal: {
          '0%': { transform: 'translateY(30px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
};
