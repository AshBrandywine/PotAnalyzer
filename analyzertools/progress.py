import time
from datetime import timedelta


class ProgressTracker:
    update_interval = 0.50
    buffer_time_length = 20.0
    timestamp_buffer = []
    total_items = 0
    completed_items = 0
    last_update_time = None
    completed_at_last_update = 0
    percent_completed = 0.0
    time_left = ''

    def __init__(self, total_items):
        self.total_items = total_items
        self.last_update_time = time.time()

    def update(self, completed_items):
        self.completed_items = completed_items
        self.percent_completed = (float(self.completed_items) / float(self.total_items)) * 100
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.__add_data_point__(current_time)

    def __add_data_point__(self, current_time):
        elapsed_time = current_time - self.last_update_time
        completed_since_last_update = self.completed_items - self.completed_at_last_update
        completion_rate = completed_since_last_update / elapsed_time
        self.completed_at_last_update = self.completed_items
        self.last_update_time = current_time
        if completion_rate > 0:
            self.timestamp_buffer.append((current_time, completion_rate))
        self.__trim_buffer__(current_time)
        if len(self.timestamp_buffer) > 0:
            average_rate = self.__get_buffer_average__()
            remaining_items = self.total_items - self.completed_items
            seconds_left = round(float(remaining_items) / float(average_rate))
            self.time_left = str(timedelta(seconds=seconds_left))
        else:
            self.time_left = ''

    def __trim_buffer__(self, current_time):
        while len(self.timestamp_buffer) > 0:
            data_point = self.timestamp_buffer[0]
            if current_time - data_point[0] > self.buffer_time_length:
                self.timestamp_buffer.pop(0)
            else:
                break

    def __get_buffer_average__(self):
        rate_sum = 0.0
        for data_point in self.timestamp_buffer:
            rate_sum += data_point[1]
        return rate_sum / len(self.timestamp_buffer)

    def __str__(self):
        if len(self.time_left) == 0:
            return "%d/%d (%.2f%%)" % (self.completed_items, self.total_items, self.percent_completed)
        else:
            return "%d/%d (%.2f%%) Estimated time remaining: %s" % (self.completed_items, self.total_items,
                                                                    self.percent_completed, self.time_left)

