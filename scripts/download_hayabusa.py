#!/usr/bin/env python3
"""Download the latest Hayabusa release for this platform into ./hayabusa/."""

import json
import platform
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO = "Yamato-Security/hayabusa"
TARGET_DIR = Path(__file__).resolve().parent.parent / "hayabusa"


def platform_suffix() -> str:
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Windows":
        if machine in ("arm64", "aarch64"):
            return "win-aarch64"
        if machine in ("amd64", "x86_64"):
            return "win-x64"
        return "win-x86"
    if system == "Linux":
        if machine in ("aarch64", "arm64"):
            return "lin-aarch64-gnu"
        return "lin-x64-gnu"
    if system == "Darwin":
        if machine in ("arm64", "aarch64"):
            return "mac-aarch64"
        return "mac-x64"

    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def fetch_latest_release() -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases/latest",
        headers={"User-Agent": "mcp-hayabusa-downloader"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def find_asset(release: dict, suffix: str) -> dict:
    candidates = [
        a
        for a in release["assets"]
        if a["name"].endswith(f"-{suffix}.zip")
        and "live-response" not in a["name"]
    ]
    if not candidates:
        available = ", ".join(a["name"] for a in release["assets"])
        raise RuntimeError(
            f"No asset found for platform suffix '{suffix}'. Available: {available}"
        )
    return candidates[0]


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "mcp-hayabusa-downloader"})
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def extract(zip_path: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(target)

    # Some release zips wrap their contents in a single top-level directory;
    # flatten that into target so binaries land directly in ./hayabusa/.
    entries = list(target.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        wrapper = entries[0]
        for item in wrapper.iterdir():
            shutil.move(str(item), str(target / item.name))
        wrapper.rmdir()


def normalize_binary_name(target: Path) -> Path:
    """Rename the versioned Hayabusa binary to a stable hayabusa(.exe) name."""
    is_windows = platform.system() == "Windows"
    final_name = "hayabusa.exe" if is_windows else "hayabusa"
    final_path = target / final_name

    for item in target.iterdir():
        if not item.is_file() or not item.name.lower().startswith("hayabusa-"):
            continue
        if is_windows and item.suffix.lower() != ".exe":
            continue
        if not is_windows and item.suffix:
            continue

        if not is_windows:
            item.chmod(item.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        item.replace(final_path)
        return final_path

    raise RuntimeError(f"Could not find the Hayabusa binary to rename in {target}")


def main() -> None:
    suffix = platform_suffix()
    print(f"Detected platform: {suffix}")

    release = fetch_latest_release()
    version = release["tag_name"]
    asset = find_asset(release, suffix)
    print(f"Latest release: {version} ({asset['name']}, {asset['size']} bytes)")

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / asset["name"]
        print("Downloading...")
        download(asset["browser_download_url"], zip_path)

        print(f"Extracting to {TARGET_DIR}...")
        extract(zip_path, TARGET_DIR)

    binary_path = normalize_binary_name(TARGET_DIR)
    print(f"Done. Hayabusa {version} is at {binary_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
