from .tui import *

class Plan:
    def __init__(self):
        self.tasks = []
        self.last_id = 0

    def __iter__(self):
        for task in self.tasks:
            yield task

    def is_empty(self):
        return len(self.tasks) == 0

    def add_task(self, task):
        self.last_id += 1
        self.tasks.append(task)
        task.id = self.last_id

    def apply(self):
        for task in self.tasks:
            if task.enabled:
                task.apply()

    def show(self):
        thead, tbody = self.show_tasks()
        tbody = list(map(lambda row: tuple(map(str, row)), tbody))
        print_plan(thead, tbody)
