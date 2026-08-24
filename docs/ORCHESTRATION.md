# Orchestration Protocol

How Johnny 5 sessions are dispatched, closed out and kept honest. Distilled 2026-08-23 from
`ORCHESTRATOR_PROMPT.md`, whose one-time bootstrap half is archived at
`docs/archive/ORCHESTRATOR_PROMPT_2026-08-22.md`. **This file carries no project state.**
State lives in `PROJECT_STATE.md`; if anything here ever states a fact about where the
project stands, that is a defect in this file.

---

## 1. The role

The orchestrator owns four answers at all times: where the project is, what is true, what
happens next, and what was decided and why. It does not build parts, write drivers, train
policies or edit CAD.

**The orchestrator is a role, not a session.** It is instantiated fresh from the repository
whenever it is needed and it stops when its turn is done. A long-lived orchestrator
accumulates beliefs that drift from the repository, which is the failure this whole
apparatus exists to prevent. An orchestrator turn is short: read, verify, then either emit
one dispatch brief or verify one close-out report and update state.

Every other session is a **worker**: dispatched with a bounded scope, does its work, returns
a close-out report. **A worker's report is a claim, never a fact.**

Two rules make the split work, and nothing else depends on continuity:

1. **No worker edits `PROJECT_STATE.md`.** A worker that believes it is wrong says so in its
   report.
2. **No worker writes its own successor's brief.** A session doing exactly that on 2026-08-21
   produced an initiating prompt for a phase that had closed two months earlier.

**Read path, in order:** `CLAUDE.md` → `PROJECT_STATE.md` → this file → the relevant phase
document. Nothing else is authoritative. A phase document's engineering detail is trusted;
any status claim in one is historical context, not authority.

**Authority to re-plan.** The orchestrator may split, merge, reorder or add phases and tasks;
redirect or terminate in-flight work; and propose branch, merge and history changes. Each is
a **proposal to Andrew with a recommendation attached**, then executed on approval. Never a
menu of options — recommend one and let him correct it.

---

## 2. Dispatch protocol

Every worker session begins with a brief the orchestrator writes. A brief that does not fit
on two screens is probably two sessions.

1. **Session ID and name.** `J5-S<nn> — <objective>`. Numbering is global, continuing the
   session ledger in `PROJECT_STATE.md` section 4.
2. **Read path.** As above, plus any named artifact. State explicitly that phase-document
   status claims are not authoritative.
3. **Branch.** Which branch, and whether to create it. Per `CLAUDE.md`'s naming scheme.
4. **Scope.** Concrete, and bounded to fit one context window with room to close cleanly.
5. **Out of scope.** Named explicitly — which files must not be touched, and whether this
   session holds the integration lock.
6. **Preconditions.** What must be true before starting, and what to do if one is not. The
   answer is always "stop and report", never "work around it".
7. **Definition of done.** Testable. For CAD, a build-time guard that passes. For code, a
   test. For a document, a specific claim a reader can check. "Looks right" is not one.
8. **Close-out requirements.** Section 3 of this file, verbatim.
9. **Session config.** Model, thinking and effort from `CLAUDE.md`'s per-phase table, with a
   reason if deviating.
10. **Standing constraints.** Section 5's hazards, trimmed to the ones this session will meet.

---

## 3. Close-out protocol

A worker's report contains: what it did, the commits or files it produced, the
definition-of-done evidence, decisions taken with rationale, open threads discovered, and
what it believes should happen next. It contains **no state updates**, because it does not
own state.

**The orchestrator verifies before it records:**

- Every claimed file exists on the claimed branch. `git show <branch>:<path>`, not `ls`.
- Every claimed commit exists and touches what the report says it touches.
- Every claimed test or guard was actually run, with output, not asserted.
- Every mass, dimension or timing figure traces to a script that produced it. Phase 00 quoted
  budget figures for two months from a script that had been crashing the whole time.
- Anything the report is silent about that you expected. **Silence is the most common form of
  bad news in this project.**

Only then update `PROJECT_STATE.md`, in one edit, and log the verification in its section 10.

If a report and the repository disagree, **the repository wins**, and say so to Andrew plainly
— not softened, and not dressed up as a process observation.

---

## 4. Concurrency: the integration lock

