
from __future__ import annotations

import csv
import io
import urllib.request
import zipfile
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
OUTPUT = Path(__file__).with_name("sms_spam_uci.csv")


def main() -> None:
    with urllib.request.urlopen(URL, timeout=30) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    rows = []
    for line in archive.read("SMSSpamCollection").decode("utf-8").splitlines():
        label, text = line.split("\t", 1)
        rows.append({"text": text, "label": 1 if label == "spam" else 0, "source": "UCI SMS Spam Collection"})
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "label", "source"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} real labeled messages to {OUTPUT}")


if __name__ == "__main__":
    main()
