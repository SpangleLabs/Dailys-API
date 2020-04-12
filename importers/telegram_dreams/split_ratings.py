from data_source import DataSource

data_source = DataSource()


def wrap_text(text, length=200):
    return "\n".join([text[i:i+length] for i in range(0, len(text), length)])


for dream_night in data_source.get_entries_for_stat_over_range("dreams", "earliest", "latest"):
    if not dream_night["data"].get("disorientation"):
        continue
    if dream_night["data"]["disorientation"] == 1:
        pass
    else:
        print("----")
        print(f"Max rating: {dream_night['data']['disorientation']}")
        for dream_idx in range(len(dream_night["data"]["dreams"])):
            print(wrap_text(f"--Dream {dream_idx}: {dream_night['data']['dreams'][dream_idx]['text']}"))
        user_ratings = input("User ratings: ").split(",")
        print(user_ratings)
        if len(dream_night["data"]["dreams"]) != len(user_ratings):
            print("ABORT")
            break
        new_data = dream_night["data"]
        for dream_idx in range(len(new_data["dreams"])):
            new_data["dreams"][dream_idx]["disorientation"] = user_ratings[dream_idx]
        del new_data["disorientation"]
        data_source.update_entry_for_stat_on_date("dreams", dream_night["date"], new_data, dream_night["source"])
        print(new_data)
