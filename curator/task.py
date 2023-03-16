class Task:
    def __init__(self, inputs=[], outputs=[]):
        self.inputs = inputs
        self.outputs = outputs
        self.enabled = True
        self.warnings = set()
        self.errors = set()
        self.id = None
        self.failed = False

    def add_warning(self, warning):
        self.warnings.add(warning)

    def add_error(self, error):
        self.errors.add(error)
        self.enabled = False

    def combine(self, other):
        assert(self.inputs == other.inputs)
        assert(self.outputs == other.outputs)
        assert(self.enabled == other.enabled)
        self.warnings |= other.warnings
        self.errors |= other.errors

    def concat(self, other):
        assert(self.outputs == self.inputs)
        raise Exception("Unimplemented")

    # Helpers
    def input_streams(self):
        for media in self.inputs:
            for stream in media.get_streams():
                yield stream

    def input_video_streams(self):
        for stream in self.input_streams():
            if stream.is_video():
                yield stream

    def input_audio_streams(self):
        for stream in self.input_streams():
            if stream.is_audio():
                yield stream

    def input_subtitle_streams(self):
        for stream in self.input_streams():
            if stream.is_subtitle():
                yield stream
