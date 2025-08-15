/** @type {import("eslint").Linter.Config} */
module.exports = {
  extends: [
    "next/core-web-vitals",
    "prettier"
  ],
  plugins: ["prettier"],
  rules: {
    "prettier/prettier": "error",
  },
  root: true,
}