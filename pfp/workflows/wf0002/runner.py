"""WF2 entry point; capabilities are selected by its own fixed contract."""

from pfp.infrastructure.workflow_runtime import WorkflowRuntime

from . import workflow

runtime = WorkflowRuntime(workflow)


def main(argv=None):
    return runtime.main(argv)
