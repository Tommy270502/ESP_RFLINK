# Contributing

This repository contains firmware, local web workbench, SDK, hardware, manufacturing outputs, and documentation. Keep changes scoped to the layer you are modifying and update the matching documentation when behavior changes.

## Development Checks

Firmware:

```bash
cd Firmware/ESP32_RFLINK
pio run -e node1 -e node2
```

Python SDK:

```bash
cd sdk/python
python -m pip install -e ".[test]"
python -m pytest
```

Local web workbench:

```bash
python -m py_compile application/main.py
python application/main.py
```

## Repository Hygiene

- Do not commit PlatformIO build output, Python caches, egg-info, KiCad lock files, local project state, or generated ZIP archives.
- Do not commit user-local absolute paths in KiCad, Python, or documentation files.
- Keep public docs accurate when command behavior, transport support, pin mapping, or hardware outputs change.
- Publish generated release archives as release assets instead of tracking them in git.
