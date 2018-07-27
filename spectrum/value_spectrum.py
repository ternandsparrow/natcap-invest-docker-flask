#!/usr/bin/python3
# Runs all permutations and logs the results. Good for getting a feel about how the inputs affect the output
# Run with:
#   python3 value_spectrum.py > output.csv

import requests
import json
import sys

def permute_inputs():
  url = 'http://localhost:5000/pollination?years=0'
  with sys.stdout as out, sys.stderr as err:
    out.write('half_sat,p_managed,fr_spring,fr_summer,fr_autumn,fr_winter,n_cavity,n_stem,n_ground,p_dep,p_abund,pdep_y_w,y_tot,y_wild\n')
    def do_http_call(data, row_num):
      resp = requests.post(url, headers={'Accept': 'application/json'}, json=data)
      if resp.status_code != 200:
        err.write('HTTP call failed with status code = %d\n' % resp.status_code)
        error_file = '/tmp/natcap-error.html'
        with open(error_file, 'w') as f:
          f.write(resp.text)
        err.write('wrote error output to %s\n' % error_file)
        exit()

      resp_body = resp.json()
      rec = resp_body['records'][0]
      err.write('processing row %d\n' % row_num)
      out.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%f,%f,%f,%f\n' % (
        rec['half_sat'], rec['p_managed'], rec['fr_spring'], rec['fr_summer'], rec['fr_autumn'], rec['fr_winter'], rec['n_cavity'],
        rec['n_stem'], rec['n_ground'], rec['p_dep'], rec['p_abund'], rec['pdep_y_w'], rec['y_tot'], rec['y_wild']))
      out.flush()
    for_each_permutation(do_http_call)


def for_each_permutation(callback):
  row_counter = 1
  step = 33 # smaller values mean an explosion of permutations
  for curr_half_sat in range(0, 101, step):
    for curr_p_managed in range(0, 101, step):
      for curr_fr in range(0, 101, step):
        for curr_n in range(0, 101, step):
          for curr_p_dep in range(0, 101, step):
            half_sat = curr_half_sat / 100 or 0.01
            p_managed = curr_p_managed / 100 or 0.01
            fr_spring = curr_fr / 100 or 0.01
            fr_summer = curr_fr / 100 or 0.01
            fr_autumn = curr_fr / 100 or 0.01
            fr_winter = curr_fr / 100 or 0.01
            n_cavity = curr_n / 100 or 0.01
            n_stem = curr_n / 100 or 0.01
            n_ground = curr_n / 100 or 0.01
            p_dep = curr_p_dep / 100 or 0.01
            # print('%.1f %.1f %.1f %.1f %.1f %.1f %.1f %.1f %.1f %.1f' % (
            #   half_sat, p_managed, fr_spring, fr_summer, fr_autumn, fr_winter, n_cavity, n_stem, n_ground, p_dep))
            data = get_data(half_sat, p_managed, fr_spring, fr_summer,
              fr_autumn, fr_winter, n_cavity, n_stem, n_ground, p_dep)
            callback(data, row_counter)
            row_counter += 1



def get_data(half_sat, p_managed, fr_spring, fr_summer, fr_autumn, fr_winter, n_cavity, n_stem, n_ground, p_dep):
  return {
    "farm": {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {
            "crop_type": "canola",
            "half_sat": half_sat,
            "p_managed": p_managed,
            "season": "summer",
            "fr_spring": fr_spring,
            "fr_summer": fr_summer,
            "fr_autumn": fr_autumn,
            "fr_winter": fr_winter,
            "n_cavity": n_cavity,
            "n_stem": n_stem,
            "n_ground": n_ground,
            "p_dep": p_dep
          },
          "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [
                  138.7976351232967,
                  -34.91457258034658
                ],
                [
                  138.78809242247843,
                  -34.9099008125332
                ],
                [
                  138.80525654750377,
                  -34.90863402266019
                ],
                [
                  138.78674319454652,
                  -34.90015396745101
                ],
                [
                  138.80292820051716,
                  -34.885391212669326
                ],
                [
                  138.81336158117088,
                  -34.904660062887984
                ],
                [
                  138.81360488755553,
                  -34.91344927305799
                ],
                [
                  138.7976351232967,
                  -34.91457258034658
                ]
              ]
            ]
          }
        }
      ]
    },
    "reveg": {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              138.8381214829456,
              -34.884585119806616
            ],
            [
              138.83812359941683,
              -34.86297820218762
            ],
            [
              138.84311529146916,
              -34.862721911365924
            ],
            [
              138.84396922110494,
              -34.88095005155782
            ],
            [
              138.85344290205637,
              -34.880946703445765
            ],
            [
              138.85358081628885,
              -34.88413143299829
            ],
            [
              138.8381214829456,
              -34.884585119806616
            ]
          ]
        ]
      }
    }
  }

if __name__ == "__main__":
  permute_inputs()