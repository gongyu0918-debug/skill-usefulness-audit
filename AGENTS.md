# Project Maintenance Notes

## Release Split

- Keep the GitHub repository as the full multi-agent edition. The root README and `codex-skill/` may document Codex, OpenClaw, Hermes, Claude Code, and other host-specific metadata when supported.
- Keep the ClawHub bundle in `skill/` as the OpenClaw-only edition. Do not include Hermes, Claude Code, Codex install routes, host-compatibility sections, or other-agent metadata in the ClawHub package.
- Do not remove the skill's usage instructions, bilingual explanation, scoring notes, or user-facing description copy just to make the ClawHub package shorter. Only remove or rewrite other-agent entry points from the ClawHub bundle.
- Avoid adding literal destructive-command rule lists to the bundled references or OpenClaw package when the same goal can be handled with lighter structural checks. This reduces unnecessary platform moderation risk.

## Sync And Publish

- Edit source files in `codex-skill/`, then run `python scripts\sync_bundle.py` to regenerate the OpenClaw bundle in `skill/`.
- Before publishing, verify that `skill/` contains only OpenClaw-facing metadata and routes, and that tests pass.
- Publish ClawHub from the generated `skill/` directory only:

```powershell
clawhub --no-input publish "E:\codex wprkspace\skill useful\skill-usefulness-audit\skill" --slug skill-usefulness-audit --name "skill-usefulness-audit" --version <version> --tags latest,audit,skills,openclaw --changelog "<short changelog>"
```

- After publishing, inspect the package and confirm the latest version, moderation status, and tags.
