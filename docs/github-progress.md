# GitHub contribution goal

The user requested more than 100 new contributions from 16 November 2026 onward.
Count real development, not empty commits, duplicate PRs or push operations.
The development baseline is `515dd99`.

The side-view migration has meaningful milestones: independent platform
simulation and ten maps; locally baked sprite art; the playable renderer,
controls and HUD; removal of the retired 3D implementation; and release checks.
Each milestone is separately reviewable and preserves history.

Useful progress checks:

```powershell
git rev-list --count 515dd99..HEAD
git log --oneline 515dd99..HEAD
git log --oneline origin/main..HEAD
```

History counts include merge commits. Feature-branch work is not a claim that
GitHub has already credited the profile graph. Commits must meet GitHub's
[contribution rules](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference),
including author identity and default-branch eligibility. Pushes synchronize
work and are not themselves profile contributions. Merge without squashing
when preserving separately useful commits; never rewrite history to inflate
counts.

The pinned pre-conversion revision used by the offline sprite baker remains
reachable in Git history. Git metadata is functional project data and is not
part of unused-file cleanup.