import pathlib
import os

from hatchling.metadata.plugin.interface import MetadataHookInterface


class MetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        metadata["version"] = os.getenv("V_DDPT_V", "0.1")
        with pathlib.Path(self.root, "requirements.txt").open() as if_:
            metadata["dependencies"] = [ln for ln in if_]
