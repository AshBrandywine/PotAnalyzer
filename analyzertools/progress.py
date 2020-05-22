import time
from datetime import timedelta


class ProgressTracker:
    total_items = 0
    completed_items = 0
    last_update_time = None
    completed_at_last_update = 0
    completion_rate = 0
    percent_completed = 0.0
    time_left = ''

    def __init__(self, total_items):
        self.total_items = total_items

    def update_completed_items(self, completed_items):
        self.completed_items = completed_items
        self.percent_completed = (float(self.completed_items) / float(self.total_items)) * 100

    def update_estimation(self):
        if self.last_update_time is None:
            self.last_update_time = time.time()
        else:
            completed_since_last_update = self.completed_at_last_update - self.completed_items
            current_time = time.time()
            elapsed_time = current_time - self.last_update_time
            self.completion_rate = completed_since_last_update / elapsed_time
            self.completed_at_last_update = self.completed_items
            self.last_update_time = current_time
            if self.completion_rate > 0:
                remaining_items = self.total_items - self.completed_items
                seconds_left = round(float(remaining_items) / float(self.completion_rate))
                self.time_left = str(timedelta(seconds=seconds_left))
            else:
                self.time_left = ''

    def __str__(self):
        if len(self.time_left) == 0:
            return "%d/%d (%.2f%%)" % (self.completed_items, self.total_items, self.percent_completed)
        else:
            return "%d/%d (%.2f%%) Estimated time remaining: %s" % (self.completed_items, self.total_items,
                                                                    self.percent_completed, self.time_left)

