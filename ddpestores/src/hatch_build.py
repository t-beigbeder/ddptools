import pathlib
import os

from hatchling.metadata.plugin.interface import MetadataHookInterface


class MetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        metadata["version"] = "0.1"
        metadata["dependencies"] = []
        with pathlib.Path(self.root, "requirements.txt").open() as if_:
            for ln in if_:
                if ln.startswith("${PYPIF}"):
                    # ${PYPIF}/../ddpbasics/ddpbasics-0.2-py3-none-any.whl
                    path = pathlib.Path(os.environ["PYPIF"], ln[len("${PYPIF}"):])
                    path.absolute()
                    # "ddpbasics @ /tools/pip_repo/ddpbasics/ddpbasics-0.1.1-py3-none-any.whl",
                    continue
                metadata["dependencies"].append(ln)
