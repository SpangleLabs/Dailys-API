from dailys_models.models import Data


class FuraffinityData(Data):

    def __init__(self, json_data):
        super().__init__(json_data)
        self.submissions = json_data['data'].get('submissions')
        self.comments = json_data['data'].get('comments')
        self.journals = json_data['data'].get('journals')
        self.notes = json_data['data'].get('notes')
        self.watches = json_data['data'].get('watches')
        self.favourites = json_data['data'].get('favourites')
        self.total = json_data['data'].get(
            "total",
            sum(filter(None,
                       [self.submissions, self.comments, self.journals, self.notes, self.watches, self.favourites]))
        )
