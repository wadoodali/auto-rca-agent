import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add an optional incident filter to pytest."""

    parser.addoption(
        "--incident",
        action="store",
        default=None,
        help="Run semantic evaluation for one incident ID.",
    )


@pytest.fixture
def incident_filter(request: pytest.FixtureRequest) -> str | None:
    """Return the requested incident ID, if one was provided."""

    return request.config.getoption("--incident")