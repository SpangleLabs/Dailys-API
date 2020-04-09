from data_source import DataSource

migration_dict = {
    "spreadsheet": "parsed from manual spreadsheet entry"
}

data_source = DataSource()
for entry in data_source.get_entries_over_range("earliest", "latest"):
    if entry["source"] in migration_dict:
        data_source.update_entry_for_stat_on_date(
            entry["stat_name"],
            entry["date"],
            entry["data"],
            migration_dict[entry["source"]]
        )
