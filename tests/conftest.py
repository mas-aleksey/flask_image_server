import os

import pytest
from app import create_app


TEST_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.dirname(TEST_DIR)
IMAGES_DIR = os.path.join(PROJECT_DIR, 'images')


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()
    testing_client = flask_app.test_client()
    ctx = flask_app.app_context()
    ctx.push()
    yield testing_client  # this is where the testing happens!
    ctx.pop()


@pytest.fixture
def images_dir():
    return IMAGES_DIR
