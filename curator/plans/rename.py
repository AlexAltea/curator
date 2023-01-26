import logging
import os

from curator.analysis import *
from curator.databases import *
from curator import Plan, Task, Media

class RenamePlan(Plan):
    def show_tasks(self):
        thead = ("Old", "→", "New")
        tbody = []
        for task in self.tasks:
            name_input = task.inputs[0].name
            name_output = task.outputs[0].name
            tbody.append((name_input, "→", name_output))
        return thead, tbody

class RenameTask(Task):
    def __init__(self, input, output):
        super().__init__([input], [output])

    def apply(self):
        src = self.inputs[0].path
        dst = self.outputs[0].path
        os.rename(src, dst)

def plan_rename(media, format, db=None):
    plan = RenamePlan()
    for m in media:
        # Detect name and year
        name = detect_name(m.name)
        year = detect_year(m.name)
        if db and (entry := db.query(name, year)):
            name = entry.get('name')
            year = entry.get('year')
        if '@name' in format and not name:
            logging.warning(f"Could not rename: {m.name} (name not detected)")
            continue
        if '@year' in format and not year:
            logging.warning(f"Could not rename: {m.name} (year not detected)")
            continue

        # Generate new filename
        filename = format
        filename = filename.replace('@name', str(name))
        filename = filename.replace('@year', str(year))
        filename = filename.replace('@ext', m.ext.lower())
        if filename != m.name:
            output_path = os.path.join(os.path.dirname(m.path), filename)
            output_media = Media(output_path, Media.TYPE_FILE)
            plan.add_task(RenameTask(m, output_media))
    return plan
