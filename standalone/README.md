# Independent standalone source

This directory is the only active source for the standalone companion slice.

Current implemented scope:

- Stable player-bound companion UUID in player ModData.
- Asset identity field reserved for the actual DeepSeek whale-girl presentation.
- Local intent values (`follow`, `hold`, `retreat`) with persistence.
- No Knox, ZombieBuddy, full-screen overlay, ordinary mouse hook, or mandatory text input.

Current limitation:

This is an identity/state slice, not a playable teammate. No world actor is created yet, so the context-menu file is intentionally inert. The next gate is an independently owned B42 actor feasibility probe; only after that succeeds will commands become active.
