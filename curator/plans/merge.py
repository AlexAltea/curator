import os
import subprocess
import tempfile

from curator import Plan, Task, Media

class MergePlan(Plan):
    def columns(self):
        return [
            { 'name': 'Inputs', 'width': '50%' },
            { 'name': '→', 'width': '1' },
            { 'name': "Output", 'width': '50%' },
        ]

    def validate(self):
        # Overriding Plan.validate since MergePlans allow for inplace merges
        # where the output already exists in the filesystem.
        outputs = set()
        for task in self.tasks:
            for output in task.outputs:
                path = output.path
                if path in outputs:
                    task.add_error(f'Output {path} already exists in the plan')
                outputs.add(path)

class MergeTask(Task):
    def __init__(self, inputs, output, format, delete):
        super().__init__(inputs, [output])
        self.format = format
        self.delete = delete

    def view(self):
        rows = [(self.inputs[0].name, "→", self.outputs[0].name)]
        for m in self.inputs[1:]:
            rows.append((m.name, "↗", ""))
        return rows
    
    def apply(self):
        # Build ffmpeg command
        cmd = ['ffmpeg']
        for minput in self.inputs:
            cmd += ['-i', minput.path]
        for i in range(len(self.inputs)):
            cmd += ['-map', str(i)]
        cmd += ['-c:v', 'copy']
        cmd += ['-c:a', 'copy']

        # Reencode MP4/TX3G to MKV/SRT
        if self.inputs[0].ext == 'mp4' and \
           self.inputs[0].has_subtitle() and self.format == 'mkv':
            cmd += ['-c:s', 'srt']
        else:
            cmd += ['-c:s', 'copy']

        # Create output file
        output = self.outputs[0]
        with tempfile.TemporaryDirectory(dir=output.dir, prefix='.temp-curator-') as tmp:
            output_tmp = os.path.join(tmp, f'output.{output.ext}')
            cmd += [output_tmp]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                errors = result.stderr.decode('utf-8')
                raise Exception(f"Failed to merge into {output.name} with ffmpeg:\n{errors}")
            os.replace(output_tmp, output.path)
            if self.delete:
                for media in self.inputs:
                    if media.path == output.path:
                        continue # Do not accidentally remove output after in-place merges
                    os.remove(media.path)

def find_related(target, media):
    basename, _ = os.path.splitext(target.name)
    matches = []
    for m in media:
        if basename in m.name and m is not target:
            matches.append(m)
    return matches

def plan_merge(media, format, delete=False):
    plan = MergePlan()
    for m in media:
        if not m.has_video_ext():
            continue
        basepath, _ = os.path.splitext(m.path)
        output = Media(f'{basepath}.{format}', Media.TYPE_FILE)
        related = find_related(m, media)
        if len(related) >= 1:
            task = MergeTask([m] + related, output, format, delete)
            plan.add_task(task)
    return plan
