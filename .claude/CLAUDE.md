mkdir -p .claude

cat > .claude/CLAUDE.md << 'EOF'
# Project Instructions

## Spec-Kit Structure
This project uses `.specify/` for all project definitions:

- `.specify/constitution/project-constitution.md` — core project rules, architecture, non-negotiables
- `.specify/features/` — one folder per feature, contains spec, plan, tasks, checklist
- `.specify/templates/` — templates for new features

## How to start every session
1. Read `.specify/constitution/project-constitution.md` first
2. Read all active feature folders in `.specify/features/`
3. Check each feature's `tasks.md` or `checklist.md` for current status
4. Confirm understanding before writing any code

## How to work on a feature
- Follow the spec in that feature's folder exactly
- Update `checklist.md` as tasks complete
- Never start a new feature without a spec file

## Code rules
- Follow architecture defined in constitution
- Commit after every completed task
- Keep changes small and focused
EOF