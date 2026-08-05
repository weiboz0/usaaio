"""Generate the original text corpus for mock test r1-001, Problem 5."""

from pathlib import Path
import random


SEED = 20260806

PASSAGES = [
    (
        "Before spring sunrise, Mara opened the blue shutters of the map shop. "
        "She penciled new sandbars beside the north channel while bakery carts "
        "rattled toward the quay. Young deckhands compared knots outside, and "
        "gulls inspected every basket as if appointed by the mayor."
    ),
    (
        "By midsummer, visitors filled the harbor steps with striped towels and "
        "paper cups. Ferries carried gardeners, musicians, and crates of silver "
        "fish across the bay. At noon the stone lanes smelled of citrus peel, "
        "warm rope, and rain drying on painted doors."
    ),
    (
        "Autumn brought patient fog and the pear harvest. Shopkeepers rolled "
        "canvas awnings tight before the western squalls, then traded weather "
        "reports over soup. Each captain left a chalk mark on the public board: "
        "wind east, channel clear, lantern repaired."
    ),
    (
        "In winter, only the mail boat crossed at dawn. Children followed its "
        "wake from the seawall, counting seals between the black rocks. Inside "
        "the library, retired sailors repaired atlases and argued cheerfully "
        "about which vanished pier had served the finest tea."
    ),
    (
        "Every market morning, Niko arranged jars of plum jam in three careful "
        "rows. Every market morning, the cooper next door swept cedar curls into "
        "a copper pan. Their routines looked identical until storm days, when "
        "both abandoned their stalls to help fasten the fishing boats."
    ),
    (
        "The town kept two calendars. One hung in the council room and named "
        "holidays; the other lived in conversation and named the first mackerel, "
        "the last tourist, the loudest thunder, and the evening when everyone "
        "finally needed a wool coat."
    ),
    (
        "At dusk, lamps appeared one by one along Lantern Quay. At dusk, lamps "
        "appeared one by one along Lantern Quay. Neighbors paused beneath them "
        "to exchange keys, recipes, and small pieces of news before the bell "
        "sent each household uphill."
    ),
]

REFRAIN = "The tide ledger remembered what the crowd forgot."


def generate_corpus() -> str:
    """Return the deterministic passage, including deliberate repetitions."""
    rng = random.Random(SEED)
    passages = PASSAGES.copy()
    rng.shuffle(passages)
    passages.insert(2, REFRAIN)
    passages.insert(5, REFRAIN)
    passages.append(REFRAIN)
    return "\n\n".join(passages) + "\n"


def main() -> None:
    output_path = Path(__file__).with_name("corpus.txt")
    output_path.write_text(generate_corpus(), encoding="utf-8")


if __name__ == "__main__":
    main()
