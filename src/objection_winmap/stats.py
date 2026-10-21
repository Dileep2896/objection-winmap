from math import ceil, sqrt


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n < 0 or not 0 <= k <= n or z <= 0:
        raise ValueError("Require 0 <= successes <= trials and z > 0.")
    if not n:
        return 0.0, 1.0
    p = k / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    radius = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def diff_interval(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Newcombe hybrid score interval using independent Wilson intervals."""
    l1, u1 = wilson_interval(k1, n1)
    l2, u2 = wilson_interval(k2, n2)
    if not n1 or not n2:
        return -1.0, 1.0
    p1, p2 = k1 / n1, k2 / n2
    gap = p1 - p2
    return (
        max(-1.0, gap - sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)),
        min(1.0, gap + sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)),
    )


def cohort_split(counts: dict[str, tuple[int, int]]) -> tuple[set[str], set[str]]:
    """Rank eligible reps by overall rate; equal rates break by stable rep ID.

    Reps below three meetings belong to neither comparison cohort.
    """
    eligible = [rep for rep, (_, n) in counts.items() if n >= 3]
    eligible.sort(key=lambda rep: (-counts[rep][0] / counts[rep][1], rep))
    size = max(1, ceil(len(eligible) * 0.2))
    return set(eligible[:size]), set(eligible[size:])
