# generated from https://jsonschema.net/
schema = {
  "$id": "http://example.com/example.json",
  "type": "object",
  "definitions": {},
  "$schema": "http://json-schema.org/draft-06/schema#",
  "additionalProperties": False,
  "properties": {
    "type": {
      "$id": "/properties/type",
      "type": "string",
      "enum": ["FeatureCollection"]
    },
    "features": {
      "$id": "/properties/features",
      "type": "array",
      "additionalItems": False,
      "items": {
        "$id": "/properties/features/items",
        "type": "object",
        "additionalProperties": False,
        "properties": {
          "type": {
            "$id": "/properties/features/items/properties/type",
            "type": "string",
            "enum": ["Feature"]
          },
          "properties": {
            "$id": "/properties/features/items/properties/properties",
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "crop_type": {
                "$id": "/properties/features/items/properties/properties/properties/crop_type",
                "type": "string",
              },
              "half_sat": {
                "$id": "/properties/features/items/properties/properties/properties/half_sat",
                "type": "number",
              },
              "p_managed": {
                "$id": "/properties/features/items/properties/properties/properties/p_managed",
                "type": "number",
              },
              "season": {
                "$id": "/properties/features/items/properties/properties/properties/season",
                "type": "string",
              },
              "fr_spring": {
                "$id": "/properties/features/items/properties/properties/properties/fr_spring",
                "type": "number",
              },
              "fr_summer": {
                "$id": "/properties/features/items/properties/properties/properties/fr_summer",
                "type": "number",
              },
              "n_cavity": {
                "$id": "/properties/features/items/properties/properties/properties/n_cavity",
                "type": "number",
              },
              "n_ground": {
                "$id": "/properties/features/items/properties/properties/properties/n_ground",
                "type": "number",
              },
              "p_dep": {
                "$id": "/properties/features/items/properties/properties/properties/p_dep",
                "type": "number",
              }
            },
            "required": [
              "crop_type",
              "half_sat",
              "p_managed",
              "season",
              "fr_spring",
              "fr_summer",
              "n_cavity",
              "n_ground",
              "p_dep"
            ]
          },
          "geometry": {
            "$id": "/properties/features/items/properties/geometry",
            "type": "object"
            # let python's geojson handle validation for this
          }
        },
        "required": [
          "type",
          "properties",
          "geometry"
        ]
      }
    }
  },
  "required": [
    "type",
    "features",
  ]
}
