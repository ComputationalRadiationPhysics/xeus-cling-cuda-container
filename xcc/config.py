"""The config object provides information for the different recipe generator stages.

"""

from typing import List

# TODO: the config object is planed for the next comment
# at the moment, it just provides keep_build and the paths of keep_build to
# solve some type hint problems
class XCC_Config:
    def __init__(self, keep_build=False):
        """Setup the configuration object

        :param keep_build: if false, delete source and build of the different projects
        :type keep_build: bool

        """
        self.keep_build: bool = keep_build
        self.paths_to_delete: List[str] = []
