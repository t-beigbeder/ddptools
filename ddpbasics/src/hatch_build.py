import pathlib
import os

from hatchling.metadata.plugin.interface import MetadataHookInterface


class MetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        v = os.getenv("V_DDPT_V")
        if not v:
            raise ValueError("V_DDPT_V environment variable shoud be set before building this package")
        metadata["version"] = v
        with pathlib.Path(self.root, "requirements.txt").open() as if_:
            metadata["dependencies"] = [ln for ln in if_]
