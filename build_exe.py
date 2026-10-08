"""Build script for compiling Flash Automator into a standalone executable using PyInstaller."""
import subprocess
import sys
from pathlib import Path


def build():
    root = Path(__file__).parent.resolve()
    spec_path = root / "flash_automator.spec"

    print(f"Building Flash Automator with PyInstaller using spec: {spec_path}...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path),
    ]

    result = subprocess.run(cmd, cwd=str(root))
    if result.returncode == 0:
        print("\n✓ SUCCESS: Build completed! Output directory: dist/FlashAutomator")
    else:
        print(f"\n❌ Build failed with return code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
