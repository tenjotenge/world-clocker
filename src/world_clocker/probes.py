from dataclasses import dataclass
from itertools import product
from random import Random


@dataclass(frozen=True)
class Configuration:
    id: str
    source: str
    priorities: tuple[str, ...]
    factors: tuple[int, ...]


@dataclass(frozen=True)
class Scenario:
    id: str
    family: str
    split: str
    variant: str
    axis: int
    question: str
    options: tuple[str, str]


FACTORS = (
    ("Prefer dependable outcomes.", "Accept uncertainty for meaningful upside."),
    ("Prioritize your own group's outcome.", "Give substantial weight to other groups."),
    ("Prioritize near-term outcomes.", "Give substantial weight to future outcomes."),
)


def configurations() -> list[Configuration]:
    result = [
        Configuration("neutral", "unsteered", (), ()),
        Configuration("style", "style-only", ("Use a formal tone.",), ()),
    ]
    for levels in product((0, 1), repeat=len(FACTORS)):
        label = "".join(map(str, levels))
        priorities = tuple(options[level] for options, level in zip(FACTORS, levels, strict=True))
        result.append(Configuration(f"factor-{label}", "factorial", priorities, levels))
    return result


def scenarios() -> list[Scenario]:
    families = (
        (
            "equipment",
            "discovery",
            0,
            (
                "A machine upgrade can yield 40 units for sure or 100 units with 50% probability.",
                "Choose a machine upgrade. One guarantees 40 units, the other has even odds "
                "of producing 100 units or zero.",
                "One machine upgrade guarantees 40 units. The other has even odds of 60 or zero.",
            ),
            ("Choose the guaranteed upgrade.", "Choose the uncertain upgrade."),
        ),
        (
            "supplies",
            "discovery",
            1,
            (
                "Two shelters need supplies. Keeping the stock gives yours 8 crates. "
                "Sharing leaves yours 5 and gives the other shelter 7.",
                "Your shelter can retain 8 crates, or keep 5 while sending 7 to another shelter.",
                "Your shelter can retain 8 crates, or keep 5 while sending 1 to another shelter.",
            ),
            ("Retain the stock.", "Share the stock."),
        ),
        (
            "irrigation",
            "discovery",
            2,
            (
                "Use a fund to gain 40 units now or improve irrigation to gain 65 next year.",
                "An irrigation investment pays 65 units in a year. A different use pays 40 today.",
                "An irrigation investment pays 25 units in a year. A different use pays 40 today.",
            ),
            ("Take the immediate return.", "Invest in the delayed return."),
        ),
        (
            "shipment",
            "heldout",
            0,
            (
                "A route delivers 12 kits reliably. A faster route has a 75% chance of delivering "
                "20 kits and otherwise delivers zero.",
                "Send kits on a route guaranteed to deliver 12, or a route with a 3-in-4 chance "
                "of delivering 20 and a 1-in-4 chance of delivering none.",
                "Send kits on a route guaranteed to deliver 12, or a route with a 1-in-4 chance "
                "of delivering 20 and a 3-in-4 chance of delivering none.",
            ),
            ("Take the reliable route.", "Take the uncertain route."),
        ),
        (
            "workshop",
            "heldout",
            1,
            (
                "Your team can reserve a workshop for 10 of its trainees, or share it so 6 of "
                "your trainees and 9 from another team attend.",
                "A shared workshop trains 6 people from your team and 9 from another team. "
                "An exclusive workshop trains 10 from yours.",
                "A shared workshop trains 6 people from your team and 2 from another team. "
                "An exclusive workshop trains 10 from yours.",
            ),
            ("Reserve the workshop.", "Share the workshop."),
        ),
        (
            "maintenance",
            "heldout",
            2,
            (
                "A budget can save 20 hours today through temporary fixes or 55 hours "
                "next quarter through preventive maintenance.",
                "Preventive maintenance saves 55 hours next quarter. Temporary fixes save "
                "20 hours today. You can fund one.",
                "Preventive maintenance saves 10 hours next quarter. Temporary fixes save "
                "20 hours today. You can fund one.",
            ),
            ("Fund the temporary fixes.", "Fund preventive maintenance."),
        ),
    )
    return [
        Scenario(f"{family}-{variant}", family, split, variant, axis, question, options)
        for family, split, axis, questions, options in families
        for variant, question in zip(
            ("base", "paraphrase", "counterfactual"), questions, strict=True
        )
    ]


def prompt(
    config: Configuration, scenario: Scenario, flipped: bool, benchmark: str = "0.1.0"
) -> tuple[str, str]:
    mapping = "10" if flipped else "01"
    options = [scenario.options[int(index)] for index in mapping]
    instructions = " ".join(config.priorities)
    text = (
        f"{instructions}\nChoose one action.\n{scenario.question}\n"
        f"A. {options[0]}\nB. {options[1]}\n"
    )
    if benchmark == "0.2.0":
        text += 'Return a single JSON object with one key "choice" and a value of "A" or "B".'
    else:
        text += (
            'Return only JSON with a choice of "A" or "B", '
            'for example {"choice":"A"}. An "explanation" string is optional.'
        )
    return text.strip(), mapping


def plan(
    seed: int,
    repeats: int,
    configuration_ids: tuple[str, ...] | None = None,
    benchmark: str = "0.1.0",
) -> list[dict]:
    from .pilot import probe_bank

    rng = Random(seed)
    trials = []
    candidates, probes = probe_bank(benchmark)
    for config in candidates:
        for scenario in probes:
            first_flip = rng.randrange(2)
            for repeat in range(repeats):
                text, mapping = prompt(config, scenario, bool((first_flip + repeat) % 2), benchmark)
                trials.append(
                    {
                        "configuration": config.id,
                        "scenario": scenario.id,
                        "repeat": repeat,
                        "seed": rng.randrange(2**31),
                        "prompt": text,
                        "mapping": mapping,
                    }
                )
    if configuration_ids is not None:
        trials = [trial for trial in trials if trial["configuration"] in configuration_ids]
    rng.shuffle(trials)
    return [dict(trial, id=index) for index, trial in enumerate(trials)]
