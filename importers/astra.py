import io
import zipfile
import xml.etree.ElementTree as ET

import requests

from .models import Product, ImportResult


ARCHIVE_URL = "https://www.retailys.cz/wp-content/uploads/astra_export_xml.zip"


class AstraImporter:
    def run(self, archive_url=ARCHIVE_URL):
        response = requests.get(archive_url)
        return AstraParser().process_archive(io.BytesIO(response.content))


class AstraParser:
    def process_archive(self, file):
        with zipfile.ZipFile(file, "r") as zip_file:
            export_str = zip_file.read("export_full.xml").decode("utf-8")
            return self.parse_xml(io.StringIO(export_str))

    def parse_xml(self, file_or_filepath):
        tree = ET.parse(file_or_filepath)
        root = tree.getroot()
        product_elems = root.findall("./items/item")
        return ImportResult(products=[self._parse_product(el) for el in product_elems])

    def _parse_product(self, elem):
        spare_parts = []
        part_elems = elem.findall("parts/part[@categoryId='1']/item")
        spare_parts = [self._parse_product_code(el) for el in part_elems]
        return Product(
            code=elem.attrib["code"],
            name=elem.attrib["name"],
            spare_part_codes=spare_parts,
        )

    def _parse_product_code(self, elem):
        return elem.attrib["code"]
