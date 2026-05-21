from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def zip_dir(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source))


def copy_if_exists(source: Path, target: Path) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Package Wireless Dev Bridge release assets")
    parser.add_argument("--output", required=True)
    parser.add_argument("--include-builds", action="store_true")
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    zip_dir(ROOT / "manufacturing" / "gerbers", output / "wireless-dev-bridge-v1-gerbers.zip")
    zip_dir(ROOT / "docs", output / "wireless-dev-bridge-docs.zip")
    zip_dir(ROOT / "hardware" / "kicad", output / "wireless-dev-bridge-kicad-source.zip")

    for path in ("README.md", "LICENSE", "CHANGELOG.md", "SECURITY.md", "SUPPORT.md"):
        copy_if_exists(ROOT / path, output / path)

    if args.include_builds:
        firmware_root = ROOT / "Firmware" / "ESP32_RFLINK" / ".pio" / "build"
        for env in ("node1", "node2"):
            copy_if_exists(firmware_root / env / "firmware.bin", output / f"firmware-{env}.bin")
            copy_if_exists(firmware_root / env / "firmware.elf", output / f"firmware-{env}.elf")
        sdk_dist = ROOT / "sdk" / "python" / "dist"
        if sdk_dist.exists():
            for artifact in sdk_dist.iterdir():
                if artifact.is_file():
                    copy_if_exists(artifact, output / artifact.name)

    print(f"Release assets written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
