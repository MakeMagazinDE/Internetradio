from prog.display import get_rolling_text

def test_get_rolling_text_no_rolling_short():
    pos = 0
    test_string = "Hello World"
    text, pos = get_rolling_text(test_string, pos)
    assert text == "Hello World"
    assert pos == 0

    text, pos = get_rolling_text(test_string, pos)
    assert text == "Hello World"
    assert pos == 0

def test_get_rolling_text_no_rolling_long():
    pos = 0
    test_string = "Hello World for real"
    text, pos = get_rolling_text(test_string, pos)
    assert text == "Hello World for real"
    assert pos == 0

    text, pos = get_rolling_text(test_string, pos)
    assert text == "Hello World for real"
    assert pos == 0

def test_get_rolling_text_with_rolling():
    pos = 0
    test_string = "This is a rolling text"

    text, pos = get_rolling_text(test_string, pos)
    assert text == "This is a rolling te"
    assert pos == 1

    text, pos = get_rolling_text(test_string, pos)
    assert text == "his is a rolling tex"
    assert pos == 2

    text, pos = get_rolling_text(test_string, pos)
    assert text == "is is a rolling text"
    assert pos == 3

    text, pos = get_rolling_text(test_string, pos)
    assert text == "This is a rolling te"
    assert pos == 1
