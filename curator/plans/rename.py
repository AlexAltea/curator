import logging
import os

from curator.analysis import *
from curator.databases import *
from curator import Plan, Task, Media

class RenamePlan(Plan):
    def columns(self):
        return [
            { 'name': 'Old', 'width': '50%' },
            { 'name': 'Source', 'width': '8' },
            { 'name': '→', 'width': '1' },
            { 'name': "New", 'width': '50%' },
        ]

class RenameTask(Task):
    def __init__(self, input, name, source, alternatives=[]):
        super().__init__([input])
        self.update_output(name)
        self.source = source
        self.alternatives = alternatives

    def update_output(self, name):
        input = self.inputs[0]
        output_path = os.path.join(os.path.dirname(input.path), name)
        output_media = Media(output_path, Media.TYPE_FILE)
        self.outputs = [output_media]

    def view(self):
        name_input = self.inputs[0].name
        name_output = self.outputs[0].name
        return [(name_input, self.source, "→", name_output)]

    def apply(self):
        src = self.inputs[0].path
        dst = self.outputs[0].path
        if not os.path.exists(dst):
            os.rename(src, dst)

def normalize(filename):
    replacements = [
        (r'(\w): ',  r'\1 - '),  # Remove colons when used as separators
        (r'\.\.\.',  r''),       # Remove ellipsis
        (r' vs\. ',  r' vs '),   # Remove versus period
        (r' 1/3 ',   r' ⅓ '),    # Convert to vulgar fractions
        (r'/',       r'-'),      # Remove slashes
        (r'\?',       r''),      # Remove question marks
    ]
    for pattern, replacement in replacements:
        filename = re.sub(pattern, replacement, filename)
    return filename

def plan_rename(media, format, db=None):
    plan = RenamePlan()
    for m in media:
        # Detect name, year and tags
        name = detect_name(m.name)
        year = detect_year(m.name)
        tags = detect_tags(m.name)
        dbid = None
        oname = None
        source = "analysis"
        if db and (entries := db.query(name, year)):
            entry = entries[0]
            name = entry.get('name')
            year = entry.get('year')
            dbid = entry.get('dbid')
            oname = entry.get('oname')
            source = db.name
        if '@name' in format and not name:
            logging.warning(f"Could not rename: {m.name} (name not detected)")
            continue
        if '@year' in format and not year:
            logging.warning(f"Could not rename: {m.name} (year not detected)")
            continue
        if '@dbid' in format and not dbid:
            logging.warning(f"Could not rename: {m.name} (database id not detected)")
            continue
        if '@oname' in format and not oname:
            logging.warning(f"Could not rename: {m.name} (original name not found)")
            continue

        # Generate new filename
        filename = format
        filename = filename.replace('@name', str(name))
        filename = filename.replace('@oname', str(oname))
        filename = normalize(filename)
        filename = filename.replace('@dbid', str(dbid))
        filename = filename.replace('@year', str(year))
        filename = filename.replace('@ext', m.ext.lower())
        filename = filename.replace('@tags',
            ''.join(map(lambda t: f'[{t}] ', tags)))
        root, ext = os.path.splitext(filename)
        filename = root.strip() + ext
        if filename != m.name:
            task = RenameTask(m, filename, source)
            plan.add_task(task)
    return plan
