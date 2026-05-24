"""
build.py - Libracycle executable builder
Packages the app into a standalone executable using PyInstaller.
Run this on each target platform to produce that platform's binary.

Usage:
    python build.py              # auto-detects platform
    python build.py --onefile    # single .exe / binary (bigger but portable)
    python build.py --onedir     # folder with binary + DLLs (faster startup)
    python build.py --clean      # delete previous build artifacts first
"""

import subprocess
import sys
import shutil
import argparse
from pathlib import Path

APP_DIR  = Path(__file__).parent
DIST_DIR = APP_DIR / "dist"
BUILD_DIR = APP_DIR / "build"


def check_pyinstaller():
    try:
        import PyInstaller
        print(f"[build] PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("[build] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def check_pillow():
    # Pillow is optional (logo support). Warn if missing but don't block.
    try:
        import PIL
        print(f"[build] Pillow found — logo support included.")
    except ImportError:
        print("[build] Pillow not found. Logo support will be disabled in the build.")
        print("        Install with: pip install pillow")


def build(onefile: bool = False, clean: bool = False):
    if clean:
        for d in (DIST_DIR, BUILD_DIR):
            if d.exists():
                shutil.rmtree(d)
                print(f"[build] Cleaned {d}")

    check_pyinstaller()
    check_pillow()

    # Data files that must ship with the binary
    # Format: source_path:dest_folder_inside_bundle
    added_data = [
        f"{APP_DIR / 'modules'}:modules",
        f"{APP_DIR / 'data'}:data",
        f"{APP_DIR / 'lang'}:lang",
    ]

    # On Windows the separator in --add-data is ; not :
    if sys.platform == "win32":
        added_data = [d.replace(":", ";") for d in added_data]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name",     "Libracycle",
        "--icon",     str(APP_DIR / "icon.ico") if (APP_DIR / "icon.ico").exists() else "NONE",
        "--noconsole",          # no terminal window on Windows/macOS
        "--clean",
    ]

    for data in added_data:
        cmd += ["--add-data", data]

    # Hidden imports that PyInstaller's static analysis sometimes misses
    hidden = [
        "customtkinter",
        "matplotlib",
        "matplotlib.backends.backend_tkagg",
        "tkinter",
        "PIL",          # optional, but include it if present
        "json",
        "csv",
        "pathlib",
    ]
    for h in hidden:
        cmd += ["--hidden-import", h]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    cmd.append(str(APP_DIR / "main.py"))

    print(f"\n[build] Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=APP_DIR)

    if result.returncode == 0:
        print("\n[build] ✓ Build complete.")
        if onefile:
            binary = DIST_DIR / ("Libracycle.exe" if sys.platform == "win32" else "Libracycle")
            print(f"[build] Binary: {binary}")
        else:
            print(f"[build] Output folder: {DIST_DIR / 'Libracycle'}")
        _print_platform_notes(onefile)
    else:
        print("\n[build] ✗ Build failed. Check the output above.")
        sys.exit(1)


def _print_platform_notes(onefile: bool):
    print()
    if sys.platform == "win32":
        print("Windows notes:")
        print("  - Run Libracycle.exe directly or from the dist/Libracycle/ folder.")
        print("  - If antivirus flags it, add an exception — PyInstaller binaries trigger false positives.")
        if not onefile:
            print("  - Distribute the entire dist/Libracycle/ folder, not just the .exe.")

    elif sys.platform == "darwin":
        print("macOS notes:")
        print("  - You may need to right-click → Open the first time (Gatekeeper).")
        print("  - For distribution, consider: codesign --deep --force --sign - dist/Libracycle")

    else:
        print("Linux notes:")
        print("  - Make executable: chmod +x dist/Libracycle/Libracycle")
        print("  - tkinter must be installed on the target machine:")
        print("    Fedora/Nobara: sudo dnf install python3-tkinter")
        print("    Ubuntu/Debian: sudo apt install python3-tk")
        if onefile:
            print("  - --onefile bundles everything but is slower to start (extracts to /tmp on launch).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Libracycle executable")
    parser.add_argument("--onefile", action="store_true",
                        help="Pack everything into a single binary file")
    parser.add_argument("--onedir",  action="store_true",
                        help="Output a folder with binary + dependencies (default)")
    parser.add_argument("--clean",   action="store_true",
                        help="Remove previous build artifacts before building")
    args = parser.parse_args()

    # Default to onedir if neither flag given
    build(onefile=args.onefile, clean=args.clean)
