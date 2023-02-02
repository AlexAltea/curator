import os
import subprocess
import tempfile

from curator import Plan, Task, Media

class TagPlan(Plan):
    def show_tasks(self):
        thead = ("Name", "Stream", "Old tag", "→", "New tag")
        tbody = []
        for task in self.tasks:
            s = task.inputs[0]
            tbody.append((s.media.name, s.index, task.old_value, "→", task.new_value))
        return thead, tbody

class TagTask(Task):
    def __init__(self, input, tag, old_value, new_value=None):
        super().__init__([input], [])
        self.tag = tag
        self.old_value = old_value
        self.new_value = new_value

    def apply(self):
        s = self.inputs[0]
        cmd = ['ffmpeg']
        cmd += ['-i', s.media.path]
        cmd += ['-c:v', 'copy']
        cmd += ['-c:a', 'copy']
        cmd += ['-c:s', 'copy']
        cmd += ['-map', '0']
        cmd += ['-map_metadata', '0']
        cmd += [f'-metadata:s:{s.index}', f'{self.tag}={self.new_value}']

        # Tweaks
        if s.media.get_info()['format_name'] == 'avi' and self.tag == 'language':
            if (audio_index := s.audio_index()) not in range(9):
                raise Exception("RIFF IASx tags should only support up to 9 audio tracks")
            cmd += ['-metadata', f'IAS{audio_index + 1}={self.new_value}']

        with tempfile.TemporaryDirectory(dir=s.media.dir, prefix='.temp-curator-') as tmp:
            output = os.path.join(tmp, f'output.{s.media.ext}')
            cmd += [output]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                errors = result.stderr.decode('utf-8')
                raise Exception(f"Failed to update tags in {s.media.name} with ffmpeg:\n{errors}")
            os.replace(output, s.media.path)

    def set_new_value(self, new_value):
        self.new_value = new_value

def plan_tag(media, stype, tag, value=None, skip_tagged=False, opts=None):
    # Locate relevant streams
    plan = TagPlan()
    tasks = []
    for m in media:
        if m.has_video_ext():
            for stream in m.get_streams():
                stream_info = stream.get_info()
                if stream_info['codec_type'] != stype:
                    continue
                stream_value = stream_info['tags'].get(tag)
                if skip_tagged and stream_value is not None:
                    continue
                task = TagTask(stream, tag, stream_value)
                tasks.append(task)
    # Set or auto-detect value
    if value:
        for task in tasks:
            task.set_new_value(value)
    elif tag == 'language':
        for task in tasks:
            s = task.inputs[0]
            lang = s.detect_language(opts)
            if m.get_info()['format_name'] == 'avi' and \
               s.get_info()['codec_type'] == 'audio' and s.audio_index() > 8:
                task.add_error("Cannot change AVI audio stream using IASx tags. Index out of range.")
            task.set_new_value(lang)
    # Prepare plan with changes
    for task in tasks:
        if m.get_info()['format_name'] == 'avi':
            task.add_warning("Modifying AVI metadata might affect stream synchronization.")
        if task.old_value != task.new_value and task.new_value is not None:
            plan.add_task(task)
    return plan
