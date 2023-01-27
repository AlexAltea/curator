class Task:
    def __init__(self, inputs=[], outputs=[]):
        self.inputs = inputs
        self.outputs = outputs
        self.enabled = True
        self.warnings = []
        self.errors = []
        self.id = None

    def add_warning(self, warning):
        self.warnings.append(warning)
