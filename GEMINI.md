# KIRAHT AI — Workspace Agent Operating Rules (GEMINI.md)

## 🚨 MANDATORY RULE: ALWAYS GIT COMMIT & PUSH TO REMOTE

Whenever ANY code modification, bug fix, feature implementation, UI change, or project file update is performed:

1. **Verify Code Quality**:
   - Ensure syntax passes (`python -m py_compile`, `node -c static/js/hud.js`, etc.).
2. **Stage and Commit**:
   - Stage all modified files (`git add .`).
   - Create a clean conventional commit (`feat(...)`, `fix(...)`, `chore(...)`, `style(...)`).
3. **Mandatory Push**:
   - **ALWAYS execute `git push origin main`** immediately after committing.
   - Never leave uncommitted edits or unpushed local commits.
   - Verify that `git status` is clean and up to date with `origin/main`.
