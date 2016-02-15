a = 3  # type: str
#? str()
a

b = 3  # type: str but I write more
#? int()
b

c = 3  # type: str # I comment more
#? str()
c

d = "It should not read comments from the next line"
# type: int
#? str()
d

# type: int
e = "It should not read comments from the previous line"
#? str()
e

class BB: pass

def test(a, b):
    a = a  # type: BB
    c = a  # type: str
    d = a
    # type: str
    e = a                 # type: str           # Should ignore long whitespace

    #? BB()
    a
    #? str()
    c
    #? BB()
    d
    #? str()
    e
