# Bill Of Materials

The current repository tracks KiCad source and manufacturing outputs, but does not yet include a normalized purchasing BOM.

Before a public hardware release, export and review:

- Manufacturer part number and distributor SKU for every fitted component.
- Quantity per board.
- Reference designators.
- Approved alternates for passives, USB-C connector, ESP32-S3 module, nRF24L01+ path components, and LEDs.
- Do-not-populate parts, if any.
- Assembly notes for orientation-sensitive components.

Keep the generated BOM as a release artifact or add a reviewed CSV in this directory once component sourcing is locked.
