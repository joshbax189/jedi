# --- Default to end of line
def test():
    #? 8 y
    x = (a + 1) + b + f(c + 1)
    return x

# +++
def test():
    y = (a + 1) + b + f(c + 1)
    x = y
    return x

# --- specify both points
def test():
    #? 8 y 9
    x = a + b
    return x

# +++
def test():
    y = a
    x = y + b
    return x

# --- Default to end of line 2
def test():
    #? 11 a
    return f(x + 1)

# +++
def test():
    a = f(x + 1)
    return a

# --- Sub expr
def test():
    #? 35 a 36
    return test(100, (30 + b, c) + 1)

# +++
def test():
    a = 1
    return test(100, (30 + b, c) + a)


# --- simple #2
def test():
    #? 22 a 28
    return test(100, (30 + b, c) + 1)

# +++
def test():
    a = 30 + b
    return test(100, (a, c) + 1)

# --- function args
def test():
    #? 16 a 22
    return test((0, 1))

# +++
def test():
    a = (0, 1)
    return test(a)

# --- multiline
def test():
    #? 30 x
    return test(1, (30 + b, c)
                            + 1)
# +++
def test():
    x = ((30 + b, c)
                            + 1)
    return test(1, x
)


# --- multiline #2
def test():
    #? 25 x
    return test(1, (30 + b, c)
                            + 1)
# +++
def test():
    x = 30 + b
    return test(1, (x, c)
                            + 1)
