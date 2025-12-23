"""
Round-trip tests for DB version 17 compatibility.

These tests are THE PROOF of compatibility. They read a reference database
written by actual ToastStunt, write it back out, and verify the output
matches the original line-by-line.

Why line-by-line comparison?
- Using our own reader to verify our writer is circular reasoning
- We'd just be confirming that we made the same assumptions in both directions
- Only byte-level (or near-byte-level) comparison against ToastStunt's output
  proves we're actually compatible
"""
import pytest
from io import StringIO
from pathlib import Path

from lambdamoo_db.reader import load
from lambdamoo_db.writer import Writer


class TestRoundtripToastcore:
    """
    Round-trip tests using toaststunt/toastcore.db as the reference.
    This is a v17 database written by actual ToastStunt.
    """

    def test_roundtrip_produces_identical_output(
        self, toastcore_db_path, compare_db_to_reference
    ):
        """
        DOING: Read toastcore.db, write to string, compare to original
        EXPECT: Zero differences (or only acceptable float formatting diffs)
        IF NO: Writer is producing incorrect output
        """
        db = load(str(toastcore_db_path))
        diffs = compare_db_to_reference(db, toastcore_db_path, max_diffs=20)

        if diffs:
            diff_report = "\n".join(str(d) for d in diffs)
            pytest.fail(
                f"Round-trip produced {len(diffs)} difference(s):\n{diff_report}"
            )

    def test_version_string_preserved(self, toastcore_db_path):
        """The version string must be written exactly as expected."""
        db = load(str(toastcore_db_path))

        output = StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeDatabase()

        output.seek(0)
        first_line = output.readline().rstrip()

        assert first_line == "** LambdaMOO Database, Format Version 17 **"

    def test_player_count_preserved(self, toastcore_db_path):
        """The number of players must be preserved."""
        db = load(str(toastcore_db_path))
        original_count = db.total_players

        output = StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeDatabase()

        # Re-read and verify
        output.seek(0)
        lines = output.readlines()

        # Player count is on line 2 (after version string)
        player_count_line = lines[1].strip()
        assert int(player_count_line) == original_count

    def test_object_count_preserved(self, toastcore_db_path):
        """The number of objects must be preserved."""
        db = load(str(toastcore_db_path))

        # Verify: objects + recycled = total
        object_count = len(db.objects)
        recycled_count = len(db.recycled_objects)
        assert object_count + recycled_count == db.total_objects

    def test_verb_count_preserved(self, toastcore_db_path):
        """The total number of verb programs must be preserved."""
        db = load(str(toastcore_db_path))

        # total_verbs = count of verbs with programs (not all verbs)
        verbs_with_programs = sum(
            1 for obj in db.objects.values()
            for verb in obj.verbs
            if verb.code is not None
        )

        assert verbs_with_programs == db.total_verbs


@pytest.mark.slow
class TestRoundtripMongoose:
    """
    Round-trip tests using the large mongoose.db (35MB).
    These are stress tests that verify we handle large databases correctly.
    """

    def test_roundtrip_mongoose(self, mongoose_db_path, compare_db_to_reference):
        """
        Round-trip the large mongoose database.
        This is a stress test for memory and correctness with many objects.
        """
        db = load(str(mongoose_db_path))
        diffs = compare_db_to_reference(db, mongoose_db_path, max_diffs=20)

        if diffs:
            diff_report = "\n".join(str(d) for d in diffs)
            pytest.fail(
                f"Mongoose round-trip produced {len(diffs)} difference(s):\n{diff_report}"
            )


class TestRoundtripDiagnostics:
    """
    Diagnostic tests that help identify WHERE the writer diverges.
    These are not pass/fail tests but produce detailed output.
    """

    def test_first_100_lines(self, toastcore_db_path):
        """Compare just the first 100 lines to narrow down issues."""
        db = load(str(toastcore_db_path))

        output = StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeDatabase()

        output.seek(0)
        output_lines = [output.readline().rstrip() for _ in range(100)]

        with open(toastcore_db_path, "r", encoding="latin-1") as ref:
            ref_lines = [ref.readline().rstrip() for _ in range(100)]

        diffs = []
        for i, (expected, actual) in enumerate(zip(ref_lines, output_lines), 1):
            if expected != actual:
                diffs.append(f"Line {i}:\n  expected: {expected!r}\n  actual:   {actual!r}")

        if diffs:
            pytest.fail(f"First 100 lines had differences:\n" + "\n".join(diffs[:10]))

    def test_section_boundaries(self, toastcore_db_path):
        """
        Verify that key section markers appear in the correct order.
        This helps identify if sections are being written out of order.
        """
        db = load(str(toastcore_db_path))

        output = StringIO()
        writer = Writer(db=db, output_file=output)
        writer.writeDatabase()

        content = output.getvalue()

        # Key markers that should appear in order
        markers = [
            "** LambdaMOO Database, Format Version 17 **",
            "values pending finalization",
            "clocks",
            "queued tasks",
            "suspended tasks",
            "active connections",
        ]

        positions = []
        for marker in markers:
            pos = content.find(marker)
            if pos == -1:
                pytest.fail(f"Marker not found in output: {marker!r}")
            positions.append((marker, pos))

        # Verify they appear in order
        for i in range(len(positions) - 1):
            current = positions[i]
            next_marker = positions[i + 1]
            if current[1] >= next_marker[1]:
                pytest.fail(
                    f"Markers out of order:\n"
                    f"  {current[0]!r} at position {current[1]}\n"
                    f"  {next_marker[0]!r} at position {next_marker[1]}"
                )
