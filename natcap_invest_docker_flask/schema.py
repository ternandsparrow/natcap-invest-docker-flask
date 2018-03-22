# generated from https://jsonschema.net/, using the following settings:
#   root ID = http://pollin8.org.au/pollination.json
#   Annotations
#     Infer title = False
#     Infer default = False
#     Infer examples = False
#     Infer descriptions = False
#   Object assertions
#     ADD'L properties = False
#   Array assertions
#     ADD'L properties = False
#   Number assertions
#     Use number, not integer = True
# Copy the "Plain" version from the jsonschema editor and paste it here. Make the following changes:
#   replace all the booleans to have an uppercase first letter for Python
#   remove everything from the 'geometry' objects except "$id" and "type", we'll use another module to validate that
schema = {
  "$id": "http://pollin8.org.au/pollination.json",
  "type": "object",
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "additionalProperties": False,
  "properties": {
    "farm": {
      "$id": "/properties/farm",
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "type": {
          "$id": "/properties/farm/properties/type",
          "type": "string"
        },
        "features": {
          "$id": "/properties/farm/properties/features",
          "type": "array",
          "additionalItems": False,
          "items": {
            "$id": "/properties/farm/properties/features/items",
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "type": {
                "$id": "/properties/farm/properties/features/items/properties/type",
                "type": "string"
              },
              "properties": {
                "$id": "/properties/farm/properties/features/items/properties/properties",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "crop_type": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/crop_type",
                    "type": "string"
                  },
                  "half_sat": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/half_sat",
                    "type": "number"
                  },
                  "p_managed": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/p_managed",
                    "type": "number"
                  },
                  "season": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/season",
                    "type": "string"
                  },
                  "fr_spring": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/fr_spring",
                    "type": "number"
                  },
                  "fr_summer": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/fr_summer",
                    "type": "number"
                  },
                  "fr_autumn": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/fr_autumn",
                    "type": "number"
                  },
                  "fr_winter": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/fr_winter",
                    "type": "number"
                  },
                  "n_cavity": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/n_cavity",
                    "type": "number"
                  },
                  "n_stem": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/n_stem",
                    "type": "number"
                  },
                  "n_ground": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/n_ground",
                    "type": "number"
                  },
                  "p_dep": {
                    "$id": "/properties/farm/properties/features/items/properties/properties/properties/p_dep",
                    "type": "number"
                  }
                }
              },
              "geometry": {
                "$id": "/properties/farm/properties/features/items/properties/geometry",
                "type": "object",
                # let python's geojson handle validation for this
              }
            }
          }
        }
      }
    },
    "reveg": {
      "$id": "/properties/reveg",
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "type": {
          "$id": "/properties/reveg/properties/type",
          "type": "string"
        },
        "properties": {
          "$id": "/properties/reveg/properties/properties",
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "id": {
              "$id": "/properties/reveg/properties/properties/properties/id",
              "type": "null"
            }
          }
        },
        "geometry": {
          "$id": "/properties/reveg/properties/geometry",
          "type": "object",
          # let python's geojson handle validation for this
        }
      }
    }
  }
}
