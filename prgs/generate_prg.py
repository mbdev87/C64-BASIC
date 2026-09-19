#!/usr/bin/env python3

import os
import re
import subprocess
import sys
from pathlib import Path

BASIC_LINE_RE = re.compile(r"^\d+")
SCRIPT_DIR = Path(__file__).resolve().parent
PARENT_DIR = SCRIPT_DIR.parent


def find_executable(name):
    if sys.platform == "win32":
        candidates = [f"{name}.exe", f"{name}.bat", f"{name}.cmd"]
    else:
        candidates = [name]

    paths = os.environ.get("PATH", "").split(os.pathsep)
    if sys.platform == "win32":
        program_files = os.environ.get("PROGRAMFILES", "")
        if program_files:
            paths.insert(0, os.path.join(program_files, "VICE", "x64sc"))

    for dir_path in paths:
        for candidate in candidates:
            full_path = os.path.join(dir_path, candidate)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
    return name


def sanitize_filename(name):
    name = name.replace(" ", "_")
    for char in ["-", "'", "(", ")", "/", "\\"]:
        name = name.replace(char, "")
    name = os.path.splitext(name)[0]
    return name.lower()


def is_basic_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if BASIC_LINE_RE.match(line.strip()):
                    return True
    except Exception:
        pass
    return False


def generate_prg(source_path, output_dir):
    prg_name = sanitize_filename(source_path.name) + ".prg"
    output_path = output_dir / prg_name

    if output_path.exists():
        print(f"  Skipping (exists): {output_path.relative_to(SCRIPT_DIR)}")
        return None

    petcat = find_executable("petcat")

    try:
        cmd = [petcat, "-w2", "-o", str(output_path), str(source_path)]
        subprocess.run(cmd, check=True)
        print(f"  Generated: {output_path.relative_to(SCRIPT_DIR)}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"  Error: {source_path.name} - {e}")
        return None
    except FileNotFoundError:
        print(f"  Error: petcat not found in PATH")
        sys.exit(1)


def run_prg(prg_file):
    x64sc = find_executable("x64sc")
    print(f"\nRunning: {prg_file.name}")

    try:
        cmd = [x64sc, "-autostart", str(prg_file)]
        subprocess.run(cmd)
    except FileNotFoundError:
        print("Note: x64sc not found, skipping emulation")


def main():
    if not PARENT_DIR.exists():
        print(f"Error: Parent directory not found: {PARENT_DIR}")
        sys.exit(1)

    txt_files = sorted(PARENT_DIR.rglob("*.txt"))
    basic_files = [f for f in txt_files if is_basic_file(f)]

    if not basic_files:
        print("No BASIC .txt files found in parent directory.")
        sys.exit(0)

    print(f"Found {len(basic_files)} BASIC file(s)")
    print(f"Output directory: {SCRIPT_DIR.relative_to(PARENT_DIR)}\n")

    generated = []
    for source in basic_files:
        rel_path = source.relative_to(PARENT_DIR)
        rel_dir = rel_path.parent
        output_subdir = SCRIPT_DIR / rel_dir
        output_subdir.mkdir(parents=True, exist_ok=True)

        print(f"Processing: {rel_path}")
        result = generate_prg(source, output_subdir)
        if result:
            generated.append(result)

    print(f"\nDone. Generated {len(generated)}/{len(basic_files)} PRG file(s).")

    run_emulator = "--run" in sys.argv
    if run_emulator and generated:
        run_prg(generated[-1])


if __name__ == "__main__":
    main()
