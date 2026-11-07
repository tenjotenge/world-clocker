from dataclasses import dataclass
from decimal import Decimal, localcontext


@dataclass(frozen=True)
class Calibration:
    version: int = 1
    minimum_population: int = 500
    reference_population: int = 40_000_000
    reference_repertoire: int = 40

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version != 1:
            raise ValueError("Unsupported calibration version")
        for name in ("minimum_population", "reference_population", "reference_repertoire"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 10**12:
                raise ValueError(f"{name} must be a positive integer no greater than 10^12")
        if self.reference_population <= self.minimum_population or self.reference_repertoire < 2:
            raise ValueError("Calibration needs increasing population anchors and repertoire >= 2")

    def normalized(self, repertoire: int) -> float:
        return max(0, repertoire - 1) / (self.reference_repertoire - 1)

    def population(self, repertoire: int) -> int:
        with localcontext() as context:
            context.prec = 32
            floor = Decimal(self.minimum_population)
            ratio = Decimal(self.reference_population) / floor
            score = Decimal(max(0, repertoire - 1)) / (self.reference_repertoire - 1)
            return round(floor * ratio**score)
