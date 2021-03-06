"""
Test of keywords and ``jedi.keywords``
"""

import pytest


def test_goto_keyword(Script):
    """
    Bug: goto assignments on ``in`` used to raise AttributeError::

      'unicode' object has no attribute 'generate_call_path'
    """
    Script('in').goto()


def test_keyword(Script, environment):
    """ github jedi-vim issue #44 """
    defs = Script("print").infer()
    if environment.version_info.major < 3:
        assert defs == []
    else:
        assert [d.docstring() for d in defs]

    assert Script("import").goto() == []

    completions = Script("import").complete(1, 1)
    assert len(completions) > 10 and 'if' in [c.name for c in completions]
    assert Script("assert").infer() == []


def test_keyword_attributes(Script):
    def_, = Script('def').complete()
    assert def_.name == 'def'
    assert def_.complete == ''
    assert def_.is_keyword is True
    assert def_.is_stub() is False
    assert def_.goto(only_stubs=True) == []
    assert def_.goto() == []
    assert def_.infer() == []
    assert def_.parent() is None
    assert def_.docstring()
    assert def_.description == 'keyword def'
    assert def_.get_line_code() == ''
    assert def_.full_name is None
    assert def_.line is def_.column is None
    assert def_.in_builtin_module() is True
    assert def_.module_name in ('builtins', '__builtin__')
    assert 'typeshed' in def_.module_path
    assert def_.type == 'keyword'


def test_none_keyword(Script, environment):
    if environment.version_info.major == 2:
        # Just don't care about Python 2 anymore, it's almost gone.
        pytest.skip()

    none, = Script('None').complete()
    assert not none.docstring()
    assert none.name == 'None'
