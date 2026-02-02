import pathlib

from hatchling.metadata.plugin.interface import MetadataHookInterface


class MetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        metadata["version"] = "0.2"
        with pathlib.Path(self.root, "requirements.txt").open() as if_:
            metadata["dependencies"] = [ln for ln in if_]
