"""
Tests for enum values.

These values are defined in the LambdaMOO/ToastStunt C source and MUST match
exactly for database compatibility. These tests serve as documentation and
regression protection.

References:
- structures.h (MooTypes)
- db.h (DBVersions, ObjectFlags)
- db_io.c (PropertyFlags)
"""
import pytest
from lambdamoo_db.enums import MooTypes, DBVersions, PropertyFlags, ObjectFlags


class TestMooTypes:
    """
    MooTypes must match structures.h TYPE_* constants exactly.
    These are written to the database when serializing values.
    """

    def test_int_is_0(self):
        assert MooTypes.INT == 0

    def test_obj_is_1(self):
        assert MooTypes.OBJ == 1

    def test_str_is_2(self):
        assert MooTypes.STR == 2

    def test_err_is_3(self):
        assert MooTypes.ERR == 3

    def test_list_is_4(self):
        assert MooTypes.LIST == 4

    def test_clear_is_5(self):
        assert MooTypes.CLEAR == 5

    def test_none_is_6(self):
        assert MooTypes.NONE == 6

    def test_catch_is_7(self):
        assert MooTypes._CATCH == 7

    def test_finally_is_8(self):
        assert MooTypes._FINALLY == 8

    def test_float_is_9(self):
        assert MooTypes.FLOAT == 9

    def test_map_is_10(self):
        assert MooTypes.MAP == 10

    def test_anon_is_12(self):
        # Note: 11 is skipped in the enum
        assert MooTypes.ANON == 12

    def test_waif_is_13(self):
        assert MooTypes.WAIF == 13

    def test_bool_is_14(self):
        assert MooTypes.BOOL == 14

    def test_is_int_enum(self):
        """MooTypes should be usable as integers for database I/O."""
        assert int(MooTypes.STR) == 2
        assert MooTypes.STR + 0 == 2


class TestDBVersions:
    """
    DBVersions must match db.h DB_Version enum exactly.
    The database version determines which features are supported.
    """

    def test_prehistory_is_0(self):
        assert DBVersions.DBV_Prehistory == 0

    def test_exceptions_is_1(self):
        assert DBVersions.DBV_Exceptions == 1

    def test_break_cont_is_2(self):
        assert DBVersions.DBV_BreakCont == 2

    def test_float_is_3(self):
        assert DBVersions.DBV_Float == 3

    def test_bf_bug_fixed_is_4(self):
        assert DBVersions.DBV_BFBugFixed == 4

    def test_nextgen_is_5(self):
        assert DBVersions.DBV_NextGen == 5

    def test_task_local_is_6(self):
        assert DBVersions.DBV_TaskLocal == 6

    def test_map_is_7(self):
        assert DBVersions.DBV_Map == 7

    def test_file_io_is_8(self):
        assert DBVersions.DBV_FileIO == 8

    def test_exec_is_9(self):
        assert DBVersions.DBV_Exec == 9

    def test_interrupt_is_10(self):
        assert DBVersions.DBV_Interrupt == 10

    def test_this_is_11(self):
        assert DBVersions.DBV_This == 11

    def test_iter_is_12(self):
        assert DBVersions.DBV_Iter == 12

    def test_anon_is_13(self):
        assert DBVersions.DBV_Anon == 13

    def test_waif_is_14(self):
        assert DBVersions.DBV_Waif == 14

    def test_last_move_is_15(self):
        assert DBVersions.DBV_Last_Move == 15

    def test_threaded_is_16(self):
        assert DBVersions.DBV_Threaded == 16

    def test_bool_is_17(self):
        assert DBVersions.DBV_Bool == 17

    def test_num_versions_is_18(self):
        """Current version is Num_DB_Versions - 1."""
        assert DBVersions.Num_DB_Versions == 18

    def test_current_version_is_17(self):
        """The current DB format version should be 17 (Bool)."""
        current = DBVersions.Num_DB_Versions - 1
        assert current == 17


