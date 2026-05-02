# Cross-Agent Portability

Write skills so they work across Claude Code, Cursor, Codex, opencode, Pi Agent, and similar agents.

## Portable Practices

- Use plain Markdown instructions and relative paths inside each skill.
- Put deterministic behavior in scripts rather than relying on one agent’s tool dialect.
- Avoid OpenAI-, Anthropic-, or editor-specific metadata as a requirement for success.
- Keep installation and distribution notes at the package level, not inside individual skill folders.
- Describe validation commands in POSIX shell terms where possible, then mention platform-specific tools.

## Runtime Differences

| Environment | Guidance |
| --- | --- |
| Claude Code | Skills and skill-scoped agents can be copied as folders; avoid relying on external absolute paths. |
| Cursor | Keep scripts executable from a normal terminal; references should be human-readable. |
| Codex | Skills trigger from frontmatter description; scripts should tolerate sandboxed workspaces. |
| opencode | Prefer shell/Python scripts and no hidden connector assumptions. |
| Pi Agent | Keep artifacts and references compact; avoid requiring UI-specific affordances. |
