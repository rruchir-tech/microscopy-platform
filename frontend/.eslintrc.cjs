module.exports = {
  root: true,
  env: { browser: true, es2021: true },
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  settings: { react: { version: "18" } },
  ignorePatterns: ["dist", "node_modules", "playwright-report"],
  rules: {},
};
