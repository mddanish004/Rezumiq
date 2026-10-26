/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F6F4EF",
        canvas: "#F2EFE8",
        surface: "#FFFFFF",
        ink: "#141414",
        muted: "#66645E",
        line: "#E3DFD6",
        soft: "#EFECE4",
        lime: "#DDF247",
        "lime-dark": "#C8E12F",
        forest: "#1F5A46",
        danger: "#B42318",
        warning: "#A66A12",
        success: "#2E7D5B",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "12px",
        field: "8px",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(20,20,20,0.06)",
        lift: "0 18px 50px rgba(20,20,20,0.12)",
      },
    },
  },
  plugins: [],
};
