import array
import struct


class SqixFileError(Exception):
    pass


class SqixFileMaxEntriesError(SqixFileError):
    pass


class SqixFileMaxLenError(SqixFileError):
    pass


class SqixFileBase:
    MAX_ENTRIES = 16384
    MAX_ENTRY_LEN = 16384 * 1024
    HEADER_SIZE = 2 * MAX_ENTRIES * 4

    def __init__(self, path: str):
        self.path = path
        self.indexes = array.array("B", bytes(self.MAX_ENTRIES * 4))
        self.sizes = array.array("B", bytes(self.MAX_ENTRIES * 4))

    def _get_index_and_size(self, num: int) -> tuple[int, int]:
        offset = num * 4
        return int(struct.unpack_from("!I", self.indexes, offset)[0]), int(
            struct.unpack_from("!I", self.sizes, offset)[0]
        )


class SqixFileCreation(SqixFileBase):
    def __init__(self, path: str):
        super().__init__(path)
        self.ofd = None
        self.ofd = open(self.path, "wb")
        self.ofd.write(self.indexes)
        self.ofd.write(self.sizes)
        self.count = 0

    def __enter__(self):
        return self

    def _close(self):
        if self.ofd is None:
            return
        self.ofd.seek(0)
        self.ofd.write(self.indexes)
        self.ofd.write(self.sizes)
        self.ofd.close()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close()
        return None

    def _set_index(self, num: int, index: int):
        offset = num * 4
        struct.pack_into("!I", self.indexes, offset, index)

    def _set_size(self, num: int, size: int):
        offset = num * 4
        struct.pack_into("!I", self.sizes, offset, size)

    def len(self):
        if self.count == 0:
            return 0
        pi, ps = self._get_index_and_size(self.count - 1)
        return pi + ps - self.HEADER_SIZE

    def has_room(self, ln: int) -> bool:
        if ln > self.MAX_ENTRY_LEN:
            raise SqixFileError(
                f"file {self.path} incorrect entry size {ln} for entry number {self.count}"
            )
        if self.count == self.MAX_ENTRIES:
            return False
        if self.len() + ln > self.MAX_ENTRY_LEN:
            return False
        return True

    def add_entry(self, bs: bytes) -> int:
        if self.ofd is None:
            raise SqixFileError(
                f"file {self.path} raised an opening error"
            )
        count = self.count
        if count == self.MAX_ENTRIES:
            raise SqixFileMaxEntriesError(
                f"file {self.path} max entries {self.MAX_ENTRIES} exceeded"
            )
        if len(bs) > self.MAX_ENTRY_LEN:
            raise SqixFileError(
                f"file {self.path} incorrect entry size {len(bs)} for entry number {self.count}"
            )
        if self.len() + len(bs) > self.MAX_ENTRY_LEN:
            raise SqixFileMaxLenError(
                f"file {self.path} max len {self.MAX_ENTRY_LEN} exceeded"
                f" for entry number {self.count} size {len(bs)} ({self.len() + len(bs)})"
            )
        if len(bs) > 0:
            self.ofd.write(bs)
        if count > 0:
            pi, ps = self._get_index_and_size(count - 1)
            self._set_index(count, pi + ps)
        else:
            self._set_index(0, self.HEADER_SIZE)
        self._set_size(count, len(bs))
        self.count += 1
        return count

    def close(self):
        self._close()


class SqixFileConsumption(SqixFileBase):

    def __init__(self, path: str):
        super().__init__(path)
        self.ifd = None
        self.ifd = open(self.path, "rb")
        self.indexes = array.array("B")
        self.indexes.fromfile(self.ifd, self.MAX_ENTRIES * 4)
        self.sizes = array.array("B")
        self.sizes.fromfile(self.ifd, self.MAX_ENTRIES * 4)

    def __enter__(self):
        return self

    def _close(self):
        if self.ifd is None:
            return
        self.ifd.close()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close()
        return None

    def read_entry(self, index: int) -> bytes:
        if self.ifd is None:
            raise SqixFileError(
                f"file {self.path} raised an opening error"
            )
        if index >= self.MAX_ENTRIES:
            raise SqixFileError(f"file {self.path}: no such entry {index}")
        pi, ps = self._get_index_and_size(index)
        self.ifd.seek(pi)
        return self.ifd.read(ps)

    def close(self):
        self._close()
