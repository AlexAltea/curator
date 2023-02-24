import os
import subprocess

from curator import Plan, Task, Media

class MergePlan(Plan):
    def columns(self):
        return [
            { 'name': 'Inputs', 'width': '50%' },
            { 'name': '→', 'width': '1' },
            { 'name': "Output", 'width': '50%' },
        ]

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
        if self.inputs[0].ext == 'mp4' and self.format == 'mkv':
            cmd += ['-c:s', 'srt']

        # Create output file
        cmd += [self.outputs[0].path]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            errors = result.stderr.decode('utf-8')
            raise Exception(f"Failed to merge into {self.outputs[0].name} with ffmpeg:\n{errors}")
        if self.delete:
            for media in self.inputs:
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
            print(m.name)
    return plan
