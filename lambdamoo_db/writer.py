from io import TextIOWrapper
from typing import Any, SupportsInt

from attrs import asdict, define

from lambdamoo_db.enums import MooTypes

from . import templates
from .database import (
    CLEAR,
    TYPE_MAPPING,
    VM,
    Activation,
    Clear,
    MooDatabase,
    MooError,
    MooObject,
    ObjNum,
    Property,
    QueuedTask,
    SuspendedTask,
    Verb,
)


@define
class Writer:
    db: MooDatabase
    output_file: TextIOWrapper

    def write(self, text: str) -> None:
        self.output_file.write(text)

    def writeInt(self, i: SupportsInt) -> None:
        # Guard against bool (which is int subclass but semantically wrong)
        if isinstance(i, bool):
            raise TypeError("writeInt() does not accept bool values")
        # Convert to int and format (works for ints, IntFlag, IntEnum, etc.)
        # Note: no trailing newline - callers add newlines as needed
        self.write(f"{int(i)}")

    def writeString(self, s: str) -> None:
        self.write(f"{s}\n")

    def writeObj(self, obj: ObjNum) -> None:
        self.write(f"{int(obj)}")

    def writeFloat(self, f: float) -> None:
        # Match ToastStunt: DBL_DIG + 4 = 19 significant digits with %g format
        self.write(f"{f:.19g}")

    def writeBool(self, b: bool) -> None:
        self.writeInt(1 if b else 0)

    def writeRawValue(self, v: Any) -> None:
        """Write a value without type tag (just the raw data)."""
        if isinstance(v, bool):
            self.writeBool(v)
            self.write("\n")
        elif isinstance(v, MooError):
            self.writeInt(v)
            self.write("\n")
        elif isinstance(v, ObjNum):
            self.writeObj(v)
            self.write("\n")
        elif isinstance(v, int):
            self.writeInt(v)
            self.write("\n")
        elif isinstance(v, str):
            self.writeString(v)
        elif isinstance(v, float):
            self.writeFloat(v)
            self.write("\n")
        elif isinstance(v, list):
            self.writeListContents(v)
        elif isinstance(v, dict):
            self.writeMapContents(v)
        elif isinstance(v, Clear):
            pass  # CLEAR has no value
        elif v is None:
            pass  # NONE has no value
        elif isinstance(v, SupportsInt):
            self.writeInt(v)
            self.write("\n")
        else:
            raise TypeError(f"Unsupported value type: {type(v).__name__}")

    def writeListContents(self, lst: list[Any]) -> None:
        """Write list contents without type tag (count + items)."""
        self.writeInt(len(lst))
        self.write("\n")
        for item in lst:
            self.writeValue(item)

    def writeMapContents(self, m: dict[Any, Any]) -> None:
        """Write map contents without type tag (count + key/value pairs)."""
        self.writeInt(len(m))
        self.write("\n")
        for key, value in m.items():
            self.writeValue(key)
            self.writeValue(value)

    def writeList(self, lst: list[Any]) -> None:
        """Write a type-tagged list."""
        self.writeInt(MooTypes.LIST)
        self.write("\n")
        self.writeListContents(lst)

    def writeMap(self, m: dict[Any, Any]) -> None:
        """Write a type-tagged map."""
        self.writeInt(MooTypes.MAP)
        self.write("\n")
        self.writeMapContents(m)

    def writeValue(self, v: Any) -> None:
        """Write a type-tagged value (type tag on its own line, then value)."""
        # Determine type tag
        if isinstance(v, bool):
            self.writeInt(MooTypes.BOOL)
            self.write("\n")
            self.writeBool(v)
        elif isinstance(v, MooError):
            self.writeInt(MooTypes.ERR)
            self.write("\n")
            self.writeInt(v)
            self.write("\n")
        elif isinstance(v, ObjNum):
            self.writeInt(MooTypes.OBJ)
            self.write("\n")
            self.writeObj(v)
            self.write("\n")
        elif isinstance(v, int):
            self.writeInt(MooTypes.INT)
            self.write("\n")
            self.writeInt(v)
            self.write("\n")
        elif isinstance(v, str):
            self.writeInt(MooTypes.STR)
            self.write("\n")
            self.writeString(v)
        elif isinstance(v, float):
            self.writeInt(MooTypes.FLOAT)
            self.write("\n")
            self.writeFloat(v)
            self.write("\n")
        elif isinstance(v, list):
            self.writeInt(MooTypes.LIST)
            self.write("\n")
            self.writeListContents(v)
        elif isinstance(v, dict):
            self.writeInt(MooTypes.MAP)
            self.write("\n")
            self.writeMapContents(v)
        elif isinstance(v, Clear):
            self.writeInt(MooTypes.CLEAR)
            self.write("\n")
        elif v is None:
            self.writeInt(MooTypes.NONE)
            self.write("\n")
        elif isinstance(v, SupportsInt):
            self.writeInt(MooTypes.INT)
            self.write("\n")
            self.writeInt(v)
            self.write("\n")
        else:
            raise TypeError(f"Unsupported value type: {type(v).__name__}")

    def writeDatabase(self) -> None:
        self.writeString(templates.version.format(version=17))
        self.writePlayers()
        self.writePending()
        self.writeClocks()
        self.writeTaskQueue()
        self.writeSuspendedTasks()
        self.writeInterruptedTasks()
        self.writeConnections()
        self.writeObjects()
        self.writeVerbs()

    def writePlayers(self) -> None:
        self.writeInt(len(self.db.players))
        self.write("\n")
        for player in self.db.players:
            self.writeInt(player)
            self.write("\n")

    def writePending(self) -> None:
        self.writeString(templates.pending_values_count.format(count=0))

    def writeObjects(self) -> None:
        # Write total count (includes recycled slots)
        self.writeInt(self.db.total_objects)
        self.write("\n")
        # Write objects in order, including recycled placeholders
        for obj_id in range(self.db.total_objects):
            if obj_id in self.db.recycled_objects:
                self.writeString(f"# {obj_id} recycled")
            elif obj_id in self.db.objects:
                self.writeObject(self.db.objects[obj_id])
            else:
                raise ValueError(f"Object {obj_id} missing and not marked recycled")
        # Write 0 to signal end of anonymous objects
        self.writeInt(0)
        self.write("\n")

    def writeObject(self, obj: MooObject) -> None:
        obj_num = obj.id
        self.writeString(f"#{obj_num}")
        self.writeString(obj.name)
        self.writeInt(obj.flags)
        self.write("\n")
        self.writeInt(obj.owner)
        self.write("\n")
        self.writeValue(obj.location)
        self.writeValue(obj.last_move)
        self.writeValue(obj.contents)
        # Single parent → ObjNum, multiple parents → list
        if len(obj.parents) == 1:
            self.writeValue(ObjNum(obj.parents[0]))
        else:
            self.writeValue(obj.parents)
        self.writeValue(obj.children)
        self.writeCollection(obj.verbs, writer=self.writeVerbMetadata)
        self.write_properties(obj)

    def writeVerbMetadata(self, verb: Verb) -> None:
        self.writeString(verb.name)
        self.writeInt(verb.owner)
        self.write("\n")
        self.writeInt(verb.perms)
        self.write("\n")
        self.writeInt(verb.preps)
        self.write("\n")

    def write_properties(self, obj: MooObject) -> None:
        # Write propdefs (properties DEFINED on this object, with names)
        self.writeInt(obj.propdefs_count)
        self.write("\n")
        for prop in obj.properties[:obj.propdefs_count]:
            self.writeString(prop.propertyName)
        # Write all property values (defined + inherited)
        self.writeInt(len(obj.properties))
        self.write("\n")
        for prop in obj.properties:
            self.writeProperty(prop)

    def writeProperty(self, prop: Property):
        self.writeValue(prop.value)
        self.writeInt(prop.owner)
        self.write("\n")
        self.writeInt(prop.perms)
        self.write("\n")

    def writeVerbs(self) -> None:
        # Count verbs with programs (None = no program, [] = empty program)
        verbs_with_programs = [v for v in self.db.all_verbs() if v.code is not None]
        self.writeInt(len(verbs_with_programs))
        self.write("\n")
        # Write each verb program
        for verb in verbs_with_programs:
            self.writeVerb(verb)

    def writeVerb(self, verb: Verb) -> None:
        objnum = verb.object
        object = self.db.objects[objnum]
        index = object.verbs.index(verb)
        vloc = f"#{objnum}:{index}"
        self.writeString(vloc)
        self.writeCode(verb.code)

    def writeCode(self, code: list[str]) -> None:
        for line in code:
            self.writeString(line)
        self.writeString(".")

    def writeCollection(self, collection, template=None, writer=None):
        if writer is None:
            writer = self.writeString
        if template is None:
            self.writeInt(len(collection))
            self.write("\n")
        else:
            self.writeString(template.format(count=len(collection)))
        for item in collection:
            writer(item)

    def writeClocks(self):
        self.writeCollection(self.db.clocks, templates.clock_count)

    def writeTaskQueue(self):
        self.writeCollection(self.db.queuedTasks, templates.task_count, self.writeQueuedTask)

    def writeQueuedTask(self, task: QueuedTask) -> None:
        taskHeader = templates.task_header.format(**asdict(task))
        self.writeString(taskHeader)
        self.writeActivationAsPI(task.activation)
        self.writeRtEnv(task.rtEnv)
        self.writeCode(task.code)

    def writeActivationAsPI(self, activation: Activation):
        # Write pre-header values (matched to read_activation_as_pi in reader)
        # These values preserve type info from the original file
        # 1. temp_value (first value, often discarded during interpretation)
        self.writeValue(activation.temp_value)
        # 2. temp_this (pre-header this, with type info)
        self.writeValue(activation.temp_this)
        # 3. temp_vloc (pre-header vloc, with type info)
        self.writeValue(activation.temp_vloc)
        # 4. threaded (just an int, no type tag for v17)
        self.writeInt(activation.threaded if activation.threaded is not None else 0)
        self.write("\n")
        # Activation header line
        activation_header = templates.activation_header.format(**asdict(activation))
        self.writeString(activation_header)
        # Argstr placeholders
        self.writeString("No")
        self.writeString("More")
        self.writeString("Parse")
        self.writeString("Infos")
        self.writeString(activation.verb)
        self.writeString(activation.verbname)

    def writeActivation(self, activation):
        langver = templates.langver.format(version=17)
        self.writeString(langver)
        self.writeActivationAsPI(activation)

    def writeSuspendedTasks(self):
        self.writeCollection(self.db.suspendedTasks, templates.suspended_task_count, self.writeSuspendedTask)

    def writeInterruptedTasks(self):
        # For now, write 0 interrupted tasks (format: "{count:d} interrupted tasks")
        self.writeString(templates.interrupted_task_count.format(count=0))

    def writeSuspendedTask(self, task: SuspendedTask):
        header = templates.suspended_task_header.format(**asdict(task))
        self.writeString(header)
        self.writeVM(task.vm)

    def writeVM(self, vm: VM):
        self.writeValue(vm.locals)

    def writeRtEnv(self, env: dict[str, Any]):
        header = templates.var_count.format(count=len(env))
        self.writeString(header)
        for name, value in env.items():
            self.writeString(name)
            moo_type = TYPE_MAPPING.get(type(value), MooTypes.INT)
            self.writeInt(moo_type)
            self.write("\n")
            if moo_type != MooTypes.NONE:
                self.writeRawValue(value)

    def writeConnections(self):
        # Connection data is not preserved, just write empty count
        self.writeString("0 active connections with listeners")


def dump(db: MooDatabase, f: TextIOWrapper) -> None:
    writer = Writer(db=db, output_file=f)
    writer.writeDatabase()
