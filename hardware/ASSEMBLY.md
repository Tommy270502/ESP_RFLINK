# Assembly Notes

## Required Release Checks

- Confirm ESP32-S3 module orientation.
- Confirm USB-C connector alignment and shell grounding.
- Confirm nRF24L01+ SPI routing and CE/CSN pins match `Firmware/ESP32_RFLINK/include/Config.h`.
- Confirm LED polarity and silkscreen labels.
- Confirm antenna/RF keepout assumptions for the selected nRF24 implementation.
- Inspect first articles for solder bridges around USB-C and fine-pitch module pads.

## Bring-Up

1. Check USB enumeration.
2. Flash `node1`.
3. Run `wdb --serial <port> self-test`.
4. Run RF pair-test against a known-good dongle.
5. Save a support report with the board revision and lot identifier.
