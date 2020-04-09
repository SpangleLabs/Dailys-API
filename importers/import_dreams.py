import json
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
        print("Multi dream")  # TODO
        continue
    if cells[0].lower().startswith("{dream "):
        print("Multi dream 2")  # TODO
        continue
    dream_data = {
        "dreams": [
            {
                "text": cells[0]
            }
        ]
    }
    if cells[1] != "not in use":
        if cells[1] == "unknown":
            dream_data["dreams"][0]["context"] = None
        else:
            dream_data["dreams"][0]["context"] = cells[1]
    if cells[2] != "not in use":
        if cells[1] == "unknown":
            dream_data["dreams"][0]["feeling"] = None
        else:
            dream_data["dreams"][0]["feeling"] = cells[2]
    if cells[3] not in ["not in use", "none"]:
        dream_data["dreams"][0]["disorientation"] = int(cells[3])
    if cells[4] not in ["not in use", "none"]:
        dream_data["dreams"][0]["lewdness"] = int(cells[4])
    print(json.dumps(dream_data, indent=2))
