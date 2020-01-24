"""
THIS is not in active development, please check
https://github.com/davidhalter/jedi/issues/667 first before editing.

Introduce some basic refactoring functions to |jedi|. This module is still in a
very early development stage and needs much testing and improvement.

.. warning:: I won't do too much here, but if anyone wants to step in, please
             do. Refactoring is none of my priorities

It uses the |jedi| `API <api.html>`_ and supports currently the
following functions (sometimes bug-prone):

- rename
- extract variable
- inline variable
"""
import difflib

from parso import python_bytes_to_unicode, split_lines
from jedi.inference import helpers


class Refactoring(object):
    def __init__(self, change_dct):
        """
        :param change_dct: dict(old_path=(new_path, old_lines, new_lines))
        """
        self.change_dct = change_dct

    def old_files(self):
        dct = {}
        for old_path, (new_path, old_l, new_l) in self.change_dct.items():
            dct[old_path] = '\n'.join(old_l)
        return dct

    def new_files(self):
        dct = {}
        for old_path, (new_path, old_l, new_l) in self.change_dct.items():
            dct[new_path] = '\n'.join(new_l)
        return dct

    def diff(self):
        texts = []
        for old_path, (new_path, old_l, new_l) in self.change_dct.items():
            if old_path:
                udiff = difflib.unified_diff(old_l, new_l)
            else:
                udiff = difflib.unified_diff(old_l, new_l, old_path, new_path)
            texts.append('\n'.join(udiff))
        return '\n'.join(texts)


#cf complete() signature in api/__init__.py
def rename(script, new_name, line=None, column=None, **kwargs):
    """ The `args` / `kwargs` params are the same as in `api.Script`.
    :param new_name: The new name of the script.
    :param script: The source Script object.
    :return: list of changed lines/changed files
    """
    return Refactoring(_rename(script.get_references(line, column), new_name))


def _rename(names, replace_str):
    """ For both rename and inline. """
    order = sorted(names, key=lambda x: (x.module_path, x.line, x.column),
                   reverse=True)

    def process(path, old_lines, new_lines):
        if new_lines is not None:  # goto next file, save last
            dct[path] = path, old_lines, new_lines

    dct = {}
    current_path = object()
    new_lines = old_lines = None
    for name in order:
        if name.in_builtin_module():
            continue
        if current_path != name.module_path:
            current_path = name.module_path

            process(current_path, old_lines, new_lines)
            if current_path is not None:
                # None means take the source that is a normal param.
                with open(current_path) as f:
                    source = f.read()

            new_lines = split_lines(python_bytes_to_unicode(source))
            old_lines = new_lines[:]

        nr, indent = name.line, name.column
        line = new_lines[nr - 1]
        new_lines[nr - 1] = line[:indent] + replace_str + \
            line[indent + len(name.name):]
    process(current_path, old_lines, new_lines)
    return dct


def extract(script, new_name):
    """ The `args` / `kwargs` params are the same as in `api.Script`.
    :param operation: The refactoring operation to execute.
    :type operation: str
    :type source: str
    :return: list of changed lines/changed files
    """
    new_lines = split_lines(python_bytes_to_unicode(script.source))
    old_lines = new_lines[:]

    user_stmt = script._parser.user_stmt()

    # TODO care for multi-line extracts
    dct = {}
    if user_stmt:
        pos = script._pos
        line_index = pos[0] - 1
        # Be careful here. 'array_for_pos' does not exist in 'helpers'.
        arr, index = helpers.array_for_pos(user_stmt, pos)
        if arr is not None:
            start_pos = arr[index].start_pos
            end_pos = arr[index].end_pos

            # take full line if the start line is different from end line
            e = end_pos[1] if end_pos[0] == start_pos[0] else None
            start_line = new_lines[start_pos[0] - 1]
            text = start_line[start_pos[1]:e]
            for l in range(start_pos[0], end_pos[0] - 1):
                text += '\n' + str(l)
            if e is None:
                end_line = new_lines[end_pos[0] - 1]
                text += '\n' + end_line[:end_pos[1]]

            # remove code from new lines
            t = text.lstrip()
            del_start = start_pos[1] + len(text) - len(t)

            text = t.rstrip()
            del_end = len(t) - len(text)
            if e is None:
                new_lines[end_pos[0] - 1] = end_line[end_pos[1] - del_end:]
                e = len(start_line)
            else:
                e = e - del_end
            start_line = start_line[:del_start] + new_name + start_line[e:]
            new_lines[start_pos[0] - 1] = start_line
            new_lines[start_pos[0]:end_pos[0] - 1] = []

            # add parentheses in multi-line case
            open_brackets = ['(', '[', '{']
            close_brackets = [')', ']', '}']
            if '\n' in text and not (text[0] in open_brackets and text[-1]
                                     == close_brackets[open_brackets.index(text[0])]):
                text = '(%s)' % text

            # add new line before statement
            indent = user_stmt.start_pos[1]
            new = "%s%s = %s" % (' ' * indent, new_name, text)
            new_lines.insert(line_index, new)
    dct[script.path] = script.path, old_lines, new_lines
    return Refactoring(dct)


