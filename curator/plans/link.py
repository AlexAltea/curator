import os

from curator import Plan, Task, Media

class LinkPlan(Plan):
    def show_tasks(self):
        thead = ("Name",)
        tbody = []
        for task in self.tasks:
            name = task.inputs[0].name
            tbody.append((name,))
        return thead, tbody

class LinkTask(Task):
    def __init__(self, input, output):
        super().__init__([input], [output])
        assert(output.type == Media.TYPE_LINK)

    def apply(self):
        src = self.inputs[0].path
        lnk = self.outputs[0].path
        os.symlink(src, lnk)

def plan_link(media, output):
    plan = LinkPlan()
    for m in media:
        path = os.path.join(output, m.name)
        link = Media(path, Media.TYPE_LINK)
        task = LinkTask(m, link)
        plan.add_task(task)
    return plan