Work is mostly sequential, occasionally parallel. The rule that makes occasional parallelism
safe:

**Exactly one session at a time holds the integration lock.** The holder is the only session
permitted to touch canonical documents (`PROJECT_STATE.md`, `CLAUDE.md`, `docs/ORCHESTRATION.md`,
`phases/*.md`), shared parameter sources (`mechanical/freecad/params.csv`,
`mechanical/freecad/j5_params.py`, `src/shared/PROTOCOL.md`), and git history. The orchestrator
holds it by default and lends it deliberately, naming the loan in the dispatch brief and
recording it in `PROJECT_STATE.md`.

Any session running alongside the lock holder is **write-isolated**: its own branch, its own
files, no shared-parameter edits. It reports parameter changes it *wants* rather than making
them, and the orchestrator applies them at close-out.

Parallelism is worth it when the work is genuinely disjoint and one strand is long-running — a
training run against a documentation pass, a CAD build against a Pi-side driver. It is not
worth it for two sessions in the same subsystem, however tempting the wall-clock saving:
merging two sessions' judgement about the same geometry costs more than running them in series.

---

## 5. Git authority and mechanics

**Every git write is Andrew's.** Claude edits the working tree and verifies its own work, then
hands over an exact command block. Claude does not commit, push, merge, tag or stash. A fenced
block of git commands is always Andrew's to run; when Claude has done something itself it says
so and reports the SHA.

Commit authority was granted with prior approval on 2026-08-22, exercised once, and returned
on 2026-08-23. Two environment facts drove that, and both still hold:

- **The device mount cannot delete files.** Every git command that takes `.git/index.lock`
  strands it, and the stranded lock blocks the next git write — Andrew's included. `rm` and
  `mv` both fail from the agent side. Only Andrew can clear it, from Windows:
  `del ".git\index.lock"`, and likewise `HEAD.lock` and `objects\maintenance.lock`.
- **Line-ending handling differs between the two environments**, so a text file committed from
  the agent side can land with wrong line endings in an otherwise-LF repository. It has.

**Practical rules:**

- Prefer git commands that only read the object database: `log`, `show`, `cat-file`, `ls-tree`,
  `rev-parse`, `for-each-ref`, `ls-remote`, `check-ignore`, `fsck`. Avoid `status`, `diff`,
  `add` — they take the index lock. Use `git --no-optional-locks status` if status is genuinely
  needed.
- Run `find .git -maxdepth 2 -name "*.lock"` before handing over a command block, and say which
  locks need clearing first.
- Show the exact `git add` list and the message before any commit block, and show what will land.
- Verify line endings after any text commit: `git cat-file -p <ref>:<path> | tr -cd '\r' | wc -c`
  must be 0. `git diff --ignore-cr-at-eol` **hides** this defect — use it to read content
  changes, never to certify a commit.
- **Recovering a commit that failed on "cannot lock ref HEAD":** the commit object is already
  written and only the ref move failed. Find it with `git fsck --dangling`, match the subject,
  verify its tree, then `git update-ref refs/heads/<branch> <sha>` and `git reset` (mixed, no
  paths — **never `--hard`**).

---

## 6. Environment hazards

Carried forward because every session otherwise rediscovers them at cost.

- **FreeCAD MCP** (neka-nat addon) runs inside FreeCAD's GUI process on the Windows desktop,
  RPC on `127.0.0.1:9875` — it must live wherever the GUI does, not on the home-lab LXC. GUI
  dispatch jams intermittently: `list_documents` answers instantly while `execute_code` and
  `create_document` time out at 60 s. Sometimes it clears on its own; sometimes it is a sliver
  boolean grinding in OCC, which is the session's own fault and not the bridge's.
- **Only trust STL mtimes read from FreeCAD's own `os.listdir`.** A fresh `.FCStd` timestamp
  with stale STLs is a GUI save, never a build, because `main()` exports before it saves.
- **A document appearing in `list_documents` usually means it was left open**, not that it was
  just built.
- **The agent sandbox cannot install PyTorch.** All ML training runs on the home lab.
- **Verification belongs in the build, not in the parameters.** `validate.py` compared numbers
  to numbers and reported ALL CHECKS PASS while three defects reached the print bed. Boolean
  guards inside `main()` are what catch real defects. Require them in any CAD session's
  definition of done. Note an overlapping fuse is legal and still returns one solid, so the
  single-solid check cannot see two features claiming the same volume.
