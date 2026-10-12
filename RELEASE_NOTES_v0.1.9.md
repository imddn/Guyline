# v0.1.9 — Skill Workflows and Provider Key Updates

Historical feature notes retained for reference. Current installation and
commands are documented for [Guyline 0.2.0](RELEASE_NOTES_v0.2.0.md).

## Highlights

- **Bundled skill creator**
  - Added a bundled `skill-creator` skill for creating, improving, and verifying Guyline/guyline agent skills.
  - This makes repeatable workflows easier to capture as first-class skills.

- **User-invocable skill slash commands**
  - Skills marked as user-invocable can now be triggered directly with slash commands.
  - Slash-invoked skills support user arguments and can request a model override through skill metadata.

- **Provider API key update fix**
  - `guyline setup` now lets users update the API key for an already-configured API-key provider profile.
  - `guyline provider edit <profile> --api-key <key>` can replace a saved profile key directly.
  - `guyline provider add ... --api-key <key>` can store a key while creating a provider profile.

## Fixes

- Fixed issue #238, where users could change a configured provider model but had no supported path to update the saved API key.

## Install

```bash
python -m pip install /path/to/guyline-0.2.0-py3-none-any.whl
```
