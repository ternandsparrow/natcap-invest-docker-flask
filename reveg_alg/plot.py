"""
Run this script to produce a matplotlib plot of the reveg values against time
(years).

It will work with the same version of matplotlib as is used by the base Docker
image but other dependencies are missing so you *cannot* run this inside the
docker container.  Instead, do the following on your dev machine:
    virtualenv -p python2 .venv
    . .venv/bin/activate
    pip install 'matplotlib<3'
    python reveg_alg/plot.py
"""
import os
import sys
import matplotlib.pyplot as plt

sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from reveg_alg.alg import get_values_for_year  # noqa: E402

years = range(0, 15)
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

fig, ax = plt.subplots()
ax.plot(years, nesting_cavity, label='nesting_cavity')
ax.plot(years, nesting_ground, label='nesting_ground')
ax.plot(years, fr_summer, label='fr_summer')
ax.plot(years, fr_spring, label='fr_spring')

ax.set(xlabel='years',
       ylabel='index value',
       title='Revegetation effectiveness')
ax.grid()
ax.legend()

image_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'reveg.png'))
fig.savefig(image_path)
print(
    '[INFO] this figure has also be written to %s. It will be ignored by git.'
    % image_path)
plt.show()
