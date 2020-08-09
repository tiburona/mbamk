from flask import current_app


def debug():
    assert current_app.debug is False, "Don't panic! You're here by request of debug()"
