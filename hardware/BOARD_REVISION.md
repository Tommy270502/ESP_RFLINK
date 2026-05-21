# Board Revision Notes

## V1

- ESP32-S3-WROOM-1 target.
- nRF24L01+ RF path.
- Native USB CDC serial.
- Firmware pin map is documented in `docs/firmware.md` and defined in `Firmware/ESP32_RFLINK/include/Config.h`.

Any PCB change that affects USB, power, nRF24 SPI, CE/CSN, IRQ, LEDs, or the RF path must update firmware config, board images, Gerber export, and release notes in the same release.
