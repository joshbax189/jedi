# --- simple
def test():
    #? 6 y
    x = a + b
    return x

# +++
def test():
    y = a + b
    x = y
    return x

# --- specify both points
def test():
    #? 6 y 16 9
    x = a + b
    return x

# +++
def test():
    y = a
    x = y + b
    return x

# --- simple
def test():
    #? 11 a
    return f(x + 1)

# +++
def test():
    a = f(x + 1)
    return a

# --- simple
def test():
    #? 35 a
    return test(100, (30 + b, c) + 1)

# +++
def test():
    a = 1
    return test(100, (30 + b, c) + a)


# --- simple #2
def test():
    #? 22 a
    return test(100, (30 + b, c) + 1)

# +++
def test():
    a = 30 + b
    return test(100, (a, c) + 1)


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
