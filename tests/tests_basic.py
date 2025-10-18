def test_dummy():
    assert 1 + 1 == 2

def test_flask_import():
    import flask
    assert flask.__version__ is not None
