module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "type-enum": [
      2,
      "always",
      [
        "feat", // New feature
        "fix", // Bug fix
        "docs", // Documentation only changes
        "style", // Changes that don't affect code meaning (white-space, formatting)
        "refactor", // Code change that neither fixes a bug nor adds a feature
        "perf", // Performance improvements
        "test", // Adding or updating tests
        "chore", // Maintenance tasks, dependency updates
        "ci", // CI/CD changes
        "build", // Build system or external dependencies
        "revert", // Revert a previous commit
      ],
    ],
  },
};