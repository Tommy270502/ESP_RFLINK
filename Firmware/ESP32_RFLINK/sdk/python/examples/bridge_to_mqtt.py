"""Publish RF packet events from a dongle to MQTT.

Requires paho-mqtt:
  python -m pip install -e ".[mqtt]"

Examples:
  python examples/bridge_to_mqtt.py --ws 192.168.4.1 --broker localhost
  python examples/bridge_to_mqtt.py --ble WirelessDev-Node1 --topic-prefix lab/bridge1
"""

from __future__ import annotations

import argparse
import json

from example_common import (
    BridgeError,
    add_transport_args,
    connect_bridge,
    enable_rf_event_bridge,
    fail_with_bridge_error,
    print_error,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Forward RF packet events to MQTT")
    add_transport_args(parser, include_http=False, default_transport="ws")
    parser.add_argument("--broker", default="localhost", help="MQTT broker hostname or IP")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--client-id", default="wireless-dev-bridge", help="MQTT client ID")
    parser.add_argument("--topic-prefix", default="wireless-dev-bridge", help="MQTT topic prefix")
    parser.add_argument("--count", type=int, default=0, help="number of packets to publish, 0 means forever")
    parser.add_argument("--event-timeout", type=float, default=10.0, help="event read timeout in seconds")
    parser.add_argument("--no-listen", action="store_true", help="do not send rf_start_listen first")
    return parser


def make_mqtt_client(mqtt_module, client_id: str):
    try:
        return mqtt_module.Client(mqtt_module.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        return mqtt_module.Client(client_id=client_id)


def main() -> int:
    args = build_parser().parse_args()

    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print_error('bridge_to_mqtt.py requires paho-mqtt. Install with: python -m pip install -e ".[mqtt]"')
        return 1

    dev = None
    mqtt_client = None

    try:
        mqtt_client = make_mqtt_client(mqtt, args.client_id)
        mqtt_client.connect(args.broker, args.port)
        mqtt_client.loop_start()

        dev, transport, _target = connect_bridge(args)
        enable_rf_event_bridge(dev, transport)
        if not args.no_listen:
            dev.rf_start_listen()

        published = 0
        topic = f"{args.topic_prefix.rstrip('/')}/rf/packet"
        while args.count == 0 or published < args.count:
            event = dev.read_event(timeout=args.event_timeout)
            if event.get("type") != "packet":
                continue

            payload = json.dumps(event, separators=(",", ":"), sort_keys=True)
            mqtt_client.publish(topic, payload)
            print(f"published {topic} {payload}")
            published += 1
        return 0
    except BridgeError as exc:
        return fail_with_bridge_error(exc)
    except OSError as exc:
        print_error(f"MQTT connection failed: {exc}")
        return 1
    except KeyboardInterrupt:
        return 130
    finally:
        if dev is not None:
            dev.close()
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
