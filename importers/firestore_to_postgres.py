import json

from data_source import FirestoreDataSource, PostgresDataSource

old_datasource = FirestoreDataSource()
with open("../config.json", "r") as f:
    config = json.load(f)
new_datasource = PostgresDataSource(config["database"])

for stat_name in old_datasource.get_unique_stat_names():
    entries = old_datasource.get_entries_for_stat(stat_name)
    for entry in entries:
        new_datasource.update_entry_for_stat_on_date(stat_name, entry["date"], entry["data"], entry["source"])
        print(f"Saved {stat_name} for {entry['date']}")
