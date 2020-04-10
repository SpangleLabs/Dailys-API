from datetime import date

from data_source import DataSource

STAT_NAME = "dreams"
SOURCE = "Parsed from telegram channel"

data_source = DataSource()

last_date = date(2020, 4, 5)
for entry in data_source.get_entries_for_stat(STAT_NAME)[::-1]:
    if entry["source"] != SOURCE:
        continue
    entry_data = entry["data"]
    print(str(entry["date"]) + " = " + str(entry_data))
    print(str(entry["date"]) + " -> " + str(last_date))
    # if True:
    #     data_source.update_entry_for_stat_on_date(STAT_NAME, last_date, entry_data, SOURCE)
    #     docs = data_source.get_documents_for_stat_on_date(STAT_NAME, entry["date"])
    #     if len(docs) != 1:
    #         print("ARGH")
    #     else:
    #         docs[0].reference.delete()

    print("---")
    last_date = entry["date"].date()
