# GitHub contribution goal

The requested goal is **more than 100 new contributions from 16 November 2026 onward**.
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

The first number counts new entries in the branch history, including merges. It
must not be presented as the number already credited on the GitHub profile.
Opening small, reviewable PRs accompanies real development milestones; empty
commits and duplicate PRs are not part of this workflow.

See GitHub's [contribution reference](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)
and [missing-contributions guide](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/troubleshooting-missing-contributions).

## Production courtyard milestone

The `feat/production-assets` pass adds seven meaningful commits: obsolete-art
cleanup, licensed Poly Pizza props, Poly Haven architecture, Panda3D GLB/HDRI
integration, UV-preserving Rodin weapon optimization, Blender privacy checks,
and the documented visual handoff. Each milestone is pushed separately.

At the courtyard-only handoff (`c343368`), the branch contained **53 history entries since the baseline**,
with **7 commits ahead of its default-branch baseline**. Those pending
commits are not a claim that GitHub has credited 53 profile contributions.
No empty commits, duplicate PRs or rewritten history are used to reach the goal.

The initial validation included 164 game/asset tests, real Blender and Panda3D previews, a
standalone wheel smoke check, and a privacy scan of both new source artifacts
and all packaged content. The Rodin optimizer is checked with a synthetic UV
fixture; no generated weapon was included in that initial courtyard-only handoff.

## Rodin follow-up

The same PR now adds the first generated rifle and Walker, source-preserving
optimization and baking, local skeletal binding, measured muzzle placement,
correct first-person depth, mixed-library packaging and regression tests.
These are development milestones; new pushes remain synchronization operations.
Use the commands above for the current branch count rather than treating the
earlier snapshot or pending commits as a credited contribution graph total.
The follow-up passes 169 tests, including real rendered weapon occlusion and
independent skinned-vertex deformation, plus the mixed-library export and wheel checks.

## Supplied Warden and motion milestone

Six meaningful follow-up commits cover export/privacy fixes, the supplied boss
and ten skinned character assets, crouching/map practice, motion/reload/HUD,
courtyard refinements, and the verified visual handoff. This brings the branch
to **65 history entries since the baseline**, including merges, with **19 pending
commits ahead of its default-branch baseline**. These are history counts rather
than credited profile-contribution totals. PR #16 remains a draft for review.

Validation now passes 184 tests, full character skin deformation, packed-scene
checks, and a rendered installed-game check outside the source checkout. The
follow-up reuses supplied and existing local assets without new cloud generation.
