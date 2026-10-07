"""Hashes used by change control.

`content_hash` is the model hash with release bookkeeping removed (status, who and when, the
baselines and the change log). Releasing a harness therefore does not change it, so outputs that
were exported and reviewed before the release still count as current for the release gate.
"""

from harness_tool.core import edit
from harness_tool.core.commands import Delete, Op, Put
from harness_tool.core.io.layout import model_hash
from harness_tool.core.model import Project, evolve


def content_hash(project: Project) -> str:
    ops: list[Op] = [Delete("baselines", k) for k in sorted(project.baselines)]
    ops += [Delete("changelog", k) for k in sorted(project.changelog)]
    for h in sorted(project.harnesses.values(), key=lambda x: x.id):
        if (h.status, h.author, h.checker, h.approver, h.released_on) != (
            "draft",
            None,
            None,
            None,
            None,
        ):
            ops.append(
                Put(
                    "harnesses",
                    evolve(
                        h,
                        status="draft",
                        author=None,
                        checker=None,
                        approver=None,
                        released_on=None,
                    ),
                )
            )
    return model_hash(edit.clone_with(project, ops))
