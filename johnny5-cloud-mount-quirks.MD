---
name: johnny5-cloud-mount-quirks
description: Nextcloud-synced Johnny 5 repo has sandbox bash-mount sync defects; work in /tmp and let user do git
metadata: 
  node_type: memory
  type: reference
  originSessionId: 96ed427c-693a-499e-93b3-192875b51b0f
---

The Johnny 5 repo (`C:\Users\apsus\Nextcloud\Documents\VS Code\Johnny5\Johnny 5`, bash mount `/sessions/<id>/mnt/Johnny 5/`) is Nextcloud cloud-synced, and the sandbox bash view of it has defects:

- **Python can't import modules from the mounted dir** — the import machinery's directory-listing throws `OSError [Errno 22] Invalid argument` / `_fill_cache`. Workaround: author and run Python in `/tmp` and `cp` finished files to the repo. Read individual files directly works; reading params via `open()` an absolute mount path works.
- **Write-tool writes can land truncated on the bash mount** (cloud→sandbox sync lag); a file the Read tool shows complete may be cut off when bash reads it. Re-`cp` from `/tmp` gives complete files; verify with `md5sum`.
- **git writes are flaky from the sandbox** — `.git/index` can read as `unknown index entry format 0x76000000`, and stale `.git/index.lock` files can't be removed (`Operation not permitted`). The user's own machine git is healthy. Policy (Andrew, confirmed): the agent **may create/switch branches** as part of delivering work, but does **not** commit, push, merge, tag, or stash — hand those to Andrew with the exact commands. If a branch op fails in the sandbox, report it and hand off rather than forcing it.
- Deliver by `cp /tmp/... ` to the repo, then verify byte counts / md5; the cloud syncs up correctly even though the down-sync to bash is flaky.

See [[johnny5-phase02-locomotion]] [[sandbox-no-torch]].
