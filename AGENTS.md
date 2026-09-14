# AGENTS.md

This repository should use the following shortcut workflow for non-technical users who want the result of saving and publishing work without managing Git manually:

When the user asks for a push, sync, save, commit, or upload, use the one-command repository workflow below:

```powershell
$env:Path += ';C:\Program Files\Git\cmd;C:\Program Files\Git\bin'; git add .; git commit -m "Update from workspace"; git push origin main
```

Rules:
- Prefer the repository's default branch `main`.
- If `git` is not found, first add the Git install path shown above to `PATH`.
- Keep the commit message short and useful.
- Do not create extra scripts. Keep the workflow simple.
- If a file is already staged, use the same command pattern.
