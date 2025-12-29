"""Tests for waif writing support in lambdamoo-db-py writer - TDD: write tests FIRST.

These tests verify that the lambdamoo-db-py Writer can write waifs.
The writer needs to be extended to support this.
"""

import io
import pytest
from lambdamoo_db.database import Waif, WaifReference, MooDatabase, ObjNum
from lambdamoo_db.enums import MooTypes


class TestWaifWriterBasics:
    """Test basic waif writing functionality."""

    def test_writeValue_handles_waif_reference(self):
        """Writer.writeValue should handle WaifReference type."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=1641, owner=2, props=["west"])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)

        # Should not raise - needs to handle WaifReference
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        # Should have TYPE_WAIF (13) tag
        assert f"{MooTypes.WAIF}\n" in content or "13\n" in content

    def test_write_waif_definition_format(self):
        """First write of a waif should produce definition format."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=1641, owner=2, props=["test_value"])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        # Definition format: "d {index}"
        assert "d 0" in content

    def test_write_waif_reference_format(self):
        """Second write of same waif should produce reference format."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=1641, owner=2, props=[])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)

        # First write = definition
        writer.writeValue(WaifReference(0))
        # Second write = reference
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        # Reference format: "r {index}"
        assert "r 0" in content

    def test_write_waif_includes_class(self):
        """Waif definition should include class object number."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=1641, owner=2, props=[])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        assert "1641" in content

    def test_write_waif_includes_owner(self):
        """Waif definition should include owner object number."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=100, owner=42, props=[])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        assert "42" in content


class TestWaifPropertyWriting:
    """Test waif property writing."""

    def test_write_waif_with_string_prop(self):
        """Should write string property values."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=100, owner=1, props=["hello"])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        assert "hello" in content

    def test_write_waif_with_int_prop(self):
        """Should write integer property values."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=100, owner=1, props=[42])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        assert "42" in content

    def test_write_waif_with_objnum_prop(self):
        """Should write object number property values."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=100, owner=1, props=[ObjNum(999)])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        assert "999" in content

    def test_write_waif_with_list_prop(self):
        """Should write list property values."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=100, owner=1, props=[[1, 2, 3]])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        # List should appear in output
        assert "1" in content and "2" in content and "3" in content

    def test_write_waif_with_none_prop(self):
        """Should handle None property values."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=100, owner=1, props=[None])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)

        # Should not raise
        writer.writeValue(WaifReference(0))


class TestMultipleWaifs:
    """Test writing multiple waifs."""

    def test_write_multiple_different_waifs(self):
        """Should write multiple different waifs correctly."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {
            0: Waif(waif_class=100, owner=1, props=["first"]),
            1: Waif(waif_class=100, owner=1, props=["second"]),
        }

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))
        writer.writeValue(WaifReference(1))

        content = output.getvalue()
        # Both should be definitions (different waifs)
        assert "d 0" in content
        assert "d 1" in content

    def test_write_same_waif_twice_produces_ref(self):
        """Writing same waif twice: first def, second ref."""
        from lambdamoo_db.writer import Writer

        db = MooDatabase()
        db.waifs = {0: Waif(waif_class=100, owner=1, props=[])}

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeValue(WaifReference(0))
        writer.writeValue(WaifReference(0))

        content = output.getvalue()
        # Should have one definition and one reference
        assert content.count("d 0") == 1
        assert content.count("r 0") == 1
