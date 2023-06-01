"""Pytest testing of `Retriever`."""

from copy import deepcopy

import pytest
from ddf import G

from .samples import SAMPLE_01, SAMPLE_02
from .strawman.app1.models import Image, Location, State
from .strawman.app1.retrievers import (
    ImageRetriever,
    LocationRetriever,
    ProductRetriever,
    StateRetriever,
)

pytestmark = pytest.mark.django_db


class TestRetriever:
    def test_success(self):
        retriever = LocationRetriever()
        structures = retriever.save(SAMPLE_02)

        assert len(structures) == 3

        for s in structures:
            assert s.obj
            assert s.model is Location
            assert s.id == ["id"]
            assert not s.err

        assert Location.objects.count() == 3

        location = structures[0].obj
        expected = SAMPLE_02[0]["output"]
        assert location.name == expected["name"]
        assert location.city == expected["city"]
        assert location.postal_code == expected["zip"]

    @pytest.mark.parametrize("strict", [True, False])
    def test_name_in_sample_not_retrieved(self, strict):
        sample = deepcopy(SAMPLE_02)
        sample[0]["output"].pop("name")

        retriever = LocationRetriever(strict=strict)
        structures = retriever.save(sample)

        assert len(structures) == 3

        if strict:
            errored = structures[0]
            assert len(errored.err) == 1
            assert "Failed to parse 'name'" in str(errored.err[0])

            assert Location.objects.count() == 2
        else:
            for s in structures:
                assert not s.err

            assert Location.objects.count() == 3

    def test_default_added_to_structures(self):
        retriever = LocationRetriever(default=[["country", "Canada"]])
        structures = retriever.save(SAMPLE_02)

        assert len(structures) == 3

        assert Location.objects.count() == 3

        for s in structures:
            assert s.obj.country == "Canada"

    def test_integrity_error_caught_on_model_save(self):
        retriever = LocationRetriever()
        temp = deepcopy(retriever.structures)
        # remove required `id` field, cannot be null
        temp[0]["output"].pop(0)
        retriever.structures = temp
        structures = retriever.save(SAMPLE_02)

        assert len(structures) == 3

        for s in structures:
            assert len(s.err) == 1
            assert "Integrity error while saving structure" in str(s.err[0])

        assert Location.objects.count() == 0

    def test_retriever_id_not_unique_in_database(self):
        _uri = SAMPLE_02[0]["output"]["url_key"]
        G(Location, uri=_uri, n=2)

        retriever = LocationRetriever()
        retriever.id = ["uri"]
        structures = retriever.save(SAMPLE_02)

        assert len(structures) == 3
        errored = structures[0]

        assert len(errored.err) == 1
        assert (
            "The retriever found 2 objects in the database matching the id"
            in str(errored.err[0])
        )

        # comprises current uri objects, 2 created
        assert Location.objects.count() == 4


class TestForeignKey:
    def test_success(self):
        product_retriever = ProductRetriever()
        product_structures = product_retriever.save(SAMPLE_01)

        retriever = ImageRetriever(foreign_structures=product_structures)
        structures = retriever.save(SAMPLE_01)

        assert len(structures) == 3

        for s in structures:
            assert s.obj.product_id
            assert not s.err

        assert Image.objects.count() == 3

        image = structures[0].obj
        expected = SAMPLE_01["results"][0]["raw"]
        assert image.source_url == expected["ec_thumbnails"]

    def test_success_no_foreign_structures(self):
        product_retriever = ProductRetriever()
        product_retriever.save(SAMPLE_01)

        retriever = ImageRetriever()
        structures = retriever.save(SAMPLE_01)

        assert len(structures) == 3

        for s in structures:
            assert s.obj.product_id
            assert not s.err

        assert Image.objects.count() == 3

        image = structures[0].obj
        expected = SAMPLE_01["results"][0]["raw"]
        assert image.source_url == expected["ec_thumbnails"]

    def test_name_in_sample_not_retrieved(self):
        sample = deepcopy(SAMPLE_01)
        sample["results"][0]["raw"].pop("ec_skus")

        product_retriever = ProductRetriever()
        product_structures = product_retriever.save(sample)

        retriever = ImageRetriever(foreign_structures=product_structures)
        structures = retriever.save(sample)

        assert len(structures) == 3
        errored = structures[0]

        assert len(errored.err) == 1
        assert "Failed to parse 'sku'. Could not find key 'ec_skus' in" in str(
            errored.err[0]
        )

        assert Image.objects.count() == 2

    def test_foreign_structures_do_not_exist(self):
        retriever = ImageRetriever()
        structures = retriever.save(SAMPLE_01)

        assert len(structures) == 3

        for s in structures:
            assert len(s.err) == 1
            assert "Failed to parse foreign id" in str(s.err[0])

        assert Image.objects.count() == 0


class TestM2m:
    def test_m2m_relationship_saves(self):
        location = Location(id=374)
        location.save()

        ret1 = ProductRetriever()
        ret2 = StateRetriever(default=[["location_id", 374]])

        ret1.save(SAMPLE_01)
        ret2.save(SAMPLE_01)

        assert State.objects.count() == 3
