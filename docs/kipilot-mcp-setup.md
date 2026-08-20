# KiPilot MCP Setup — KiCad 10.0.5 Live Control from Claude Desktop

Same integration pattern as the FreeCAD MCP: a local MCP server bridges Claude Desktop to a running KiCad session on `drewsdesktop`. Project: [belaszalontai/kipilot-mcp](https://github.com/belaszalontai/kipilot-mcp) — targets KiCad 10.x, documented for 10.0.1+, so it covers the installed 10.0.5.

**Status note:** early/experimental (v0.1.x on the KiCad forum as of this writing). Read-heavy operations are considered solid; write/mutation is present but should be treated as unproven until tested on a throwaway board.

**Why this doc exists instead of Claude doing the edit directly:** the Filesystem MCP bridge tool errored this session on every call (`invalid outputSchema... unsupported dialect`) — a connector-side bug, not a permissions issue. That tool is what a previous session used to edit `claude_desktop_config.json` directly for the FreeCAD MCP. Until it's working again, the config edit below is manual.

---

## 1. Download and extract

Get the latest Windows build from the [releases page](https://github.com/belaszalontai/kipilot-mcp/releases/latest) — asset name follows the pattern `kipilot-mcp-<version>-windows-x64.zip`. It bundles its own Python runtime, so no local Python install is required.

Extract to a stable, permanent location, e.g. `C:\Tools\kipilot-mcp\`. Don't extract into a temp folder or anywhere that might get cleaned up — the `.exe` path goes straight into Claude Desktop's config.

## 2. Enable KiCad's IPC API

The IPC API is disabled by default in KiCad 10. It's a per-install preference, not per-project:

1. Open KiCad 10.0.5 and the PCB Editor for a project.
2. Go to **Preferences** and look for a **Plugins** section with an "Enable KiCad API" (or similarly worded) checkbox.

I could not independently verify the exact menu wording from official KiCad docs — sources describe it inconsistently and the setting may have moved between 10.0.0 and 10.0.5. If it's not directly under Preferences → Plugins, search KiCad's Preferences dialog for "API." KiCad needs to stay running with a project open while KiPilot connects; it communicates over a local named pipe (Windows) that KiCad exposes once the API is enabled — no manual socket path or API token setup should be needed.

## 3. Add KiPilot to Claude Desktop's config

Real config path (this is an MSIX/Windows Store install, not the generic `%APPDATA%\Claude\` path — see the msix-config note if you need the background):

```
C:\Users\apsus\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
```

Easiest route: Claude Desktop → **Settings → Developer → Edit Config**. That opens the real file in your default text editor, which avoids the PowerShell BOM issue entirely.

Add this entry under the existing top-level `mcpServers` key (the FreeCAD entry should already be there — merge, don't replace the file):

```json
"kipilot-mcp": {
  "type": "stdio",
  "command": "C:\\Tools\\kipilot-mcp-<version>-windows-x64\\kipilot-mcp.exe",
  "env": {
    "KIPILOT_KICAD_CLIENT_NAME": "kipilot-mcp",
    "KIPILOT_KICAD_TIMEOUT_MS": "60000",
    "KIPILOT_LOG_LEVEL": "INFO",
    "KIPILOT_LOG_FILE": ".logs/kipilot-mcp.log"
  }
}
```

Replace `<version>` with the actual extracted folder name. Write access is off by default — KiPilot starts read-only. To allow it to move footprints, edit tracks, etc., add:

```json
"KIPILOT_ENABLE_MUTATIONS": "1"
```

to the `env` block once you've verified the read-only connection works and want to test edits (start on a throwaway board given the project's experimental status).

If you script the edit instead of using Edit Config, use no-BOM UTF-8 (`New-Object System.Text.UTF8Encoding($false)` in PowerShell) and back up the file first — a BOM-corrupted config breaks the whole app's settings load, not just MCP.

## 4. Restart and verify

Fully quit and reopen Claude Desktop (tray icon → Quit, not just closing the window — standard for picking up MCP config changes). In a chat, ask it to run the KiPilot tool `ping_kicad` to confirm the connection before attempting any board operations.

---

## Open items for next session

- Confirm exact KiCad 10.0.5 menu path for enabling the IPC API once you've found it — worth a one-line memory update so the next KiCad-MCP task doesn't re-derive it.
- Re-test the Filesystem MCP bridge; if it's working again, future config edits (this one or others) can be done directly from a Cowork session instead of handed off.
- Once `ping_kicad` succeeds, decide whether to flip on `KIPILOT_ENABLE_MUTATIONS` for actual PCB editing work, or keep KiPilot read-only for design review/inspection only.
