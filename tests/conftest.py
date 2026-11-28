"""Shared pytest fixtures for DataDuck generator tests."""

from copy import deepcopy

import pytest

from generator.config import load_config
from generator.generate import generate_clean_data


@pytest.fixture
def generator_config():
    """Return an independent generator configuration."""
    config = deepcopy(load_config("configs/generator/default.json"))
    config["record_count"] = 100

    return config


@pytest.fixture
def clean_dataset(generator_config):
    """Return a reproducible clean test dataset."""
    return generate_clean_data(generator_config)
