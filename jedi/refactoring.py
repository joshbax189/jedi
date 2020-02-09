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
        """
        :returns dict(old_path=old_file_string)
        """
        dct = {}
        for old_path, (new_path, old_l, new_l) in self.change_dct.items():
            dct[old_path] = '\n'.join(old_l)
        return dct

    def new_files(self):
        """
        :returns dict(new_path=new_file_string)
        """
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

    def new_lines(self, old_path):
        """
        :returns updated list of lines for file at old_path
        """
        return self.change_dct[old_path][2]

    def set_new_lines(self, path, updates):
        """
        Replace new_lines at path with updates.
        """
        self.change_dct[path] = (self.change_dct[path][0], self.change_dct[path][1], updates)


# cf complete() signature in api/__init__.py
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


# Convert a definition a,b,c = e into the equivalent
# multi-line definitions.
# May introduce an extra variable if e cannot be destructured.
def unpack(script, line=None, column=None):
    pass


# TODO use consistent names
# TODO look for similar functions to reuse
# TODO error checking:
#      definition contains a *
#      definition contains a non-simple unpacking
def inline(script, line=None, column=None):
    """
    Replace a variable with its definition
    :type script: api.Script
    :rtype: :class:`Refactoring`
    """

    # Find any relevant definitions/uses
    # Get a ValueError if pos is not valid
    definitions = script.goto(line, column)

    if definitions == []:
        raise ValueError('No definition found at '+(line, column))

    # aka the definition statement to be replaced
    # type: 'api.classes.Definition'
    stmt = definitions[0]

    # e.g. def f() is a definition but not a statement
    # stmt.is_definition true, stmt.type != statement
    if stmt.type != 'statement':
        raise ValueError('Not a statement')

    # TODO disallow * replacements

    # Definitions divided into those to replace within and those to remove.
    targets, remove = _target_definitions(script, stmt)

    # By convention lines are numbered from 1
    stmt_index = stmt.line - 1
    new_lines = split_lines(python_bytes_to_unicode(script._code))
    # Split the line into assignment and residue
    # E.g. a, b = 1, 2 --> a = 1, b = 2
    replace_str, line = _split_insertion_expr(stmt, new_lines[stmt_index])

    # Perform replacements
    dct = Refactoring(_rename(targets, replace_str))

    stmt_end_index = stmt._name.tree_name.parent.end_pos[0] - 1

    # Remove everything in remove, replace with line residue from above.
    dct.set_new_lines(script.path,
                      _cleanup_after_insertion(dct.new_lines(script.path), line, stmt_index, remove,
                                               stmt_end_index))
    return dct


def _target_definitions(script, stmt):
    """
    :returns A pair of Definition lists (replace, remove), where replace should be replaced with
    the inlining expression, and remove should be removed from the final result.
    The original statement is always in 'remove'.
    """

    # whether a Definition for x is in "del x"
    def def_in_del_stmt(d):
        return d._name.tree_name.parent.type == 'del_stmt'

    def def_in_nl_stmt(d):
        return d._name.tree_name.parent.type == 'nonlocal_stmt'

    # assumes that references is in same order as source file
    references = script.get_references(stmt.line, stmt.column)

    active_refs = []
    remove_refs = []

    new_def_index = 0
    seen_original_stmt = False
    for r in references:
        # skip to original definition
        # TODO perhaps need to check module name too
        if (r.line, r.column) == (stmt.line, stmt.column):
            seen_original_stmt = True
            remove_refs.append(r)
            continue

        # re-assignment may use original expr, e.g. x=x+1
        # if not, break the loop
        if new_def_index > 0 and r.line != new_def_index:
            break

        # In active scope of definition
        if seen_original_stmt:
            # mark a del statement
            # this terminates the scope, I think parso correctly accounts for this
            if def_in_del_stmt(r):
                remove_refs.append(r)
                new_def_index = r.line
                continue
            # mark a re-assignment
            elif r.is_definition():
                new_def_index = r.line
                continue
            elif def_in_nl_stmt(r):
                remove_refs.append(r)
                continue
            else:
                active_refs.append(r)

    active_refs = sorted(active_refs, key=lambda x: (x.module_path, x.line, x.column),
                         reverse=True)

    return active_refs, remove_refs


# return a string tuple: (insertion_expr, line_without_expr)
# should trim additional semicolons, commas and whitespace in new line
# should add necessary parens in insertion_expr
def _split_insertion_expr(stmt, orig_line):
    # the parent expression of the form "x = expr"
    assign_stmt = stmt._name.tree_name.get_definition()
    lhs = assign_stmt.children[0]
    rhs = assign_stmt.get_rhs()

    is_multiline = assign_stmt.end_pos[0] != assign_stmt.start_pos[0]

    # if stmt.line == 179:
    #     import pdb; pdb.set_trace()

    if len(stmt._name.assignment_indexes()) > 0:
        # TODO needs to be recursive to support e.g. (a, (b, c)) = (1, (2,3))
        # TODO what about (a, (b, c)) = e?
        for n, e in zip(lhs.children, rhs.children):
            if n.value != ',' and n.start_pos == stmt._name.start_pos:
                replace_expr = e

        # see jedi.inference.value.iterable.unpack_tuple_to_dict !!!
        # no, seems to use type context

        line = _cut_with_delim(orig_line, replace_expr.start_pos[1], replace_expr.end_pos[1], ',')
        line = _cut_with_delim(line, stmt._name.tree_name.start_pos[1], stmt._name.tree_name.end_pos[1], ',')
    elif len(assign_stmt.get_defined_names()) > 1:
        # of the form a = b = e
        replace_expr = rhs
        name_stmt = stmt._name.tree_name
        line = _cut_with_delim(orig_line, name_stmt.start_pos[1], name_stmt.end_pos[1], '=')
    elif is_multiline:
        replace_expr = rhs
        line = ''
    else:
        # simple case
        replace_expr = rhs
        # as the whole expr_stmt is to be removed, check for statement after semicolon
        line = _cut_with_delim(orig_line, assign_stmt.start_pos[1], assign_stmt.end_pos[1], ';')

    replace_str = replace_expr.get_code(include_prefix=False)
    # tuples and lambdas need parentheses
    if replace_expr.type in ['testlist_star_expr', 'lambdef', 'lambdef_nocond']:
        if replace_str[0] not in ['(', '[', '{']:
            replace_str = '(%s)' % replace_str

    return replace_str, line


def _cut_with_delim(s, start, end, delim):
    """
    Remove [start:end] from s, consuming trailing delim if present.
    :rtype: String
    """
    prefix = s[:start]
    suffix = s[end:].strip()

    if suffix:
        if suffix[0] == delim:
            suffix = suffix[1:].strip()
        else:
            assert suffix[0].isspace(), 'Split at non-whitespace char'

    return prefix + suffix


def _cleanup_after_insertion(replaced_lines, line_residue, index, remove_refs, index_end):

    remove_indices = {x.line - 1 for x in remove_refs}
    result = []
    for i, line in enumerate(replaced_lines):
        if i == index:
            if line_residue.strip():
                result.append(line_residue)
            else:
                continue
        elif index < i and i <= index_end:
            # drop all parts of a multiline statment
            continue
        elif i not in remove_indices:
            result.append(line)

    return result
