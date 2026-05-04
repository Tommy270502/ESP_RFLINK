from wireless_dev_bridge import WirelessDevBridge


def main() -> None:
    dev = WirelessDevBridge.http("192.168.4.1")
    print(dev.status())
    print(dev.rf_send_hex("1234", require_ack=True))


if __name__ == "__main__":
    main()
