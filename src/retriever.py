"""Base extensible retriever."""

import json
import logging
from abc import ABC
from dataclasses import dataclass
from itertools import islice
from typing import Any as T
from typing import Dict, Iterable, List, Optional, Tuple, Union

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import IntegrityError, models
from django.db.transaction import atomic


class RetrieverError(Exception):
    pass


def chunks(iterable: Iterable, n: int):
    _iterable = iter(iterable)

    def _slice(iterable):
        return list(islice(iterable, n))

    while chunk := _slice(_iterable):
        yield chunk


@dataclass
class ForeignStructure:

    id: List[str]
    model: models.Model
    structures: List


@dataclass
class Structure:

    obj: Optional[T]
    model: models.Model
    id: Union[List[str], str]
    structures: Dict[Union[str, Tuple[str]], Union["Structure", T]]
    err: List[RetrieverError]

    def register_error(self, message):
        self.err.append(RetrieverError(message))


class Retriever(ABC):

    model = None
    id = []
    structures = []

    def __init__(
        self,
        batch_size: int = 5,
        default: List[List] = [],
        strict: bool = False,
        foreign_structures: List[Structure] = [],
    ):
        self.batch_size = batch_size
        self.default = default
        self.strict = strict
        self.foreign_structures = foreign_structures

    def _log(self, message, *args, log_level=logging.INFO):
        logging.log(log_level, message.format(*args))

    def _retrieve(self, structures, res):
        temp = []
        substructures = []

        if isinstance(res, list):
            substructures.append(
                [x for y in res for x in self._retrieve(structures, y)]
            )
        else:
            for s in structures:
                if isinstance(s, list):
                    temp.append(s)
                else:
                    for name, temp2 in s.items():
                        substructures.append(
                            self._retrieve(temp2, res.get(name))
                        )

        return self._parse(temp, substructures, res)

    def _parse_structures(self, x, y):
        z = x

        for a, b in y:
            if a in [c for c, _ in z]:
                for c, d in z:
                    if a == c:
                        if isinstance(b, ForeignStructure) and isinstance(
                            d, ForeignStructure
                        ):
                            d.structures.append(b.structures)
            else:
                z.append([a, b])

        return z

    def _parse_res(self, res, name, bridge):
        _name, func = bridge

        if func:
            return [_name, func(res[name])]

        return [_name, res[name]]

    def _extend_structure(self, s):
        if s:
            if isinstance(s[0], list):
                return s

            return [s]

        return []

    def _parse(self, structures, substructures, res):
        temp = []
        temp2 = []
        err = []

        for name, foreign_structures, bridges in self._extend_structure(
            structures
        ):
            for model, fid, id, bridge in self._extend_structure(
                foreign_structures
            ):
                if name not in res:
                    err.append(
                        RetrieverError(
                            f"Failed to parse '{bridge[0]}'. Could not "
                            f"find key '{name}' in {json.dumps(res)}"
                        )
                    )
                else:
                    if id in [t[0] for t in temp2]:
                        for t in temp2:
                            if t[0] == id:
                                t[1].structures.append(
                                    self._parse_res(res, name, bridge)
                                )
                    else:
                        temp2.append(
                            [
                                id,
                                ForeignStructure(
                                    fid,
                                    model,
                                    [self._parse_res(res, name, bridge)],
                                ),
                            ]
                        )

            for bridge in self._extend_structure(bridges):
                if name not in res:
                    if self.strict:
                        err.append(
                            RetrieverError(
                                f"Failed to parse '{bridge[0]}'. Could not "
                                f"find key '{name}' in {json.dumps(res)}"
                            )
                        )
                else:
                    temp2.append(self._parse_res(res, name, bridge))

        if temp2:
            temp.append(Structure(None, self.model, self.id, temp2, err))

        if not temp or not substructures:
            for substructure in substructures:
                temp.extend(substructure)
        else:
            for x in substructures:
                temp2 = []

                for z in temp:
                    for y in x:
                        temp2.append(
                            Structure(
                                None,
                                self.model,
                                self.id,
                                self._parse_structures(
                                    z.structures, y.structures
                                ),
                                z.err + y.err,
                            )
                        )

                temp = temp2

        return temp

    def _parse_foreign_structure(
        self, name, s
    ) -> Tuple[List[str], List[RetrieverError]]:
        objects = []

        for t in self.foreign_structures:
            temp = []

            for _name, _ in s.structures:
                if t.obj is not None:
                    temp.append([_name, getattr(t.obj, _name)])

            if temp == s.structures:
                objects.append(t.obj)

        if len(objects) > 1:
            return name, []

        if not objects:
            try:
                objects.append(s.model.objects.get(**dict(s.structures)))
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return name, []

        id = []

        for _name in s.id:
            id.append(getattr(objects[0], _name))

        if len(id) == 1:
            return name[0], id[0]

        return name, id

    def _parse_id(self, s):
        _id = {}

        for name in self.id:
            for a, b in s.structures:
                if a == name:
                    _id[a] = b

        return _id

    def save(self, res) -> List[Structure]:
        structures = self._retrieve(self.structures, res)

        for s in structures:
            s.structures = self._parse_structures(s.structures, self.default)

        for s in structures:
            iter = 0
            num_structures = len(s.structures)

            while iter < num_structures:
                name, value = s.structures[iter]

                if isinstance(value, ForeignStructure):
                    _name, _id = self._parse_foreign_structure(name, value)

                    if _id:
                        s.structures[iter] = [_name, _id]
                    else:
                        s.register_error(
                            f"Failed to parse foreign id for {name} from "
                            f"foreign structure: {s.structures[iter][1]}"
                        )

                        s.structures = (
                            s.structures[:iter] + s.structures[(iter + 1) :]
                        )
                        iter -= 1
                        num_structures -= 1

                iter += 1

        for s in structures:
            obj = self.model.objects.filter(**self._parse_id(s))

            if obj.count() > 1:
                s.register_error(
                    f"The retriever found {obj.count()} "
                    "objects in the database matching the id: "
                    f"{self._parse_id(s)}"
                )
            elif obj.count() == 1:
                s.obj = obj[0]

        existing_structures = (s for s in structures if not s.err and s.obj)

        for batch_structures in chunks(existing_structures, self.batch_size):
            for s in batch_structures:
                for name, value in s.structures:
                    setattr(s.obj, name, value)

            self.model.objects.bulk_update([s.obj for s in batch_structures])

            for s in batch_structures:
                self._log("Updated structure: {}", s)

        new_structures = (s for s in structures if not s.err and not s.obj)

        for batch_structures in chunks(new_structures, self.batch_size):
            for s in batch_structures:

                print(s)
                s.obj = self.model(**dict(s.structures))
            try:
                with atomic():
                    self.model.objects.bulk_create(
                        [s.obj for s in batch_structures]
                    )
            except IntegrityError:
                for s in batch_structures:
                    try:
                        with atomic():
                            s.obj.save()
                    except IntegrityError as e2:
                        s.register_error(
                            "Integrity error while saving "
                            f"structure: {s}. Error: {e2}"
                        )

            for s in [s for s in batch_structures if not s.err]:
                self._log("Structure created: {}", s)

        for s in [s for s in structures if s.err]:
            self._log("Structure not created: {}.", s, log_level=logging.ERROR)

        return structures
