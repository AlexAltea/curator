import logging
import os

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

    def validate(self):
        outputs = set()
        for task in self.tasks:
            for output in task.outputs:
                path = output.path
                if path in outputs:
                    task.add_error(f'Output {path} already exists in the plan')
                if os.path.exists(path):
                    task.add_error(f'Output {path} already exists in the filesystem')
                outputs.add(path)

    def apply(self):
        for task in self.tasks:
            if task.enabled:
                try:
                    task.apply()
                except Exception as e:
                    task.failed = True
                    print(f'Task #{task.id} with input {task.inputs[0]} failed:\n{e}')

    def show(self):
        from .tui import print_plan
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
        from .tui import EditorApp
        if backend == 'tui':
            app = EditorApp(self)
            app.run()
