# --- simple usage
def test(b, c):
    #? 4
    a = (30 + b, c)
    return test(100, a)
# +++
def test(b, c):
    return test(100, (30 + b, c))

# --- semicolon statement
def test(x, y):
    #? 4
    a = (30 + x, y); b = 0
    return test(100, a, b)
# +++
def test(x, y):
    b = 0
    return test(100, (30 + x, y), b)

# --- variable reassignment 1
def test():
    #? 4
    x = 0
    x = x + 1
    return f(x)
# +++
def test():
    x = 0 + 1
    return f(x)

# --- variable reassignment 2
def test():
    x = 0
    #? 4
    x = x + 1
    return f(x)
# +++
def test():
    x = 0
    return f(x + 1)

# --- variable increment
def test():
    #? 4
    x = 0
    print(x)
    x += 1
    return x
# +++
def test():
    print(0)
    x = 0 + 1
    return x

# --- variable increment 2
def test(y):
    #? 4
    x = 5
    print(x)
    x //= (x + y)
    return x
# +++
def test(y):
    print(0)
    x = 5 // (5 + y)
    return x

# --- for loop variables cannot be inlined
def f():
    #? 8
    for i in range(1, 5):
        print(i)
# +++
#^ ValueError

# --- tuple assignment 1
def test():
    #? 4
    a = 1, 2
    return test(100, a)
# +++
def test():
    return test(100, (1, 2))

# --- tuple assignment 2
def test():
    #? 4
    a = (1, 2)
    return test(100, a)
# +++
def test():
    return test(100, (1, 2))

# --- single element tuple must remain a tuple
def test():
    #? 4
    a = 1,
    return test(100, a)
# +++
def test():
    return test(100, (1,))

# --- tuple unpacking 1
def test():
    #? 4
    a, b, c = 1, 2, 3
    return f(a, b, c, 1)
# +++
def test():
    b, c = 2, 3
    return f(1, b, c, 1)

# --- tuple unpacking 2
def test():
    #? 7
    a, b, c = 1, 2, 3
    return f(a, b, c, 1)
# +++
def test():
    a, c = 1, 3
    return f(a, 2, c, 1)

# --- cannot inline underscore variable
def test():
    #? 4
    _, b, c = [1, 2, 3]
    return test(100, b)
# +++
#^ ValueError

# --- nested tuple unpacking 1
def test():
    #? 4
    a, (b, c) = 1, (2, 3)
    return f(a, b, c, 1)
# +++
def test():
    (b, c) = (2, 3)
    return f(1, b, c, 1)

# --- nested tuple unpacking 2
def test():
    #? 11
    a, (b, c) = 1, (2, 3)
    return f(a, b, c, 1)
# +++
def test():
    a, (b, ) = 1, (2, )
    return f(a, b, 3, 1)

# --- failing tuple unpacking 1
def test():
    #? 4
    a, (b, c) = g()
    return f(a, b, c, 1)
# +++
#^ ValueError

# --- failing tuple unpacking 2
def test():
    #? 4
    a, *b, c = [0] * 5
    return f(a, b, c, 1)
# +++
#^ ValueError

# --- multi assignment 1
def test():
    #? 4
    a = b = 0
    return f(a, b, 1)
# +++
def test():
    b = 0
    return f(0, b, 1)

# --- multi assignment 2
def test():
    #? 8
    a = b = 0
    return f(a, b, 1)
# +++
def test():
    a = 0
    return f(a, 0, 1)

# --- name capture counter-example
def test(y):
    #? 4
    x = y + 1
    def g():
        y = -1
        print(x)
        print(y)
    return x
# +++
def test(y):
    def g():
        y = -1
        print(y + 1)
        print(y)
    return y + 1

# --- delete statement
def test():
    #? 4
    x = 123
    print(x)
    del x  # a comment

# +++
def test():
    print(123)
    # a comment

# --- delete statement 2
def test():
    #? 4
    x = 123
    y = 0
    print(x)
    del x, y  # a comment
# +++
def test():
    y = 0
    print(123)
    del y  # a comment

# --- nested scopes
def test():
    #? 4
    x = 1
    def g():
        x = 2
        print(x)
    print(x)
# +++
def test():
    def g():
        x = 2
        print(x)
    print(1)

# --- nested scopes with nonlocal
def test():
    #? 4
    x = 1
    def g():
        nonlocal x
        print(x)
    print(x)
# +++
def test():
    def g():
        print(1)
    print(1)

# --- lambda
def test():
    #? 4
    x = lambda y: y + 1
    return x(5)
# +++
def test():
    return (lambda y: y + 1)(5)

# --- multiline list
def test():
    #? 4
    x = [y for y in range(1,100)
         if y%5 == 0]
    return g(x[:5])
# +++
def test():
    return g([y for y in range(1,100)
         if y%5 == 0][:5])

# --- multiline string
def test():
    #? 4
    x = """aaa
aaa
aaa
"""
    return x + "z"
# +++
def test():
    return """aaa
aaa
aaa
""" + "z"

# --- multiline statement with semicolon
def test():
    #? 4
    x = 1 + 2 + 3 + \
        4 + 5 + 6; y = 5
    return x + y
# +++
def test():
    y = 5
    return 1 + 2 + 3 + \
           4 + 5 + 6 + y

# --- inline in lambda
def test():
    #? 4
    z = 1
    f1 = lambda x, y: x + y + z
    print(f1(10, 20))
# +++
def test():
    f1 = lambda x, y: x + y + 1
    print(f1(10, 20))

# --- double lambda 1
def test():
    #? 4
    f1 = lambda x, y: x + y
    f2 = lambda a, b: f1(a, b)
    print(f2(10, 20))
# +++
def test():
    f2 = lambda a, b: (lambda x, y: x + y)(a, b)
    print(f2(10, 20))
