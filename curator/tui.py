import math
import shutil
import time

import numpy

from rich.style import Style
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult, RenderResult
from textual.binding import Binding
from textual.containers import Grid
from textual.geometry import Size
from textual.keys import Keys
from textual.screen import Screen
from textual.widgets.data_table import ColumnKey, RowKey
from textual.widgets._header import HeaderIcon
from textual.widgets import Button, Header, Footer, DataTable, Static

class TaskFlow(DataTable):
    COMPONENT_CLASSES = {
        "taskflow--task-odd",
        "taskflow--task-even",
        "taskflow--task-disabled",
    }
    DEFAULT_CSS = """
        TaskFlow > .taskflow--task-odd {
            background: $primary 0%;
        }
        TaskFlow > .taskflow--task-even {
            background: $primary 10%;
        }
        TaskFlow > .taskflow--task-disabled {
            color: $text 25%;
        }
    """

    def __init__(self, plan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_type = 'row'
        self.zebra_stripes = False
        self.styles.overflow_x = "hidden"
        self.plan = plan

    def add_column(self, name):
        align = "right" if name == "#" else None
        label = Text(name, overflow='ellipsis', justify=align)
        super().add_column(label, key=name)

    # HACK: Overriding private method
    def _render_line_in_row(self, row_key, line_no, base_style, cursor_location, hover_location):
        index = self._row_locations.get(row_key)
        style = "taskflow--task-odd"
        if index is not None:
            if index % 2:
                style = "taskflow--task-even"
            if not self.plan[index].enabled:
                style = "taskflow--task-disabled"
        style = self.get_component_styles(style).rich_style
        return super()._render_line_in_row(row_key, line_no, style, cursor_location, hover_location)

class EditorApp(App):
    TITLE = "Curator"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f", "view_flow", "View flow"),
        ("c", "view_commands", "View commands"),
    ]

    def __init__(self, plan):
        super().__init__()
        self.plan = plan

    def compose(self) -> ComposeResult:
        yield Header()
        yield TaskFlow(self.plan)
        yield Footer()

    def on_mount(self):
        # Remove annoying icon
        self.query_one(HeaderIcon).icon = ' '
        # Add table contents
        table = self.query_one(DataTable)
        for column in self.get_columns():
            table.add_column(column['name'])
        for task in self.plan:
            view = task.view()
            row = map(lambda c: '\n'.join(c), zip(*view))
            row = [Text(str(task.id), justify="right", overflow='ellipsis')] + \
                list(map(lambda text: Text(text, overflow='ellipsis'), row))
            table.add_row(*row, height=len(view))

    def on_key(self, event):
        if event.key == Keys.Space or event.key == Keys.Enter:
            self.toggle_selected_task()

    def action_view_flow(self):
        return

    def action_view_commands(self):
        return

    def toggle_selected_task(self):
        table = self.query_one(TaskFlow)
        index = table.cursor_coordinate.row
        self.plan[index].enabled ^= True

        # HACK: Without this styles don't refresh
        # TODO: Find a better approach
        table._line_cache.clear()

    def get_columns(self):
        first_width = str(len(str(len(self.plan))))
        columns = [{ 'name': '#', 'width': str(first_width) }] + self.plan.columns()
        return columns

    def compute_column_widths(self, w):
        columns = self.get_columns()
        # First reserve absolute widths
        for col in columns:
            if not col['width'].endswith('%'):
                col_width = int(col['width'])
                col['width'] = col_width
                w -= col_width
        # Then reserve relative widths
        scale = 1
        for col in columns:
            if isinstance(col['width'], str):
                col_ratio = float(col['width'][:-1]) / 100
                col_width = round(w * col_ratio * scale)
                col['width'] = col_width
                scale_div = (1 - col_ratio * scale)
                scale = scale_div and scale / scale_div or math.inf # Avoid division by zero
                w -= col_width
        # Adjust last column
        if w != 0:
            col['width'] += w
        return columns

    def on_resize(self, event):
        table = self.query_one(TaskFlow)
        cols = self.compute_column_widths(event.size.width)
        for c in cols:
            key = ColumnKey(c['name'])
            col = table.columns.get(key)
            if col:
                col.width = c['width']
                col.auto_width = False
        table._require_update_dimensions = True


ALIGN_LEFT = 1
ALIGN_RIGHT = 2

# Helpers
def print_field(string, length, align=ALIGN_LEFT):
    lpad = ' '
    rpad = ' '
    if len(string) <= length:
        if align == ALIGN_LEFT:
            rpad += ' ' * (length - len(string))
        if align == ALIGN_RIGHT:
            padr += ' ' * (length - len(string))
        return lpad + string + rpad
    else:
        return lpad + string[:length-3] + '...' + rpad

def compute_width(table, maxwidth=80):
    widths = [] # (width, avgw, maxw, fixed)
    table = numpy.transpose(table)
    for column in table:
        lengths = list(map(len, column))
        average = numpy.average(lengths)
        maximum = max(lengths)
        if maximum <= 4:
            widths.append((maximum, average, maximum, True))
        else:
            widths.append((maximum, average, maximum, False))

    # Account for padding and borders
    maxwidth = maxwidth - 3*len(table) + 1

    # Reduce column size if overflow
    curwidth = sum(map(lambda x: x[0], widths))
    if curwidth > maxwidth:
        removal = curwidth - maxwidth 
        fixwidth = sum(map(lambda x: x[0], filter(lambda x: x[3], widths)))
        movwidth = sum(map(lambda x: x[0], filter(lambda x: not x[3], widths)))
        ratio = (movwidth-removal)/movwidth
        for i in range(len(widths)):
            width = widths[i]
            if width[3]: continue
            widths[i] = (int(width[0] * ratio - 1),) + width[1:]
    return list(map(lambda x: x[0], widths))
        
def print_plan(thead, tbody):
    # Add ID column
    thead = ("#",) + thead
    for i in range(len(tbody)):
        tbody[i] = (str(i+1),) + tbody[i]

    # Compute width for each column
    termsize = shutil.get_terminal_size()
    table = [thead] + tbody
    widths = compute_width(table, termsize.columns)
    
    # Print table
    print('┌' + '┬'.join(list(map(lambda w: '─'*(w+2), widths))) + '┐')
    print('│' + '│'.join(list(map(lambda x: print_field(*x), zip(thead, widths)))) + '│')
    print('├' + '┼'.join(list(map(lambda w: '─'*(w+2), widths))) + '┤')
    for row in tbody:
        print('│' + '│'.join(list(map(lambda x: print_field(*x), zip(row, widths)))) + '│')
    print('└' + '┴'.join(list(map(lambda w: '─'*(w+2), widths))) + '┘')
