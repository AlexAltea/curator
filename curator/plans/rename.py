import logging
import os

from curator.analysis import *
from curator.databases import *
from curator import Plan, Task, Media

class RenamePlan(Plan):
    def show_tasks(self):
        thead = ("Old", "Source", "→", "New")
        tbody = []
        for task in self.tasks:
            name_input = task.inputs[0].name
            name_output = task.outputs[0].name
            tbody.append((name_input, task.source, "→", name_output))
        return thead, tbody

class RenameTask(Task):
    def __init__(self, input, output, source):
        super().__init__([input], [output])
        self.source = source

    def apply(self):
        src = self.inputs[0].path
        dst = self.outputs[0].path
        os.rename(src, dst)

def plan_rename(media, format, db=None, keep_tags=False):
    plan = RenamePlan()
    for m in media:
        # Detect name, year and tags
        name = detect_name(m.name)
        year = detect_year(m.name)
        tags = detect_tags(m.name)
        source = "analysis"
        if db and (entry := db.query(name, year)):
            name = entry.get('name')
            year = entry.get('year')
            source = db.name
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
        filename = filename.replace('@tags',
            ''.join(map(lambda t: f'[{t}] ', tags)))
        root, ext = os.path.splitext(filename)
        filename = root.strip() + ext

        if filename != m.name:
            output_path = os.path.join(os.path.dirname(m.path), filename)
            output_media = Media(output_path, Media.TYPE_FILE)
            task = RenameTask(m, output_media, source)
            plan.add_task(task)
    return plan
