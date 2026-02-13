from collections import Counter, defaultdict
from fitparse import FitFile
import sys

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    print("Pouziti: python inspect_fit.py cesta_k_souboru.fit")
    sys.exit(1)

fit = FitFile(path)

type_counts = Counter()
fields_seen = defaultdict(Counter)

for msg in fit.get_messages():
    type_counts[msg.name] += 1
    for f in msg.fields:
        if f.name:
            fields_seen[msg.name][f.name] += 1

print("\nMESSAGE COUNTS:")
for k, v in type_counts.most_common():
    print(f"  {k:15s} {v}")

print("\nTOP FIELDS PER MESSAGE:")
for msg_name in type_counts:
    print(f"\n[{msg_name}] rows={type_counts[msg_name]}")
    for field_name, cnt in fields_seen[msg_name].most_common(20):
        print(f"  {field_name:25s} {cnt}")
