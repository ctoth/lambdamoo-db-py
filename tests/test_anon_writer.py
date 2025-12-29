"""Tests for anon writing support in lambdamoo-db-py writer - TDD: write tests FIRST.

These tests verify that the lambdamoo-db-py Writer can write anonymous objects.
The writer needs to be extended to support this.
"""

import io
import pytest
from lambdamoo_db.database import MooDatabase, MooObject, Property
from lambdamoo_db.enums import ObjectFlags, PropertyFlags


def create_test_db():
    """Create a minimal test database."""
    db = MooDatabase()
    db.version = 17
    db.total_objects = 2
    db.objects = {
        0: MooObject(id=0, name="System", flags=ObjectFlags(0), owner=0, location=-1, parents=[-1]),
        1: MooObject(id=1, name="Root", flags=ObjectFlags(0), owner=0, location=-1, parents=[0]),
    }
    return db


class TestAnonWriterBasics:
    """Test basic anonymous object writing functionality."""

    def test_writeObjects_handles_anon_objects(self):
        """Writer.writeObjects should handle objects with anon=True."""
        from lambdamoo_db.writer import Writer

        db = create_test_db()

        # Add an anon object
        anon = MooObject(id=1001, name="", flags=ObjectFlags.ANONYMOUS, owner=1, location=-1, parents=[1])
        anon.anon = True
        db.objects[1001] = anon

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)

        # Should not raise - needs to handle anon objects
        writer.writeObjects()

        content = output.getvalue()
        # Should include the anon object ID
        assert "1001" in content

    def test_anon_count_written(self):
        """Should write count of anonymous objects."""
        from lambdamoo_db.writer import Writer

        db = create_test_db()

        # Add 2 anon objects
        anon1 = MooObject(id=1001, name="", flags=ObjectFlags.ANONYMOUS, owner=1, location=-1, parents=[1])
        anon1.anon = True
        anon2 = MooObject(id=1002, name="", flags=ObjectFlags.ANONYMOUS, owner=1, location=-1, parents=[1])
        anon2.anon = True
        db.objects[1001] = anon1
        db.objects[1002] = anon2

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeObjects()

        content = output.getvalue()
        # Should have count of 2 anons somewhere
        # After regular objects, before terminating 0
        assert "2\n" in content  # anon count

    def test_anon_followed_by_terminator(self):
        """Anon section should end with 0 terminator."""
        from lambdamoo_db.writer import Writer

        db = create_test_db()

        anon = MooObject(id=1001, name="", flags=ObjectFlags.ANONYMOUS, owner=1, location=-1, parents=[1])
        anon.anon = True
        db.objects[1001] = anon

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeObjects()

        content = output.getvalue()
        # Should end with 0 terminator
        lines = content.strip().split('\n')
        assert lines[-1] == "0"

    def test_no_anons_just_zero(self):
        """With no anon objects, should just write 0."""
        from lambdamoo_db.writer import Writer

        db = create_test_db()  # No anon objects

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeObjects()

        content = output.getvalue()
        lines = content.strip().split('\n')
        # Last line should be 0 (no anons)
        assert lines[-1] == "0"


class TestAnonObjectWriting:
    """Test writing individual anonymous objects."""

    def test_write_anon_object_format(self):
        """Anon object should be written in same format as regular object."""
        from lambdamoo_db.writer import Writer

        db = create_test_db()

        anon = MooObject(id=1001, name="", flags=ObjectFlags.ANONYMOUS, owner=1, location=-1, parents=[1])
        anon.anon = True
        anon.properties.append(Property(propertyName="test", value="hello", owner=1, perms=PropertyFlags.READ))
        anon.propdefs_count = 1
        db.objects[1001] = anon

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeObjects()

        content = output.getvalue()
        # Should include object header
        assert "#1001" in content
        # Should include property value
        assert "hello" in content

    def test_anon_with_empty_name(self):
        """Anon objects have empty names - should be written correctly."""
        from lambdamoo_db.writer import Writer

        db = create_test_db()

        anon = MooObject(id=1001, name="", flags=ObjectFlags.ANONYMOUS, owner=1, location=-1, parents=[1])
        anon.anon = True
        db.objects[1001] = anon

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeObjects()

        content = output.getvalue()
        # After #1001, next line should be empty name
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line == "#1001":
                # Next line is the name (empty)
                assert lines[i + 1] == ""
                break


class TestMultipleAnons:
    """Test writing multiple anonymous objects."""

    def test_write_multiple_anons(self):
        """Should write multiple anon objects correctly."""
        from lambdamoo_db.writer import Writer

        db = create_test_db()

        for i in range(3):
            anon = MooObject(id=1001 + i, name="", flags=ObjectFlags.ANONYMOUS, owner=1, location=-1, parents=[1])
            anon.anon = True
            db.objects[1001 + i] = anon

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeObjects()

        content = output.getvalue()
        # All three anons should appear
        assert "#1001" in content
        assert "#1002" in content
        assert "#1003" in content

    def test_anons_written_after_regular_objects(self):
        """Anon objects should be written after all regular objects."""
        from lambdamoo_db.writer import Writer

        db = create_test_db()

        anon = MooObject(id=1001, name="", flags=ObjectFlags.ANONYMOUS, owner=1, location=-1, parents=[1])
        anon.anon = True
        db.objects[1001] = anon

        output = io.StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeObjects()

        content = output.getvalue()
        # Regular objects (0, 1) should come before anon (1001)
        pos_obj0 = content.find("#0")
        pos_obj1 = content.find("#1\n")  # Be specific to not match #1001
        pos_anon = content.find("#1001")
        assert pos_obj0 < pos_anon
        assert pos_obj1 < pos_anon
