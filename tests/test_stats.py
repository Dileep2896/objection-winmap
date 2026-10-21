import pytest

from objection_winmap.stats import cohort_split, diff_interval, wilson_interval


def test_wilson_known_values():
    assert wilson_interval(5, 10) == pytest.approx((0.23659, 0.76341), abs=0.0001)


def test_empty_and_extreme_intervals():
    assert wilson_interval(0, 0) == (0.0, 1.0)
    assert wilson_interval(0, 10)[0] == pytest.approx(0)
    assert wilson_interval(10, 10)[1] == pytest.approx(1)
    assert diff_interval(0, 0, 0, 0) == (-1.0, 1.0)


def test_newcombe_known_value_and_sign():
    # Newcombe formula, using Wilson bounds (0.319507, 0.806742),
    # (0.065915, 0.430093), gives these independently rounded limits.
    assert diff_interval(7, 12, 3, 16) == pytest.approx((0.03743, 0.65018), abs=0.0001)
    low, high = diff_interval(3, 16, 7, 12)
    reverse = diff_interval(7, 12, 3, 16)
    assert (low, high) == pytest.approx((-reverse[1], -reverse[0]))


@pytest.mark.parametrize("k,n", [(-1, 4), (5, 4), (0, -1)])
def test_invalid_counts(k, n):
    with pytest.raises(ValueError):
        wilson_interval(k, n)


def test_cohorts_ceil_ties_and_min_meetings():
    counts = {f"rep-{i}": (2, 4) for i in range(6)}
    counts["rookie"] = (2, 2)
    top, rest = cohort_split(counts)
    assert top == {"rep-0", "rep-1"}
    assert rest == {"rep-2", "rep-3", "rep-4", "rep-5"}
    assert cohort_split({}) == (set(), set())
    assert cohort_split({"solo": (1, 3)}) == ({"solo"}, set())
