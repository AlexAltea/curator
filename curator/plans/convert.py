import logging
import os
import subprocess

from curator import Plan, Task, Media

class ConvertPlan(Plan):
    def show_tasks(self):
        thead = ("Inputs", "→", "Output")
        tbody = []
        for task in self.tasks:
            tbody.append((task.inputs[0].name, "→", task.outputs[0].name))
        return thead, tbody

class ConvertTask(Task):
    def __init__(self, input, output, format, delete=False):
        super().__init__([input], [output])
        assert(output.type == Media.TYPE_FILE)
        self.format = format
        self.delete = delete
        self.flags = set()

    def apply(self):
        # Build ffmpeg command
        cmd = ['ffmpeg']
        if self.flags:
            cmd += ['-fflags', ''.join(self.flags)]
        cmd += ['-i', self.inputs[0].path]
        cmd += ['-c:v', 'copy']
        cmd += ['-c:a', 'copy']
        cmd += ['-c:s', 'copy']
        cmd += ['-c:d', 'copy']
        cmd += ['-c:t', 'copy']
        cmd += ['-map', '0']
        cmd += ['-map_metadata', '0']
        cmd += ['-movflags', 'use_metadata_tags']

        # Create output file
        output = self.outputs[0].path
        cmd += [output]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            if os.path.exists(output):
                os.remove(output)
            errors = result.stderr.decode('utf-8')
            raise Exception(f"Failed to convert to {output} with ffmpeg:\n{errors}")
        if self.delete:
            os.remove(self.inputs[0].path)

    def add_flag(self, flag):
        self.flags.add(flag)

def plan_convert(media, format, delete=False):
    plan = ConvertPlan()
    for m in media:
        root, ext = os.path.splitext(m.path)
        output_path = f'{root}.{format}'
        if os.path.exists(output_path):
            logging.debug(f'Skipping existing output: {output_path}')
            continue
        output_media = Media(output_path, Media.TYPE_FILE)
        task = ConvertTask(m, output_media, format, delete)
        if m.get_info()['format_name'] == 'avi' and m.has_video():
            task.add_warning(f'Media contains packets without PTS data')
            task.add_flag('+genpts')
        plan.add_task(task)
    return plan
