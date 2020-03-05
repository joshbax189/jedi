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
from parso.tree import search_ancestor


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


def extract(script, new_name, line=None, column=None, end_line=None, end_column=None):
    """ Extract an expression to a variable.
    Expressions are selected by marking start and end positions.
    If no end mark is given, it is treated as EOL, which usually means select the entire expression.
    """
    new_lines = split_lines(python_bytes_to_unicode(script._code))
    old_lines = new_lines[:]
    dct = {}

    target = _find_sub_expr(script, line, column, end_line, end_column)

    cut_start_pos = target.start_pos
    cut_end_pos = target.end_pos

    line_index = line - 1
    start_code = new_lines[line_index]

    is_multiline = cut_start_pos[0] != cut_end_pos[0]

    if not is_multiline:
        text = start_code[cut_start_pos[1]:cut_end_pos[1]]
        start_code = start_code[:cut_start_pos[1]] + new_name + start_code[cut_end_pos[1]:]
        new_lines[line_index] = start_code
    else:
        text = start_code[cut_start_pos[1]:]
        for l in range(cut_start_pos[0], cut_end_pos[0] - 1):
            text += '\n' + new_lines[l]

        end_code = new_lines[cut_end_pos[0] - 1]
        text += '\n' + end_code[:cut_end_pos[1]]
        new_lines[cut_end_pos[0] - 1] = end_code[cut_end_pos[1]:]

    # add parentheses in multi-line case
    open_brackets = ['(', '[', '{']
    close_brackets = [')', ']', '}']

    if '\n' in text and not (text[0] in open_brackets and text[-1]
                             == close_brackets[open_brackets.index(text[0])]):
        text = '(%s)' % text

    # add new line before statement
    indent = len(start_code) - len(start_code.lstrip())
    new = "%s%s = %s" % (' ' * indent, new_name, text)
    new_lines.insert(line_index, new)

    dct[script.path] = script.path, old_lines, new_lines
    return Refactoring(dct)


def _find_sub_expr(script, line=None, column=None, end_line=None, end_column=None):
    # Find maximal (closest to root) sub-expression between the two positions satisfying:
    # it is assignable (exclude x = y)
    # it can be substituted for (func call f>(x)< should not become fy)
    # it does not contain anything BEFORE the first position (e.g. (>x + y)< becomes (z))
    # CE: a > + b + c</ should this extract a + b + c or b + c?
    # a None end pos is treated as EOL
    # it has balanced parens, quotes

    # Multiline?
    # Can it return a list of targets?
    # e.g. x, >y, z< or a + > b + c <

    def pos_in_node(n, pos):
        return n.start_pos <= pos and pos <= n.end_pos

    # defines assignable
    def cut_eligible(n):
        return n.type not in ['operator', 'trailer', 'expr_stmt']

    start_leaf = script._module_node.get_leaf_for_position((line, column))
    target = start_leaf

    start_pos = start_leaf.start_pos #(line, column)

    if end_line is not None and \
       end_column is not None:
        end_pos = (end_line, end_column)

        while not pos_in_node(target, end_pos):
            target = target.parent
    else:
        while target:
            if target.parent is None or start_pos >= target.parent.start_pos or not cut_eligible(target.parent):
                if cut_eligible(target):
                    break
                else:
                    target = start_leaf.get_next_sibling()
            else:
                target = target.parent

    return target


def get_sub_positions(script, line, column=None, include_names=True):
    # Return a list of start + end positions defining sub expressions of the given expression
    # Use for selecting a sub expression for extraction
    # Typically expect 'x = e' type expressions
    # include_names => whether to report single names

    # x = >(a + b) + f(x + 1)
    # (a + b) + f(x + 1)
    # (a + b)
    # a

    # x = (a + b) >+ f(x + 1)
    # f(x + 1)
    # f

    # case: x, *y, z = e
    # case: multiline
    # case: [el]if (a and b) ...
    # case: for x,y,z in e:

    def eligible(n):
        return n.type not in ['operator', 'trailer', 'expr_stmt', 'keyword']

    # TODO
    if column is None:
        raise ValueError('Not Handled')

    # Find the target position
    start_leaf = script._module_node.get_leaf_for_position((line, column))
    target = start_leaf

    # case: pos on an opening paren or keyword
    while not eligible(target):
        try:
            target = target.get_next_sibling().get_first_leaf()
        except AttributeError:
            raise ValueError('No expression found')

    res = []

    # Traverse to the root recording eligible positions
    start_pos = (line, column)

    while target:
        if include_names or target.type != 'name':
            res += (target.start_pos, target.end_pos, target.get_code())

        if target.parent is None or start_pos > target.parent.start_pos or \
           not eligible(target.parent):
            if eligible(target):
                break
            else:
                target = start_leaf.get_next_sibling()
        else:
            target = target.parent

    return res


# Convert a definition a,b,c = e into the equivalent
# multi-line definitions.
# May introduce an extra variable if e cannot be destructured.
def unpack(script, line=None, column=None):
    pass


