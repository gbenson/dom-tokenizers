import csv
import sys

from datasets import load_dataset

WINDOW = 72

with open("tokens-to-check.htmls") as fp:
    html = fp.read()

w = csv.writer(sys.stdout)
w.writerow(["is_base64", "lead_in", "token", "trail_out"])
details = load_dataset("csv", sep="\t", data_files="camel-details.tsv")
for row in details["train"]:
    if not row["is_flagged"]:
        continue
    token = row["token"]
    start = html.find(token)
    if start < 0:
        w.writerow((False, "", token, ""))
        print(f"{token}: not found", file=sys.stderr)
        continue
    limit = start + len(token)
    start = max(start - WINDOW // 2, 0)
    limit = min(limit + WINDOW // 2, len(html))
    window = html[start:limit].replace("\n", " ")
    start = window.find(token)
    assert start >= 0
    limit = start + len(token)
    wstart = (start + limit - WINDOW) // 2
    wlimit = wstart + WINDOW
    w.writerow((
        False,
        window[wstart:start].lstrip("="),
        window[start:limit],
        window[limit:wlimit],
    ))
