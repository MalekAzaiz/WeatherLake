import subprocess
import sys
import os

# Force le working directory à la racine du projet
os.chdir(os.path.dirname(os.path.abspath(__file__)))

scripts = [
    "ingestion/fetch_and_upload.py",
    "processing/raw_to_silver.py",
    "processing/silver_to_gold.py",
]

for script in scripts:
    print(f"\n▶️ Running {script}...")
    subprocess.run([sys.executable, script], check=True, env={**os.environ, "PYTHONPATH": os.getcwd()})

print("\n✅ Pipeline complete.")