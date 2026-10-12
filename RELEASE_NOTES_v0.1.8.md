# v0.1.8 — Providers, guyline agent Feishu Groups, and Safer Remotes

Historical feature notes retained for reference. Current installation and
commands are documented for [Guyline 0.2.0](RELEASE_NOTES_v0.2.0.md).

## Highlights

- **New provider workflows**
  - Added NVIDIA NIM as a built-in OpenAI-compatible provider using `NVIDIA_API_KEY`.
  - Added ModelScope Inference API support.
  - Added Qwen (DashScope), MiniMax, and Gemini provider profiles.
  - Improved OpenAI-compatible API behavior, including explicit bearer authorization headers and `<think>` block filtering for compatible streaming responses.

- **guyline agent Feishu group support**
  - Added Feishu managed group creation flow for guyline agent.
  - Added gateway-scoped provider/model commands for chat-based operation.
  - Improved group routing and mention policy so guyline agent responds in shared Feishu groups only when explicitly addressed.
  - Hardened Feishu attachment filename handling.

- **Security and remote-channel hardening**
  - Kept sensitive config/auth/provider/model/ship commands local-only by default in remote channels.
  - Kept bridge commands local-only by default.
  - Added coverage for bridge spawn blocking and remote gateway security behavior.
  - Rejected path traversal names during plugin uninstall.

- **Windows and shell reliability**
  - Fixed Windows agent/subagent spawning by direct-executing teammate argv instead of shell-wrapping Python paths.
  - Windows shell resolution now skips discovered `bash.exe` binaries that cannot actually run commands, falling back to PowerShell/cmd.
  - Improved Windows gateway process lifecycle handling.
  - Avoided shell execution when opening browsers on Windows.

- **MCP, tools, and stability**
  - MCP startup now isolates failed servers instead of aborting the whole Guyline startup.
  - Fixed subprocess stderr pipe deadlocks in grep/glob/bash/session runner paths.
  - Bounded large tool results in conversation history and improved compaction under large/vision contexts.
  - Improved skill frontmatter parsing with YAML `safe_load` for bundled and user skills.

- **TUI and UX fixes**
  - Restored raw `DEL` backspace handling for macOS Terminal-style environments.
  - Added better slash-command completion, markdown table rendering, spinner behavior, and escape interruption.
  - Added image-to-text fallback support for text-only models and `--vision-model` override.


## Install

```bash
python -m pip install /path/to/guyline-0.2.0-py3-none-any.whl
```

Or run the installer from the repository docs.
