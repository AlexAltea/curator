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
        cmd += ['-c', 'copy']

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

def plan_merge(media, format, delete=False):
    plan = MergePlan()
    cur_video = None
    cur_task = None
    for m in media:
        if m.has_video_ext():
            basename, _ = os.path.splitext(m.name)
            basepath, _ = os.path.splitext(m.path)
            cur_output = Media(f'{basepath}.{format}', Media.TYPE_FILE)
            cur_video = basename
            if cur_task and len(cur_task.inputs) >= 2:
                plan.add_task(cur_task)
            cur_task = MergeTask([m], cur_output, format, delete)
        elif cur_task and cur_video in m.name:
            cur_task.inputs.append(m)
        else:
            cur_task = None
    if cur_task and len(cur_task.inputs) >= 2:
        plan.add_task(cur_task)
    return plan
