import pytest

from app.auth import login_throttle


@pytest.fixture(autouse=True)
def _reset_login_throttle():
    """Failed-login counters are process-global; isolate them between tests."""
    login_throttle.reset()
    yield
    login_throttle.reset()
