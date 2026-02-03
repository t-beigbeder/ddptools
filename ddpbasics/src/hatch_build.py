import pathlib

from hatchling.metadata.plugin.interface import MetadataHookInterface


class MetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        with pathlib.Path(self.root, "requirements.txt").open() as if_:
            metadata["dependencies"] = [ln for ln in if_]
