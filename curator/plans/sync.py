import os
import subprocess

from curator import Plan, Task, Media

class SyncPlan(Plan):
    def columns(self):
        return [
            { 'name': 'Input', 'width': '100%' },
            { 'name': 'Old start', 'width': '9' },
            { 'name': '+', 'width': '1' },
            { 'name': 'Delta', 'width': '9' },
            { 'name': '→', 'width': '1' },
            { 'name': "New start", 'width': '9' },
        ]

class SyncTask(Task):
    def __init__(self, input, output, start, delta):
        super().__init__([input], [output])
        self.start = start # Just for debugging
        self.delta = delta

    def view(self):
        t0 = self.start
        t1 = self.start + self.delta
        dt = self.delta
        return [(self.inputs[0].name, t0, "+", dt, "→", t1)]

    def apply(self):
        si = self.inputs[0]
        so = self.outputs[0]

        # Build ffmpeg command
        cmd = ['ffmpeg']
        cmd += ['-i', si.media.path]
        cmd += ['-itsoffset', str(self.delta)]
        cmd += ['-i', si.media.path]
        cmd += ['-c:v', 'copy']
        cmd += ['-c:a', 'copy']
        cmd += ['-c:s', 'copy']

        # Select streams respecting input order
        for i in range(si.media.num_streams()):
            if i == si.index:
                cmd += ['-map', f'1:{i}']
            else:
                cmd += ['-map', f'0:{i}']

        # Generate and replace from temporary directory
        with tempfile.TemporaryDirectory(dir=si.media.dir, prefix='.temp-curator-') as tmp:
            output = os.path.join(tmp, f'output.{si.media.ext}')
            cmd += [output]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                errors = result.stderr.decode('utf-8')
                raise Exception(f"Failed to sync {self.outputs[0].name} with ffmpeg:\n{errors}")
            os.replace(output, so.media.path)

def plan_sync(media):
    plan = SyncPlan()
    for m in media:
        pass # TODO
    return plan
