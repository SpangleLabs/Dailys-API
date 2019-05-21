import dateutil.parser


class Data:

    def __init__(self, json_data):
        self.date = dateutil.parser.parse(json_data['date'])
        self.source = json_data['source']
        self.stat_name = json_data['stat_name']


class SleepData(Data):

    def __init__(self, json_data):
        super().__init__(json_data)
        self.sleep_time = dateutil.parser.parse(json_data['data']['sleep_time'])
        self.wake_time = dateutil.parser.parse(json_data['data']['wake_time'])
        self.time_sleeping = self.wake_time - self.sleep_time
        self.interruptions = json_data['data'].get('interruptions')


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
