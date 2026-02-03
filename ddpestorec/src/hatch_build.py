import pathlib

from hatchling.metadata.plugin.interface import MetadataHookInterface


class MetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        metadata["dependencies"] = []
        with pathlib.Path(self.root, "requirements.txt").open() as if_:
            for ln in if_:
                ln = ln[:-1]
                if not ln.startswith("../"):
                    metadata["dependencies"].append(ln)
                    continue
                # ../ddpbasics => ddpbasics @ file:///path/to/ddpbasics
                metadata["dependencies"].append(f"{ln[3:]} @ file://{str(pathlib.Path(ln).resolve())}")
        with open("/tmp/tbe.log", "w") as of:
            of.write(f"dependencies metadata hook {metadata['dependencies']}\n")
