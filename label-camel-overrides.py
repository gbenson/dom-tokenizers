from collections import defaultdict
from datasets import load_dataset

labels = [
    "UNCATEGORIZABLE",
    "BASE64_ENCODED_DATA",
]

tokens_by_label = defaultdict(set)
for row in load_dataset("csv", data_files="token-contexts.csv")["train"]:
    row = type("Row", (), row)
    kind = (int(row.not_base64) << 1) | int(row.is_base64)
    if kind == 2:
        continue
    tokens_by_label[labels[kind]].add(row.token)

for label, tokens in sorted(tokens_by_label.items()):
    print(f"    (Label.{label},")
    print(f"     (", end='"')
    print('", "'.join(sorted(tokens)), end='")),\n')
