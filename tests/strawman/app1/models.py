from django.db import models


class Location(models.Model):

    id = models.BigIntegerField(primary_key=True)
    country = models.CharField(max_length=64)
    city = models.CharField(max_length=64)
    email = models.EmailField(null=True, max_length=128)
    region = models.CharField(null=True, max_length=64)
    name = models.CharField(max_length=128)
    phone_number = models.CharField(null=True, max_length=10)
    street = models.CharField(max_length=256)
    postal_code = models.CharField(null=True, max_length=6)
    zip_code = models.CharField(null=True, max_length=5)
    unit = models.PositiveIntegerField(null=True)
    uri = models.CharField(max_length=256)


class Product(models.Model):

    abv = models.DecimalField(max_digits=4, decimal_places=1)
    brand = models.CharField(null=True, max_length=128)
    category = models.CharField(null=True, max_length=128)
    country_of_manufacture = models.CharField(null=True, max_length=64)
    description = models.TextField(null=True, max_length=1024)
    increment = models.PositiveSmallIntegerField(null=True)
    locations = models.ManyToManyField(Location, through="State")
    msrp = models.DecimalField(null=True, max_digits=8, decimal_places=2)
    maximum = models.PositiveIntegerField()
    minimum = models.PositiveIntegerField()
    name = models.CharField(max_length=128)
    permanent_id = models.BigIntegerField(null=True)
    rating = models.DecimalField(null=True, max_digits=3, decimal_places=1)
    region = models.CharField(null=True, max_length=64)
    sale_price = models.DecimalField(null=True, max_digits=8, decimal_places=2)
    sku = models.CharField(max_length=32)
    subregion = models.CharField(null=True, max_length=64)
    title = models.CharField(max_length=128)
    uri = models.URLField(max_length=512)


class State(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    is_available = models.BooleanField(null=True)
    is_buyable = models.BooleanField(null=True)
    is_deficient = models.BooleanField(null=True)
    is_enabled = models.BooleanField(null=True)
    is_low_stock_combined = models.BooleanField(null=True)
    is_stock_combined = models.BooleanField(null=True)
    is_stocked = models.BooleanField(null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    low_stock_threshold = models.PositiveSmallIntegerField(null=True)
    out_of_stock_threshold = models.PositiveSmallIntegerField(null=True)
    quantity = models.PositiveSmallIntegerField(null=True, default=0)
    deliverable_quantity = models.PositiveSmallIntegerField(
        null=True, default=0
    )


class Image(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField()
    source = models.CharField(max_length=64)
    source_url = models.CharField(null=True, max_length=128)
    thumbnail = models.ImageField()
