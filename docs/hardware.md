# Hardware Guide

The hardware source is a KiCad project for the ESP32-S3 and nRF24L01+ USB-C developer dongle.

## Board Assets

Top view:

![PCB top view](assets/board/PCB-TOP.png)

Bottom view:

![PCB bottom view](assets/board/PCB-BOT.png)

## Paths

| Path | Purpose |
| --- | --- |
| `hardware/kicad/ESPxRF.kicad_pro` | KiCad project entry point. |
| `hardware/kicad/ESPxRF.kicad_sch` | Schematic source. |
| `hardware/kicad/ESPxRF.kicad_pcb` | PCB layout source. |
| `hardware/3d-models` | Bundled project-local 3D model assets. |
| `manufacturing/gerbers` | Current Gerber and drill export. |

## Opening In KiCad

Open:

```text
hardware/kicad/ESPxRF.kicad_pro
```

The KiCad project no longer depends on user-local absolute model paths. The ESP32-S3 model is referenced through the bundled `hardware/3d-models` directory, while standard passives use KiCad library models.

## Manufacturing Outputs

The current generated manufacturing files are in:

```text
manufacturing/gerbers
```

Before ordering boards for a public release:

- Re-run KiCad DRC/ERC in the KiCad version used for release.
- Inspect copper, solder mask, paste, silkscreen, edge cuts, and drills in a Gerber viewer.
- Confirm stackup, board thickness, copper weight, impedance expectations, and RF connector footprint requirements with the fab.
- Generate a fresh fab package from `hardware/kicad/ESPxRF.kicad_pcb` if the layout changes.

## Firmware Pin Alignment

The firmware pin map is kept in:

```text
Firmware/ESP32_RFLINK/include/Config.h
```

Any PCB routing change that affects the nRF24 SPI bus, CE/CSN, or LEDs must be reflected there before releasing firmware.
