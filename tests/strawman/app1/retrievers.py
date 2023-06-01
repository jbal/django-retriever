"""App retriever classes."""

from retriever import Retriever

from .models import Image, Location, Product, State


def _first(value):
    if value:
        return value[0]


class LocationRetriever(Retriever):
    def _phone(value):
        temp = ""

        for c in value:
            if c.isdigit():
                temp += c

        return temp

    model = Location
    id = ["id"]
    structures = [
        {
            "output": [
                ["stloc_identifier", [], ["id", int]],
                ["name", [], ["name", None]],
                ["address", [], ["street", None]],
                ["city", [], ["city", None]],
                ["zip", [], ["postal_code", None]],
                ["phone", [], ["phone_number", _phone]],
                ["url_key", [], ["uri", None]],
            ]
        }
    ]


class StateRetriever(Retriever):
    def _bool(value):
        if value in ["true", "True", "on", "On", "1", 1]:
            return True
        elif value in ["false", "False", "off", "Off", "0", 0]:
            return False

    model = State
    id = ["product_id", "location_id"]
    structures = [
        {
            "results": [
                {
                    "raw": [
                        [
                            "ec_skus",
                            [Product, ["id"], ["product_id"], ["sku", _first]],
                            [],
                        ],
                        ["is_buyable", [], ["is_buyable", _bool]],
                        [
                            "stores_low_stock_combined",
                            [],
                            ["is_low_stock_combined", _bool],
                        ],
                        [
                            "out_of_stock_threshold",
                            [],
                            ["out_of_stock_threshold", None],
                        ],
                        [
                            "low_stock_threshold",
                            [],
                            ["low_stock_threshold", None],
                        ],
                        ["out_of_stock", [], ["is_available", _bool]],
                        [
                            "is_stock_combined",
                            [],
                            ["stores_stock_combined", _bool],
                        ],
                        ["is_deficient", [], ["stores_low_stock", _bool]],
                        ["stores_stock", [], ["is_stocked", _bool]],
                        ["stores_inventory", [], ["quantity", int]],
                        [
                            "online_inventory",
                            [],
                            ["deliverable_quantity", None],
                        ],
                        ["enabled", [], ["is_enabled", _bool]],
                    ]
                }
            ]
        }
    ]


class ProductRetriever(Retriever):

    model = Product
    id = ["sku"]
    structures = [
        {
            "results": [
                ["title", [], ["title", None]],
                {
                    "raw": [
                        [
                            "country_of_manufacture",
                            [],
                            ["country_of_manufacture", None],
                        ],
                        [
                            "ec_brand",
                            [],
                            ["brand", None],
                        ],
                        ["ec_category_filter", [], ["category", _first]],
                        ["ec_price", [], ["msrp", None]],
                        ["ec_promo_price", [], ["sale_price", None]],
                        ["ec_rating", [], ["rating", None]],
                        [
                            "ec_shortdesc",
                            [],
                            [
                                "description",
                                None,
                            ],
                        ],
                        ["ec_skus", [], ["sku", _first]],
                        ["permanentid", [], ["permanent_id", None]],
                        ["lcbo_alcohol_percent", [], ["abv", None]],
                        ["max_cart_qty", [], ["maximum", None]],
                        ["min_cart_qty", [], ["minimum", None]],
                        [
                            "name",
                            [],
                            ["name", None],
                        ],
                        [
                            "qty_increments",
                            [],
                            ["increment", None],
                        ],
                        ["uri", [], ["uri", None]],
                    ]
                },
            ]
        },
    ]


class ImageRetriever(Retriever):

    model = Image
    id = ["product_id", "source_url"]
    structures = [
        {
            "results": [
                {
                    "raw": [
                        [
                            "ec_skus",
                            [
                                Product,
                                ["id"],
                                ["product_id"],
                                [
                                    "sku",
                                    _first,
                                ],
                            ],
                            [],
                        ],
                        [
                            "ec_thumbnails",
                            [],
                            [
                                "source_url",
                                None,
                            ],
                        ],
                    ]
                },
            ]
        }
    ]
