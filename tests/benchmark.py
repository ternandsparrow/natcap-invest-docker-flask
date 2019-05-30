#!/usr/bin/env python3
# performs a benchmark against the a live service to see how the number of
# years impacts the elapsed runtime (in milliseconds)
import requests

body = {
    "crop_type": "apple",
    "years": 3,
    "farm": {
        "type":
        "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type":
                "Polygon",
                "coordinates": [[[138.81568908691406, -34.88888795032023],
                                 [138.86469841003418, -34.89550563374408],
                                 [138.82899284362793, -34.86205975394847],
                                 [138.81568908691406, -34.88888795032023]]]
            }
        }]
    },
    "reveg": {
        "type":
        "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type":
                "Polygon",
                "coordinates": [[[138.81568908691406, -34.888958354012935],
                                 [138.81208419799805, -34.89578722546953],
                                 [138.8631534576416, -34.90170042871544],
                                 [138.86444091796875, -34.89564642972747],
                                 [138.81568908691406, -34.888958354012935]]]
            }
        }]
    }
}

headers = {'accept': 'application/json'}

print('years,elapsed_ms')
for curr_years in range(1, 20):
    body['years'] = curr_years
    resp = requests.post('http://localhost:5000/pollination',
                         json=body,
                         headers=headers)
    elapsed = resp.json()['elapsed_ms']
    print('%d,%d' % (curr_years, elapsed))
