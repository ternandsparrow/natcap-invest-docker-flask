"""
The algorithm that models the effect that revegetation has on the nesting and
floral resources over time.

To see a chart of this, look in (and run) the ./plot.py script.
"""


def c(v):
    return min(max(v, 0.0), 1.0)


def get_values_for_year(year):
    def compute_seed(year):
        if year < 5:
            return 0.01
        elif year >= 5 and year < 10:
            return year * 0.095
        return 0.95

    val = compute_seed(year)
    # FIXME handle separate fields correctly
    return {
        'nesting_cavity': c(val - 0.1),
        'nesting_ground': c(val - 0.2),
        'fr_summer': c(val),
        'fr_spring': c(val + 0.1),
    }
