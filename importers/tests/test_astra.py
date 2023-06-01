import os

import pytest

from ..models import Product, ImportResult
from ..astra import AstraParser


def abspath(filename):
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, filename)


@pytest.fixture
def sample_xml_file(filename="export_sample.xml"):
    return abspath(filename)


@pytest.fixture
def sample_zip_file(filename="export_sample.zip"):
    return abspath(filename)


@pytest.fixture
def expected_result():
    return ImportResult(
        products=[
            Product(code="P1", name="Dummy Product 1", spare_part_codes=[]),
            Product(code="P2", name="Dummy Product 2", spare_part_codes=["P1", "P3"]),
        ]
    )


def test_parsing_xml_file(sample_xml_file, expected_result):
    result = AstraParser().parse_xml(sample_xml_file)
    assert result == expected_result


def test_parsing_zip_archive(sample_zip_file, expected_result):
    result = AstraParser().process_archive(sample_zip_file)
    assert result == expected_result
