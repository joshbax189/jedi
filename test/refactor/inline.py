# --- for loop counter-example
def f():
    #? 8
    for i in range(1,5):
        print(i)
# +++
#^ ValueError

# --- name capture counter-example
def f(y):
    #? 4
    x = y + 1
    def g():
        y = -1
        print(x)
        print(y)
    return x
# +++
def f(y):
    def g():
        y = -1
        print(y + 1)
        print(y)
    return y + 1
# --- simple
def test():
    #? 4
    a = (30 + b, c) + 1
    return test(100, a)
# +++
def test():
    return test(100, (30 + b, c) + 1)

# --- simple, with semicolon
def test():
    #? 4
    a = (30 + b, c) + 1; b = 0
    return test(100, a, b)
# +++
def test():
    b = 0
    return test(100, (30 + b, c) + 1, b)

# --- tuple packing
def testA():
    #? 4
    a = 1, 2
    return test(100, a)
# +++
def testA():
    return test(100, (1, 2))

# --- tuple packing 2
def testA():
    #? 4
    a = (1, 2)
    return test(100, a)
# +++
def testA():
    return test(100, (1, 2))

# --- single element tuple has type preserved
def testA():
    #? 4
    a = 1,
    return test(100, a)
# +++
def testA():
    return test(100, (1,))

# --- tuple assignment
def test():
    #? 4
    a, b, c = 1, 2, 3
    return f(a, b, c, 1)
# +++
def test():
    b, c = 2, 3
    return f(1, b, c, 1)

# --- tuple assignment 2
def test():
    #? 7
    a, b, c = 1, 2, 3
    return f(a, b, c, 1)
# +++
def test():
    a, c = 1, 3
    return f(a, 2, c, 1)

# --- nested tuple assignment
def test():
    #? 4
    a, (b, c) = 1, (2, 3)
    return f(a, b, c, 1)
# +++
def test():
    (b, c) = (2, 3)
    return f(1, b, c, 1)

# --- nested tuple assignment 2
def test():
    #? 11
    a, (b, c) = 1, (2, 3)
    return f(a, b, c, 1)
# +++
def test():
    a, b = 1, 2
    return f(a, b, 3, 1)

# --- failing tuple assignment
def test():
    #? 8
    a, (b, c) = [0] ^ 3
    return f(a, b, c, 1)
# +++
#^ ValueError

# --- failing tuple assignment 2
def test():
    #? 4
    a, *b, c = [0] ^ 5
    return f(a, b, c, 1)
# +++
#^ ValueError

# --- multi assignment
def test():
    #? 4
    a = b = 0
    return f(a, b, c, 1)
# +++
def test():
    b = 0
    return f(0, b, c, 1)

# --- multi assignment 2
def test():
    #? 8
    a = b = 0
    return f(a, b, c, 1)
# +++
def test():
    a = 0
    return f(a, 0, c, 1)

# --- multi use 1
def test():
    #? 4
    x = 0
    x = x + 1
    return f(x)
# +++
def test():
    x = 0 + 1
    return f(x)

# --- multi use 2
def test():
    x = 0
    #? 4
    x = x + 1
    return f(x)
# +++
def test():
    x = 0
    return f(x + 1)
# --- multi use 3
def f():
    #? 4
    x = 0
    print(x)
    x += 1
    return x
# +++
def f():
    x = 0
    print(0)
    x += 1
    return x
# --- existence of del x
def f():
    #? 4
    x = 123
    print(x)
    del x
# +++
def f():
    print(123)

# --- nested scopes
def f():
    #? 4
    x = 1
    def g():
        x = 2
        print(x)
    print(x)
# +++
def f():
    def g():
        x = 2
        print(x)
    print(1)

# --- nested scopes: nonlocal
def f():
    #? 4
    x = 1
    def g():
        nonlocal x
        print(x)
    print(x)
# +++
def f():
    def g():
        print(1)
    print(1)

# --- lambda
def f():
    #? 4
    x = lambda y: y + 1
    return x(5)
# +++
def f():
    return (lambda y: y + 1)(5)
# --- multiline list
def f():
    #? 4
    x = [y for y in range(1,100)
         if y%5 == 0]
    return g(x[:5])
# +++
def f():
    return g([y for y in range(1,100)
         if y%5 == 0][:5])
# --- multiline string
def f():
    x = """aaa
aaa
aaa
"""
    return x + "z"
# +++
def f():
    return """aaa
aaa
aaa
""" + "z"
# --- multiline statement
def f():
    x = 1 + 2 + 3 + \
        4 + 5 + 6; y = 5
    return (x) + y
# +++
def f():
    y = 5
    return (1 + 2 + 3 + \
            4 + 5 + 6) + y
