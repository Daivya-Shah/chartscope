/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        clinical: {
          50: "#f0f7fa",
          100: "#daedf3",
          200: "#b8dbe8",
          300: "#89c0d4",
          400: "#559fb8",
          500: "#3a839e",
          600: "#326a82",
          700: "#2d576b",
          800: "#2b4959",
          900: "#273e4c",
          950: "#172833",
        },
        sage: {
          50: "#f4f7f4",
          100: "#e3ebe3",
          200: "#c8d7c9",
          300: "#a0bba3",
          400: "#759a7a",
          500: "#567d5c",
          600: "#426449",
          700: "#36503c",
          800: "#2d4132",
          900: "#26362b",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        display: ["DM Sans", "Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