- **A tangency is invisible to a boolean.** Touching solids share zero volume, exactly like a
  5 mm gap. Proving contact needs a second probe grown slightly on radius that *must* intersect.
- **Python cannot import modules from the mounted repo directory** (`OSError [Errno 22]` in
  `_fill_cache`). Author and run Python in `/tmp` and copy results over, verifying by `md5sum`.
- **The agent's writes to the mount can land truncated.** Author in `/tmp`, copy over, verify
  by `md5sum` — for edits as well as new files.

---

## 7. Operating style

`CLAUDE.md`'s Token Discipline and Style sections apply in full. In particular: outline in two
or three sentences and wait before producing a multi-section document; one targeted question
with a recommendation rather than a list of options; no status narration; no restating the task
before doing it; direct tone; prose over bullets except where a table genuinely carries the
structure; en-dashes for ranges, no em-dashes.

One addition specific to the orchestrator: **report position, not activity.** Andrew does not
need to know that seven phase documents were read. He needs to know where the project is, what
is blocking it, and what is proposed about it. When there is nothing that changes his picture
of the project, say so in a line.

---

## 8. How this fails

The failure that created the role, stated so its shape is recognisable:

On 2026-08-21 a session finished its work, was asked to write the next session's initiating
prompt, opened `MEMORY.md`, read the index line "Phase 02 locomotion — Tasks 1–5 done, 6a/6b
remaining", **never opened the file behind it**, and wrote a Phase 01 initiating prompt for a
phase that had closed on 2026-06-22. It was caught only because Andrew ran it and the receiving
session pushed back.

Three conditions made it possible: an index was read in place of the document it summarises;
the document that had the right answer sat in no read path; and truth was per-branch.

**The countermeasures are not optional.** Read the file, never the index. Keep exactly one
authority and put it in every read path. Verify against the repository at the start of every
orchestrator turn and before every state update. Record the date and SHA of every verification
in `PROJECT_STATE.md` section 10, so the next reader can see how stale you are.

Two further instances from 2026-08-23, both the same shape:

- A commit was certified with `git diff --ignore-cr-at-eol`, the one flag that conceals
  line-ending defects, and a CRLF blob reached the repository as a result.
- A repository migration was recommended on a root cause that had never been tested and did not
  survive contact.

The pattern in all three is a confident claim built on a plausible correlation instead of a
check. **When a number or a cause appears in a report, ask which command produced it.**

Related: `mass_budget.py` crashed silently on a malformed CSV row for two months, and every mass
figure quoted in that window was produced by hand without anyone noticing.

---

## 9. `PROJECT_STATE.md` required structure

Repo root. Orchestrator-owned. Keep it under about 1,200 lines by moving closed material into
`docs/archive/` — a state document nobody finishes reading is the problem this exists to solve.

| § | Contents |
|---|---|
| 1 | **Position** — active phase and task, one-sentence status, gate condition verbatim, and the single thing that would close it |
| 2 | **Blockers** — what, who can clear it, what it blocks, since when. Physical-world blockers marked as such, because no session can clear them |
| 3 | **Phase ledger** — per phase: name, gate condition, state, date of change, and the commit or artifact evidencing it. "Met" with no evidence pointer is not met |
| 4 | **Session ledger** — every session dispatched: ID, date, phase, one-line scope, outcome, commits. Numbered globally, never per phase |
| 5 | **Dispatch queue** — what to dispatch next and why, in order, with preconditions. The section to read on a busy day |
| 6 | **Repository map** — trunk and its role, live branches, tags, and artifacts deliberately untracked with where they live instead |
| 7 | **Open items register** — carried non-blocking items with an owner and a phase they are due in |
| 8 | **Known weaknesses accepted** — what, why accepted, what would trigger revisiting |
| 9 | **Decision record** — most recent first: date, decision, rationale, session ID. **Never truncate**; archive by year or phase if it grows |
| 10 | **Verification log** — each reconciliation: date, what was checked, what was found wrong. This is how anyone judges how stale the file is |
