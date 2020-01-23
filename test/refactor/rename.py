"""
Test coverage for renaming is mostly being done by testing
`Script.get_references`.
"""

# --- simple
def test1():
    #? 7 blabla
    test1()
    AssertionError
    return test1, test1.not_existing
# +++
def blabla():
    blabla()
    AssertionError
    return blabla, blabla.not_existing

# --- function params
def a_func(a_param):
    #? 12 new_param
    print a_param

a_func(a_param=10)
a_func(10)
# +++
def a_func(new_param):
    print new_param

a_func(new_param=10)
a_func(10)

# --- class attributes
class AClass(object):

    def __init__(self):
        #? 15 new_attr
        self.an_attr = 1

    def a_method(self, arg):
        print self.an_attr, arg

a_var = AClass()
a_var.a_method(a_var.an_attr)
# +++
class AClass(object):

    def __init__(self):
        self.new_attr = 1

    def a_method(self, arg):
        print self.new_attr, arg

a_var = AClass()
a_var.a_method(a_var.new_attr)
