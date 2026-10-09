import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--update-goldens",
        action="store_true",
        default=False,
        help="Overwrite *.expected.jsonl with current pipeline output.",
    )


@pytest.fixture
def update_goldens(request):
    return request.config.getoption("--update-goldens")