class TestPropertyFlags:
    """
    PropertyFlags are bitmask flags for property permissions.
    Must match db_io.c PF_* constants.
    """

    def test_none_is_0(self):
        assert PropertyFlags.NONE == 0

    def test_read_is_1(self):
        assert PropertyFlags.READ == 1

    def test_write_is_2(self):
        assert PropertyFlags.WRITE == 2

    def test_clear_is_4(self):
        assert PropertyFlags.CLEAR == 4

    def test_is_intflag(self):
        """PropertyFlags should support bitwise operations."""
        combined = PropertyFlags.READ | PropertyFlags.WRITE
        assert int(combined) == 3
        assert PropertyFlags.READ in combined
        assert PropertyFlags.WRITE in combined

    def test_all_flags_combined(self):
        """READ | WRITE | CLEAR should be 7."""
        all_flags = PropertyFlags.READ | PropertyFlags.WRITE | PropertyFlags.CLEAR
        assert int(all_flags) == 7

    def test_aliases(self):
        """Backward compatibility aliases should match."""
        assert PropertyFlags.R == PropertyFlags.READ
        assert PropertyFlags.W == PropertyFlags.WRITE
        assert PropertyFlags.C == PropertyFlags.CLEAR


class TestObjectFlags:
    """
    ObjectFlags are bitmask flags for object state.
    Must match db.h FLAG_* constants.
    """

    def test_none_is_0(self):
        assert ObjectFlags.NONE == 0

    def test_user_is_1(self):
        assert ObjectFlags.USER == 1

    def test_programmer_is_2(self):
        assert ObjectFlags.PROGRAMMER == 2

    def test_wizard_is_4(self):
        assert ObjectFlags.WIZARD == 4

    def test_obsolete_1_is_8(self):
        assert ObjectFlags.OBSOLETE_1 == 8

    def test_read_is_16(self):
        assert ObjectFlags.READ == 16

    def test_write_is_32(self):
        assert ObjectFlags.WRITE == 32

    def test_obsolete_2_is_64(self):
        assert ObjectFlags.OBSOLETE_2 == 64

    def test_fertile_is_128(self):
        assert ObjectFlags.FERTILE == 128

    def test_anonymous_is_256(self):
        assert ObjectFlags.ANONYMOUS == 256

    def test_invalid_is_512(self):
        assert ObjectFlags.INVALID == 512

    def test_recycled_is_1024(self):
        assert ObjectFlags.RECYCLED == 1024

    def test_is_intflag(self):
        """ObjectFlags should support bitwise operations."""
        wizard_programmer = ObjectFlags.WIZARD | ObjectFlags.PROGRAMMER
        assert int(wizard_programmer) == 6
        assert ObjectFlags.WIZARD in wizard_programmer

    def test_typical_wizard_flags(self):
        """A typical wizard player object has USER | PROGRAMMER | WIZARD."""
        wizard = ObjectFlags.USER | ObjectFlags.PROGRAMMER | ObjectFlags.WIZARD
        assert int(wizard) == 7

    def test_typical_room_flags(self):
        """A typical room might have READ (16) only."""
        room = ObjectFlags.READ
        assert int(room) == 16

    def test_aliases(self):
        """Backward compatibility aliases should match."""
        assert ObjectFlags.FLAG_USER == ObjectFlags.USER
        assert ObjectFlags.FLAG_WIZARD == ObjectFlags.WIZARD
        assert ObjectFlags.FLAG_FERTILE == ObjectFlags.FERTILE


class TestEnumIntegerConversion:
    """
    All enums must be usable as integers for database I/O.
    The writer uses int() on flags, the reader uses the enum constructor.
    """

    def test_property_flags_to_int(self):
        """Writer calls int(PropertyFlags) when serializing."""
        flags = PropertyFlags.READ | PropertyFlags.WRITE
        assert int(flags) == 3

    def test_property_flags_from_int(self):
        """Reader constructs PropertyFlags from int."""
        flags = PropertyFlags(3)
        assert PropertyFlags.READ in flags
        assert PropertyFlags.WRITE in flags

    def test_object_flags_to_int(self):
        """Writer calls int(ObjectFlags) when serializing."""
        flags = ObjectFlags.USER | ObjectFlags.PROGRAMMER | ObjectFlags.WIZARD
        assert int(flags) == 7

    def test_object_flags_from_int(self):
        """Reader constructs ObjectFlags from int."""
        flags = ObjectFlags(7)
        assert ObjectFlags.USER in flags
        assert ObjectFlags.PROGRAMMER in flags
        assert ObjectFlags.WIZARD in flags