def inline(script, line=None, column=None):
    """
    Replace a variable with its definition
    :type script: api.Script
    """
    new_lines = split_lines(python_bytes_to_unicode(script._code))

    dct = {}

    definitions = script.goto(line, column)
    assert len(definitions) == 1

    stmt = definitions[0]
    assert stmt.type == 'statement'
    # TODO disallow keywords, methods here

    # a list of definitions
    references = script.get_references(line, column)

    # TODO
    # don't allow multi-line refactorings for now.
    # assert stmt.start_pos[0] == stmt.end_pos[0] # TODO

    # Examples include, multiline lists, dicts, statement continuations or parens.

    # TODO factor this into a method
    # search forward until next definition, checking for reuses
    refs2 = []
    newDefLine = 0
    for r in references:
        if (r.line, r.column) == (stmt.line, stmt.column):
            continue

        if r.is_definition():
            newDefLine = r.line
            continue

        if newDefLine > 0:
            if r.line == newDefLine:
                refs2.append(r)
            else:
                break
        else:
            refs2.append(r)

    # inlines = [r for r in references
    #            if (r.line, r.column) != (stmt.line, stmt.column)]
    inlines = sorted(refs2, key=lambda x: (x.module_path, x.line, x.column),
                     reverse=True)

    index = stmt.line - 1
    line = new_lines[index]

    # the parent expression of the form "x = expr"
    assign_stmt = stmt._name.tree_name.parent

    if len(stmt._name.assignment_indexes()) > 0:
        # the same as parso.tree.search_ancestor()
        while assign_stmt.type != 'expr_stmt':
            assign_stmt = assign_stmt.parent

        expr_tree = assign_stmt.get_rhs()
        replace_str = expr_tree.get_code(include_prefix=False)
    else:
        expr_tree = assign_stmt.children[2]
        replace_str = expr_tree.get_code(include_prefix=False)

    # tuples and lambdas need parentheses
    if (expr_tree.type == 'testlist_star_expr' or
        expr_tree.type == 'lambdef' or
        expr_tree.type == 'lambdef_nocond'):
        if replace_str[0] not in ['(', '[', '{']:
            replace_str = '(%s)' % replace_str

    # TODO eliminate del, nonlocal

    # if len(stmt.get_defined_names()) == 1:
    #     line = line[:stmt.start_pos[1]] + line[stmt.end_pos[1]:]

    line_prefix = line[:assign_stmt.start_pos[1]]
    line_suffix = line[assign_stmt.end_pos[1]:].strip()

    if line_suffix and line_suffix[0] == ';':
        line_suffix = line_suffix[1:].strip()
    line = line_prefix + line_suffix

    dct = _rename(inlines, replace_str)
    # remove the empty line
    new_lines = dct[script.path][2]
    if line.strip():
        new_lines[index] = line
    else:
        new_lines.pop(index)

    return Refactoring(dct)
