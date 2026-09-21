import os
import subprocess
import sys

def build():
    print("Mengompilasi aplikasi menjadi file executable Windows (.exe)...")

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--name=QwQ_Offline_AI",
        "--add-data=app/templates:app/templates",
        "--add-data=app/static:app/static",
        "run.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n[BERHASIL] Aplikasi tersusun di folder dist/QwQ_Offline_AI/")
    except Exception as e:
        print(f"\n[Gagal PyInstaller]: {e}")
        print("Pastikan pyinstaller sudah terinstall: pip install pyinstaller")

if __name__ == "__main__":
    build()
