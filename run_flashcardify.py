#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_flashcardify.py — tiny helper to run the pipeline.
"""

import os
import shlex
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

def main():
    pdf = input("Path to PDF book: ").strip().strip('"')
    out = input("Output CSV path [flashcards.csv]: ").strip() or "flashcards.csv"
    use_g = input("Use Gemini for MCQs? (y/N): ").strip().lower().startswith("y")

    # check template packs
    tpl = HERE / "templates"
    packs = ["fb_templates.json", "cloze_templates.json", "cloze_input_templates.json"]
    missing = [p for p in packs if not (tpl / p).exists()]
    if missing:
        print("[!] Missing template packs in ./templates/:", ", ".join(missing))
        print("    Please create them from the JSON in the instructions.")
        return

    cmd = f'python {shlex.quote(str(HERE/"flashcardify_book.py"))} -i {shlex.quote(pdf)} -o {shlex.quote(out)} --templates {shlex.quote(str(tpl))}'
    if use_g:
        if not os.getenv("GEMINI_API_KEY"):
            print("[!] GEMINI_API_KEY not set; Gemini will be skipped.")
        else:
            cmd += " --use-gemini"
    print("\nRunning:\n ", cmd)
    subprocess.run(cmd, shell=True, check=False)

if __name__ == "__main__":
    main()
