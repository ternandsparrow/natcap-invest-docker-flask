"""
Create a matplotlib chart of the reveg curve (how the values change over time)
"""
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from reveg_alg.alg import get_values_for_year


def generate_chart(max_years=15):
    """ Generate a chart and return the PNG bytes """
    years = range(0, max_years + 1)
    nesting_cavity = []
    nesting_ground = []
    fr_summer = []
    fr_spring = []

    for curr in years:
        val = get_values_for_year(curr)
        nesting_cavity.append(val['nesting_cavity'])
        nesting_ground.append(val['nesting_ground'])
        fr_summer.append(val['fr_summer'])
        fr_spring.append(val['fr_spring'])
    # thanks https://stackoverflow.com/a/50728936/1410035
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(years, nesting_cavity, label='nesting_cavity')
    axis.plot(years, nesting_ground, label='nesting_ground')
    axis.plot(years, fr_summer, label='fr_summer')
    axis.plot(years, fr_spring, label='fr_spring')

    axis.set(xlabel='years',
             ylabel='index value',
             title='Revegetation effectiveness')
    axis.grid()
    axis.legend()
    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return output
