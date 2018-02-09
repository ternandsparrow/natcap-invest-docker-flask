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
      "title": "The Type Schema",
      "description": "An explanation about the purpose of this instance.",
      "default": "",
      "examples": [
        "FeatureCollection"
      ]
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
            "title": "The Type Schema",
            "description": "An explanation about the purpose of this instance.",
            "default": "",
            "examples": [
              "Feature"
            ]
          },
          "properties": {
            "$id": "/properties/features/items/properties/properties",
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "crop_type": {
                "$id": "/properties/features/items/properties/properties/properties/crop_type",
                "type": "string",
                "title": "The Crop_type Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": "",
                "examples": [
                  "almonds"
                ]
              },
              "half_sat": {
                "$id": "/properties/features/items/properties/properties/properties/half_sat",
                "type": "number",
                "title": "The Half_sat Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": 0,
                "examples": [
                  0.6000000238418579
                ]
              },
              "p_managed": {
                "$id": "/properties/features/items/properties/properties/properties/p_managed",
                "type": "number",
                "title": "The P_managed Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": 0,
                "examples": [
                  0.8999999761581421
                ]
              },
              "season": {
                "$id": "/properties/features/items/properties/properties/properties/season",
                "type": "string",
                "title": "The Season Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": "",
                "examples": [
                  "spring"
                ]
              },
              "fr_spring": {
                "$id": "/properties/features/items/properties/properties/properties/fr_spring",
                "type": "number",
                "title": "The Fr_spring Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": 0,
                "examples": [
                  1
                ]
              },
              "fr_summer": {
                "$id": "/properties/features/items/properties/properties/properties/fr_summer",
                "type": "number",
                "title": "The Fr_summer Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": 0,
                "examples": [
                  0.10000000149011612
                ]
              },
              "n_cavity": {
                "$id": "/properties/features/items/properties/properties/properties/n_cavity",
                "type": "number",
                "title": "The N_cavity Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": 0,
                "examples": [
                  0.8999999761581421
                ]
              },
              "n_ground": {
                "$id": "/properties/features/items/properties/properties/properties/n_ground",
                "type": "number",
                "title": "The N_ground Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": 0,
                "examples": [
                  0.10000000149011612
                ]
              },
              "p_dep": {
                "$id": "/properties/features/items/properties/properties/properties/p_dep",
                "type": "number",
                "title": "The P_dep Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": 0,
                "examples": [
                  0.6499999761581421
                ]
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
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "type": {
                "$id": "/properties/features/items/properties/geometry/properties/type",
                "type": "string",
                "title": "The Type Schema",
                "description": "An explanation about the purpose of this instance.",
                "default": "",
                "examples": [
                  "Polygon"
                ]
              },
              "coordinates": {
                "$id": "/properties/features/items/properties/geometry/properties/coordinates",
                "type": "array",
                "additionalItems": False,
                "items": {
                  "$id": "/properties/features/items/properties/geometry/properties/coordinates/items",
                  "type": "array",
                  "additionalItems": False,
                  "items": {
                    "$id": "/properties/features/items/properties/geometry/properties/coordinates/items/items",
                    "type": "array",
                    "additionalItems": False,
                    "items": {
                      "$id": "/properties/features/items/properties/geometry/properties/coordinates/items/items/items",
                      "type": "number",
                      "title": "The 0 Schema",
                      "description": "An explanation about the purpose of this instance.",
                      "default": 0,
                      "examples": [
                        476012.21875
                      ]
                    }
                  }
                }
              }
            },
            "required": [
              "type",
              "coordinates"
            ]
          }
        },
        "required": [
          "type",
          "properties",
          "geometry"
        ]
      }
    },
    "crs": {
      "$id": "/properties/crs",
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "type": {
          "$id": "/properties/crs/properties/type",
          "type": "string",
          "title": "The Type Schema",
          "description": "An explanation about the purpose of this instance.",
          "default": "",
          "examples": [
            "name"
          ]
        },
        "properties": {
          "$id": "/properties/crs/properties/properties",
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "name": {
              "$id": "/properties/crs/properties/properties/properties/name",
              "type": "string",
              "title": "The Name Schema",
              "description": "An explanation about the purpose of this instance.",
              "default": "",
              "examples": [
                "urn:ogc:def:crs:EPSG::26910"
              ]
            }
          },
          "required": [
            "name"
          ]
        }
      },
      "required": [
        "type",
        "properties"
      ]
    }
  },
  "required": [
    "type",
    "features",
    "crs"
  ]
}