# TODO use consistent names
# TODO look for similar functions to reuse
def inline(script, line=None, column=None):
    """
    Replace a variable with its definition.
    This only has effect until the selected variable is reassigned.

    Any uses of `del` and `nonlocal` that refer to the inlined variable are removed.

    This cannot be used to inline default values for function parameters.

    :type script: api.Script
    :rtype: :class:`Refactoring`
    """

    def can_inline(definition):
        return search_ancestor(definition._name.tree_name, 'expr_stmt') is not None

    # Raises ValueError if position is invalid
    definitions = script.goto(line, column)

    if definitions == []:
        raise ValueError('No definition found at '+(line, column))
    elif len(definitions) > 1:
        raise ValueError('Could not resolve definition at '+(line, column))

    # aka the definition statement to be replaced
    # type: 'api.classes.Definition'
    stmt = definitions[0]

    if not can_inline(stmt):
        raise ValueError('Not eligible for inline')

    # TODO this would force the user to select only definitions
    # i.e. you can't select x in (x + 7) to inline the definition of x
    # assert stmt.is_definition()

    # TODO can the references be across multiple files?

    # By convention lines are numbered from 1
    stmt_index = stmt.line - 1
    stmt_code = script._code_lines[stmt_index]

    # Split the line into assignment and residue
    # E.g. a, b = 1, 2 --> a = 1, b = 2
    replace_expr, line_residue = _split_insertion_expr(stmt, stmt_code)

    # Definitions divided into those to replace within and those to remove.
    targets, remove = _target_definitions(script, stmt, line, column)

    # Perform replacements and convert to Refactoring object
    dct = Refactoring(_rename(targets, replace_expr))

    stmt_end_index = stmt._name.tree_name.parent.end_pos[0] - 1

    # Remove everything in remove, replace with line residue from above.
    dct.set_new_lines(script.path,
                      _cleanup_after_insertion(dct.new_lines(script.path), line_residue, stmt_index, remove,
                                               stmt_end_index))
    return dct


def _target_definitions(script, stmt, line, column):
    """
    :returns A pair of Definition lists (replace, remove), where replace should be replaced with
    the inlining expression, and remove should be removed from the final result.
    The original statement is always in 'remove'.
    """

    def def_in_del_stmt(d):
        return definition_name_is_in(d, 'del_stmt')

    def def_in_nl_stmt(d):
        return definition_name_is_in(d, 'nonlocal_stmt')

    # List of references to the chosen name in the same scope
    # Assumes that references is in same order as source file
    references = script.get_references(line, column)

    active_refs = []
    remove_refs = []

    # the line, if any, where original name is re-assigned
    reassign_line = 0
    # defined as: between closest assignment/definition of stmt until reassignment or del_stmt.
    in_active_scope = False
    for r in references:
        # skip to original definition
        # TODO perhaps need to check module name too
        if (r.line, r.column) == (stmt.line, stmt.column):
            in_active_scope = True
            remove_refs.append(r)
            continue

        # re-assignment may use original expr, e.g. x=x+1
        if reassign_line > 0 and r.line != reassign_line:
            break

        if in_active_scope:
            # mark a del statement
            if def_in_del_stmt(r):
                remove_refs.append(r)
                reassign_line = r.line
                # this terminates the scope, I think parso correctly accounts for this
                continue
            # mark a re-assignment
            elif r.is_definition():
                reassign_line = r.line
                # TODO also handle x+=1 here
                continue
            elif def_in_nl_stmt(r):
                remove_refs.append(r)
                continue
            else:
                active_refs.append(r)

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

    if len(stmt._name.assignment_indexes()) > 0:

        if '*' in lhs.get_code():
            raise ValueError('Cannot inline in the presence of a star expr')

        replace_expr = _extract_packed_assign(lhs.children, rhs.children, stmt._name.start_pos)

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


# args list of parso.python.tree.Name, Operator, Value, Expr
# return expr from rhs that is assigned to target_col
def _extract_packed_assign(lhs, rhs, target_pos):
    if len(lhs) != len(rhs):
        raise ValueError('Could not unpack assignment')

    for l, r in zip(lhs, rhs):
        if l.start_pos == target_pos:
            return r
        elif l.end_pos[1] > target_pos[1] and len(l.children) > 0:
            return _extract_packed_assign(l.children, r.children, target_pos)

    raise ValueError('Could not unpack assignment')


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
            assert (suffix[0].isspace() or suffix[0] == ')'), \
                'Split at non-whitespace char'

    return prefix + suffix


def _cleanup_after_insertion(replaced_lines, line_residue, line_index, remove_refs, index_end):

    remove_indices = {x.line - 1 for x in remove_refs}
    result = []
    for i, line in enumerate(replaced_lines):
        if i == line_index:
            if line_residue.strip():
                result.append(line_residue)
            else:
                continue
        elif line_index < i and i <= index_end:
            # drop all parts of a multiline statment
            continue
        elif i not in remove_indices:
            result.append(line)

    return result


# Candidates for addition to API

def definition_name_is_in(definition, stmt_type: str):
    return search_ancestor(definition._name.tree_name, stmt_type) is not None


def statement_type(definition):
    return definition._name.tree_name.parent.type


def tree_def(definition):
    # cf definition._name.tree_name
    return definition._name.tree_name.get_definition()
