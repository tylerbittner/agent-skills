# Agent Skills

A collection of [Agent Skills](https://agentskills.io) — the open standard for giving AI agents new capabilities.

Compatible with: Claude Code, Cursor, GitHub Copilot, Codex, Gemini CLI, OpenClaw, OpenCode, and any agent that supports the AgentSkills format.

## Skills

| Skill | Description |
|-------|-------------|
| [spaced-repetition](./spaced-repetition/) | Adaptive spaced repetition engine using the FSRS-6 algorithm. Schedules flashcard reviews with scientifically optimal intervals and multi-mode review coaching. |

## Installation

### OpenClaw
```bash
# Skills are auto-discovered in the workspace skills/ directory
cp -r spaced-repetition/ ~/.openclaw/workspace/skills/
```

### Claude Code / Cursor / Copilot
```bash
# Copy to your project's .agent/skills/ directory
cp -r spaced-repetition/ .agent/skills/
```

Or clone this repo and symlink the skills you want.

## Contributing

PRs welcome for new skills or improvements to existing ones. Each skill should follow the [AgentSkills spec](https://agentskills.io).

## License

MIT
