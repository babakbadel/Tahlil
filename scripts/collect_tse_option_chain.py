"""Collect a live option chain using sm-sokout/tse-option.

Designed for CI. No fabricated values: unavailable fields remain null and
source/provenance are persisted with the snapshot.
"""
from __future__ import annotations
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

SYMBOL = os.getenv("OPTION_SYMBOL", "فملی")
OUT = Path(os.getenv("TSE_OPTION_OUT", "data/raw/tse_option_chain.json"))
REPO = "https://github.com/sm-sokout/tse-option.git"


def main():
    root = Path(".cache/tse-option-runtime")
    if not (root / ".git").exists():
        root.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", REPO, str(root)], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(root)], check=True)

    code = r'''import json, os
import tse_option as tso
symbol=os.environ["OPTION_SYMBOL"]
df=tso.option_chain(symbol=symbol, IV=True, leverage=True, P_BSM=True, sort="Maturity")
# Convert all values safely; never coerce missing values to fake numbers.
print(json.dumps({"columns": list(df.columns), "rows": df.where(df.notna(), None).to_dict(orient="records")}, ensure_ascii=False, default=str))
'''
    env = dict(os.environ)
    env["OPTION_SYMBOL"] = SYMBOL
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    snapshot = {
        "source": "sm-sokout/tse-option",
        "symbol": SYMBOL,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Collected {len(snapshot['rows'])} option rows for {SYMBOL}")

if __name__ == "__main__":
    main()
