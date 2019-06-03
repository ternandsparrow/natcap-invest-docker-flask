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
# Copy the "Plain" version from the jsonschema editor and paste it here. Make
# the following changes:
#   replace all the booleans to have an uppercase first letter for Python
#   remove everything from the 'geometry' objects except "$id" and "type",
#   we'll use another module to validate that
schema = {
    "$id": "http://pollin8.org.au/pollination.json",
    "type": "object",
    "definitions": {},
    "$schema": "http://json-schema.org/draft-07/schema#",
    "additionalProperties": False,
    "properties": {
        "crop_type": {
            "$id": "/properties/crop_type",
            "type": "string"
        },
        "years": {
            "$id": "/properties/years",
            "type": "number"
        },
        "socketio_sid": {
            "$id": "/properties/socketio_sid",
            "type": "string"
        },
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
                                "$id":
                                "/properties/farm/properties/features/items/properties/type",
                                "type": "string"
                            },
                            "properties":
                            {  # technically GeoJSON requires this field, but we set it all server side
                                "$id":
                                "/properties/farm/properties/features/items/properties/properties",
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {}
                            },
                            "geometry": {
                                "$id":
                                "/properties/farm/properties/features/items/properties/geometry",
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
                "features": {
                    "$id": "/properties/reveg/properties/features",
                    "type": "array",
                    "additionalItems": False,
                    "items": {
                        "$id": "/properties/reveg/properties/features/items",
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "type": {
                                "$id":
                                "/properties/reveg/properties/features/items/properties/type",
                                "type": "string"
                            },
                            "properties":
                            {  # technically GeoJSON requires this field, but we set it all server side
                                "$id":
                                "/properties/reveg/properties/features/items/properties/properties",
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {}
                            },
                            "geometry": {
                                "$id":
                                "/properties/reveg/properties/features/items/properties/geometry",
                                "type": "object",
                                # let python's geojson handle validation for this
                            }
                        }
                    }
                }
            }
        }
    }
}
