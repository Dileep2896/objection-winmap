import json
from collections import Counter
from pathlib import Path

from objection_winmap.agent import HeuristicObjectionAgent


def test_fixture_accuracy():
    labels = json.loads((Path(__file__).parents[1] / "seed/labels.json").read_text())
    confusion = Counter()
    correct = 0
    for label in labels:
        actual = HeuristicObjectionAgent.classify(label["text"])
        confusion[(label["objection"], actual)] += 1
        correct += actual == label["objection"]
    accuracy = correct / len(labels)
    assert accuracy >= 0.9, f"Accuracy {accuracy:.1%}; confusion (gold, predicted): {confusion}"
    # Negatives must not hide a classifier that misses a specific objection class.
    for objection in {label["objection"] for label in labels if label["objection"]}:
        total = sum(count for (gold, _), count in confusion.items() if gold == objection)
        assert confusion[(objection, objection)] / total >= 0.9, (
            f"Recall failed for {objection}: {confusion}"
        )
