import logging

from .tui import *

# Configuration
DEFAULT_UI_BACKEND = 'tui'

class Plan:
    def __init__(self):
        self.tasks = []
        self.last_id = 0

    def __iter__(self):
        for task in self.tasks:
            yield task

    def __len__(self):
        return len(self.tasks)

    def __getitem__(self, index):
        return self.tasks[index]

    def is_empty(self):
        return len(self.tasks) == 0

    def add_task(self, task):
        self.last_id += 1
        self.tasks.append(task)
        task.id = self.last_id

    def optimize(self):
        logging.debug('This plan does not support optimizations')

    def apply(self):
        for task in self.tasks:
            if task.enabled:
                task.apply()

    def show(self):
        thead, tbody = self.show_tasks()
        tbody = list(map(lambda row: tuple(map(str, row)), tbody))
        print_plan(thead, tbody)

    def show_tasks(self):
        thead = tuple(map(lambda c: c['name'], self.columns()))
        tbody = []
        for task in self.tasks:
            tbody += task.view()
        return thead, tbody

    def edit(self, backend=DEFAULT_UI_BACKEND):
        if backend == 'tui':
            app = EditorApp(self)
            app.run()
