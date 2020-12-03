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

f_items = "/properties/farm/properties/features/items"
r_items = "/properties/reveg/properties/features/items"

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
        "varroa_mite_year": {
            "$id": "/properties/varroa_mite_year",
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
                # TODO support supplying a CRS. Our code supports it but only
                # to run the official NatCap sample data. Also add it for
                # reveg.
                "features": {
                    "$id": "/properties/farm/properties/features",
                    "type": "array",
                    "additionalItems": False,
                    "items": {
                        "$id": f_items,
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "type": {
                                "$id":
                                f"{f_items}/properties/type",
                                "type": "string"
                            },
                            "properties": {
                                # technically GeoJSON requires this field, but
                                # we set it all server side
                                "$id":
                                f"{f_items}/properties/properties",
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {}
                            },
                            "geometry": {
                                "$id":
                                f"{f_items}/properties/geometry",
                                "type": "object",
                                # let python's geojson handle validation
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
                        "$id": r_items,
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "type": {
                                "$id":
                                f"{r_items}/properties/type",
                                "type": "string"
                            },
                            "properties": {
                                # technically GeoJSON requires this field, but
                                # we set it all server side
                                "$id":
                                f"{r_items}/properties/properties",
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {}
                            },
                            "geometry": {
                                "$id":
                                f"{r_items}/properties/geometry",
                                "type": "object",
                                # let python's geojson handle validation
                            }
                        }
                    }
                }
            }
        }
    }
}
