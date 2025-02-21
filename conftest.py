import asyncio

import pytest

TESTING = False


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the session scope."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
