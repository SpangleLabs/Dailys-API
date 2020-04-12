from collections import defaultdict

from data_source import DataSource

data_source = DataSource()

base_keys = defaultdict(lambda: [])
dream_keys = defaultdict(lambda: [])
for dream_night in data_source.get_entries_for_stat_over_range("dreams", "earliest", "latest"):
    for key in dream_night["data"].keys():
        if key == "dreams":
            continue
        base_keys[key].append(dream_night["date"].date())
    for dream in dream_night["data"]["dreams"]:
        for key in dream.keys():
            dream_keys[key].append(dream_night["date"].date())

print(base_keys)
for key, val in base_keys.items():
    print(f"{key}: {len(val)}")
print(dream_keys)
for key, val in dream_keys.items():
    print(f"{key}: {len(val)}")
