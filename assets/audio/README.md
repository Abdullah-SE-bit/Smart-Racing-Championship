# Original sound pack

All WAVs in this directory are synthesized for this project by
[`scripts/generate_audio_assets.py`](../../scripts/generate_audio_assets.py)
using only Python's standard library. There are no third-party samples or
external audio licenses. The pack includes menu ambience, three engine layers
(idle, revving, and boost, crossfaded from live player state), plus focus,
confirmation, screen transition, countdown, launch, nitro, checkpoint, warning,
and finish cues.

Regenerate the files with:

```powershell
py -3.12 scripts/generate_audio_assets.py
```
