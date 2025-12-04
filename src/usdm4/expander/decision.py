from usdm4.api.scheduled_instance import ScheduledDecisionInstance

class Decision():

    def __init__(self, sdi: ScheduledDecisionInstance):
        self._sdi: ScheduledDecisionInstance = sdi