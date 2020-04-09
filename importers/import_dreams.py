import json
import re
from datetime import date

start_date = date(2016, 4, 12)
stat_name = "dreams"
source = "parsed from manual spreadsheet entry"

with open("import_dreams_data.txt", "r") as f:
    spreadsheet_data = f.readlines()

for line in spreadsheet_data:
    if not line.strip():
        continue
    cells = line.strip().split("\t")
    if cells[0] == "none":
        dream_data = {"dreams": []}
        continue
    if cells[0].startswith("1)"):
        dreams = [{"text": text} for text in filter(None, re.split(r" *\d+\) *", cells[0]))]
    elif cells[0].lower().startswith("{dream "):
        dreams = [{"text": text} for text in filter(None, re.split(r" *\{dream ?\d+\} *", cells[0], flags=re.I))]
    elif cells[0].lower().startswith("{1"):
        dreams = [{"text": text} for text in filter(None, re.split(r" *\{\d+\} *", cells[0]))]
    else:
        dreams = [{"text": cells[0]}]
    dream_data = {"dreams": dreams}
    if cells[1] != "not in use":
        if cells[1] == "unknown":
            dream_data["context"] = None
        else:
            dream_data["context"] = cells[1]
    if cells[2] != "not in use":
        if cells[1] == "unknown":
            dream_data["feeling"] = None
        else:
            dream_data["feeling"] = cells[2]
    if cells[3] not in ["not in use", "none"]:
        dream_data["disorientation"] = int(cells[3])
    if cells[4] not in ["not in use", "none"]:
        dream_data["lewdness"] = int(cells[4])
    print(json.dumps(dream_data, indent=2))
