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
