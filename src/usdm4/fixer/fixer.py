import copy

from usdm4.ct.cdisc.library import Library
from usdm4.fixer.ct_fixer import CTFixer
from usdm4.fixer.fix_result import FixResult
from usdm4.fixer.id_fixer import IdFixer


class Fixer:
    """Fix errors in USDM JSON that need no judgement about the study.

    Each step is opt-in. The input dict is not modified: the fixed JSON is in
    the returned :class:`FixResult` with a log of every change and every
    problem left for a person to fix.
    """

    def __init__(self, library: Library | None = None):
        self._library = library

    def fix(self, data: dict, ids: bool = True, ct: bool = True) -> FixResult:
        result = FixResult(copy.deepcopy(data))
        if ids:
            IdFixer(result).fix()
        if ct:
            if self._library is None:
                raise ValueError("the ct step needs a CT library")
            CTFixer(result, self._library).fix()
        return result
