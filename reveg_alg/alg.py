"""
The algorithm that models the effect that revegetation has on the nesting and
floral resources over time.

To see a chart of this curve over time, run the server and GET /reveg-curve.png

See the README.md in this directory for where the formulae came from.
"""
from math import sin


def compute_fr(year, magic):
    if year > 25:
        return compute_fr(25, magic)
    return (sin((year + 13.5) / -8) + 1) / magic


def get_values_for_year(year):
    return {
        'nesting_cavity': compute_fr(year, 3.2),
        'nesting_ground': 0.31 + (3 / ((year / 0.9) + 6)),
        'fr_summer': compute_fr(year, 2.4),
        'fr_spring': compute_fr(year, 2),
    }
