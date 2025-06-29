import uuid
import random
from datetime import datetime, timedelta
from tqdm import tqdm

ROWS = 10_000_000
OUTFILE = "logs.csv"
SEVERITIES = ["INFO", "WARNING", "ERROR", "CRITICAL"]

def random_date():
    return (datetime.utcnow() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")

with open(OUTFILE, "w") as f:
    for _ in tqdm(range(ROWS), desc="Generating"):
        row = ",".join([
            str(uuid.uuid4()),
            "abc",
            str(random.randint(0, 999)),
            "login",
            "user",
            str(uuid.uuid4()),
            random_date(),
            f"192.168.1.{random.randint(0, 255)}",
            "Mozilla/5.0",
            "", "", "",  # before, after, metadata
            random.choice(SEVERITIES)
        ])
        f.write(row + "\n")

print(f"✅ Done: {ROWS} rows written to {OUTFILE}")
