# Django Retriever 
### The Simple Way to Interface JSON and Django

## Overview
The retriever is an interface used to define how to map
a JSON object to a Django model. The retriever takes care
of mutating the JSON structure, connecting foreign objects,
and creating or updating the resulting Django model.

There are several components that must be defined in the
retriever to complete the job,
  - `model` the Django model with which the retriever
is intended to interface
  - `id` the list of field names in the Django model
that should be used to determine whether an object is
already in the database. These can be thought of unique
fields. If they are not actually unique, the retriever will
react by not saving the JSON object.
  - `structures` the critical component of the retriever. The
`structures` attribute is the interface between the JSON
document and the Django model. The interface is a nested structure
of lists and dictionaries, and must nest to a series of tuple/list
objects in the following format,
    - `name` the name of the key in the JSON document
    - `foreign_structures` (defined below) the list of foreign structures to
define how a key in the JSON document must be used to relate
Django models
    - `structures` (defined below) the list of mappings to determine how the
JSON document value must be mutated and saved to the Django
model

## Definitions
- `ForeignStructure`
  - `model` the foreign model
  - `id` the primary key field name in the foreign model
  - `id2` the field name in the current model that is mapped
to the primary key in the foreign model (`id`)
  - `Structure` the normal structure definition for the JSON
document, because the value might very well map to another
field on the foreign model
- `Structure`
  - `name` the new name of the JSON document, in the case
the JSON and the Django model name the field differently
  - `func` the mutation to perform on the JSON document. Can
be one of `int`, `str`, `bool`, or a custom function

## Installation
```
pip install django-retriever
```

## Contributing
Before contributing, please install the `test` and `dev` versions of
the library,
```
pip install django-retriever[dev,test]
```

Please run tests using (in the root project directory)
```
python -m pytest tests
```

Once the package is ready to be uploaded, please complete the
following in order,
- Increment the `version` template in `pyproject.toml`
- Set the `PYPI_TOKEN` environment variable
- Run `./bin/twine` from the root project directory


## Usage
The best explanation is going to be through an implementation, so please
consider the following case. The JSON object includes information
about a product image, and is taken from a public API.

Consider the JSON document,
```
{
  "results": [
    {
      "raw": {
        "ec_sku": "333333",
        "image": "https://image3.jpeg"
      }
    }
    {
      "raw": {
        "ec_sku": "333333",
        "image": "https://image3.jpeg"
      }
    }
    {
      "raw": {
        "ec_sku": "333333",
        "image": "https://image3.jpeg"
      }
    }
  ]
}
```
The JSON document should be loaded into a python object,
using a parser of your choice. The following code in
`models.py` and `retriever.py` is a sample that could be
used to parse the JSON document into some database objects
through the Django ORM.
```
# models.py

from django.db import models


class Product(models.Model):

    id = models.AutoField(
        primary_key=True)
    sku = models.CharField(
        max_length=64)


class Image(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images")
    image = models.ImageField(
        # storage, etc.
        ...)
    source_url = models.CharField(
      max_length=512)
```
```
# retrievers.py

from retriever import Retriever
from .models import (
    Image,
    Product
)


class ProductRetriever(Retriever):

    model = Product
    id = ["sku"]
    structures = [
        {
            "results": [
                {
                    "raw": [
                        [
                            "ec_sku",
                            [],
                            [
                                "sku",
                                None
                            ]
                        ]
                    ]
                }
            ]
        }
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
                            # JSON name
                            "ec_sku",
                            # foreign structures
                            [
                                # foreign model
                                Product,
                                # id and foreign id field name
                                ["id"],
                                ["product_id"],
                                # normal structure, the `ec_sku` field is
                                # clearly a map to the unique field `sku`, not `id` # itself. Note that `sku` should be unique or the
                                # structure will not be created and an error should
                                # be propagated
                                [
                                    "sku",
                                    None
                                ],
                            ],
                            # structures. Note `sku` is not in the `Image` model,
                            # we are not interested in mapping it
                            [],
                        ],
                        [
                            # JSON name
                            "image",
                            # no foreign structures
                            [],
                            # map it to `source_url` field name, no
                            # mutation required
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
```
If you've loaded in the JSON document and defined the retrievers
correctly, you can now simply save the JSON document to
the database,
```
from .retrievers import *

json_object = {
    "results": [
        ...
    ]
}

ProductRetriever(
    batch_size=5,
    default=[],
    strict=True
).save(json_object)

ImageRetriever(
    batch_size=5,
    default=[],
    strict=True
).save(json_object)
```
The retrievers have used the `ec_sku` field in the JSON
document to find the `Product` object that corresponds to
the correct `Image` object. In this way, a JSON document can
be decomposed into several retrievers, and the definitions 
can be isolated. Note, the `ProductRetriever` should be called
before the `ImageRetriever`, or there will be no `Product` objects
in the database to find.
