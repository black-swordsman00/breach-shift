# GitHub contribution goal

The requested goal is **100 new contributions from 16 November 2026 onward**.
The existing contribution graph is not counted toward that target.

The development baseline is commit `515dd99` (65 commits in its history).
At that point `origin/main` contained 59 commits; the visual/gameplay work and
audio/pursuit work were awaiting integration through PRs #11 and #12.

Count meaningful new commits and pull requests. A push is a synchronization
operation and is not itself a contribution. Commits on a feature branch are
pending contributions until they reach the repository's default branch, subject
to GitHub's author/email and repository eligibility rules. GitHub can take up to
24 hours to update the graph. Merging without squashing preserves individual
commit history; never rewrite existing history just to change the counter.

Useful local progress checks:

```powershell
git rev-list --count 515dd99..HEAD
git log --oneline 515dd99..HEAD
git log --oneline origin/main..HEAD
```

The first number is newly authored commits in the current branch history. It
must not be presented as the number already credited on the GitHub profile.
Opening small, reviewable PRs accompanies real development milestones; empty
commits and duplicate PRs are not part of this workflow.

See GitHub's [contribution reference](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)
and [missing-contributions guide](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/troubleshooting-missing-contributions).
