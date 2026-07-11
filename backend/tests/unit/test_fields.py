"""Unit tests for domain/fields.py — UIField definitions and field lists."""

import pytest
from domain.fields import (
    UIField,
    ANALYTE_FIELDS,
    BIO_FIELDS,
    IMMOB_FIELDS,
    MEM_FIELDS,
    ALL_FIELDS,
)

pytestmark = pytest.mark.unit


class TestUIFieldDataclass:
    """Tests for the UIField dataclass."""

    def test_uifield_required_attributes(self):
        """UIField can be created with required attributes."""
        f = UIField(name="ta_id", label="ID аналита", type="text")
        assert f.name == "ta_id"
        assert f.label == "ID аналита"
        assert f.type == "text"

    def test_uifield_optional_attributes_default_to_none(self):
        """Optional attributes default to None or empty string."""
        f = UIField(name="x", label="X", type="number")
        assert f.min_value is None
        assert f.max_value is None
        assert f.options is None
        assert f.group is None
        assert f.column is None
        assert f.help == ""

    def test_uifield_with_all_attributes(self):
        """UIField stores all attributes correctly."""
        f = UIField(
            name="adhesion",
            label="Адгезия",
            type="select",
            options=["низкая", "средняя", "высокая"],
            help="Уровень адгезии",
            group="immob",
            column=2,
        )
        assert f.options == ["низкая", "средняя", "высокая"]
        assert f.group == "immob"
        assert f.column == 2

    def test_uifield_with_range_constraints(self):
        """UIField stores min/max values for number fields."""
        f = UIField(name="ph_min", label="pH Min", type="number", min_value=2.0, max_value=10.0)
        assert f.min_value == 2.0
        assert f.max_value == 10.0


class TestAnalyteFields:
    """Tests for ANALYTE_FIELDS list."""

    def test_analyte_fields_not_empty(self):
        """ANALYTE_FIELDS list is not empty."""
        assert len(ANALYTE_FIELDS) > 0

    def test_all_analyte_fields_are_uifield_instances(self):
        """All items in ANALYTE_FIELDS are UIField instances."""
        assert all(isinstance(f, UIField) for f in ANALYTE_FIELDS)

    def test_analyte_fields_contain_ta_id(self):
        """ANALYTE_FIELDS contains the ta_id field."""
        names = [f.name for f in ANALYTE_FIELDS]
        assert "ta_id" in names

    def test_analyte_fields_have_correct_group(self):
        """All analyte fields belong to 'analyte' group."""
        assert all(f.group == "analyte" for f in ANALYTE_FIELDS)


class TestBioFields:
    """Tests for BIO_FIELDS list."""

    def test_bio_fields_not_empty(self):
        """BIO_FIELDS list is not empty."""
        assert len(BIO_FIELDS) > 0

    def test_all_bio_fields_are_uifield_instances(self):
        """All items in BIO_FIELDS are UIField instances."""
        assert all(isinstance(f, UIField) for f in BIO_FIELDS)

    def test_bio_fields_contain_bre_id(self):
        """BIO_FIELDS contains the bre_id field."""
        names = [f.name for f in BIO_FIELDS]
        assert "bre_id" in names

    def test_bio_fields_have_correct_group(self):
        """All bio fields belong to 'bio' group."""
        assert all(f.group == "bio" for f in BIO_FIELDS)


class TestImmobFields:
    """Tests for IMMOB_FIELDS list."""

    def test_immob_fields_not_empty(self):
        """IMMOB_FIELDS list is not empty."""
        assert len(IMMOB_FIELDS) > 0

    def test_all_immob_fields_are_uifield_instances(self):
        """All items in IMMOB_FIELDS are UIField instances."""
        assert all(isinstance(f, UIField) for f in IMMOB_FIELDS)

    def test_immob_fields_contain_im_id(self):
        """IMMOB_FIELDS contains the im_id field."""
        names = [f.name for f in IMMOB_FIELDS]
        assert "im_id" in names


class TestMemFields:
    """Tests for MEM_FIELDS list."""

    def test_mem_fields_not_empty(self):
        """MEM_FIELDS list is not empty."""
        assert len(MEM_FIELDS) > 0

    def test_all_mem_fields_are_uifield_instances(self):
        """All items in MEM_FIELDS are UIField instances."""
        assert all(isinstance(f, UIField) for f in MEM_FIELDS)

    def test_mem_fields_contain_mem_id(self):
        """MEM_FIELDS contains the mem_id field."""
        names = [f.name for f in MEM_FIELDS]
        assert "mem_id" in names


class TestAllFields:
    """Tests for ALL_FIELDS combined list."""

    def test_all_fields_is_union_of_four_groups(self):
        """ALL_FIELDS equals the union of all four field lists."""
        expected = ANALYTE_FIELDS + BIO_FIELDS + IMMOB_FIELDS + MEM_FIELDS
        assert ALL_FIELDS == expected

    def test_all_fields_length_matches_sum(self):
        """Length of ALL_FIELDS equals sum of individual lists."""
        assert len(ALL_FIELDS) == (
            len(ANALYTE_FIELDS) + len(BIO_FIELDS) + len(IMMOB_FIELDS) + len(MEM_FIELDS)
        )
