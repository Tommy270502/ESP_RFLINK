# Manufacturing

This directory contains the current V1 board manufacturing export.

## Gerbers

Gerber and drill files live in:

```text
manufacturing/gerbers
```

The KiCad project is configured to export new Gerbers to this folder from:

```text
hardware/kicad/ESPxRF.kicad_pcb
```

## Release Package

Create a fab upload package from the repository root:

```bash
cd manufacturing/gerbers
zip -r ../wireless-dev-bridge-v1-gerbers.zip .
```

Do not commit generated ZIP archives. Attach them to tagged releases instead.

## Status

- **Verified**: Gerber and drill files exist in `manufacturing/gerbers` and correspond to the current KiCad PCB layout.
- **Open**: Fab order from these outputs has not been confirmed. DRC/ERC review should be repeated before production ordering.
