from dataclasses import dataclass, field


@dataclass
class Product:
    code: str
    name: str
    spare_part_codes: list[str] = field(default_factory=lambda: [])


@dataclass
class ImportResult:
    products: list[Product]
