"""WF1 entry point; shared runtime never selects another workflow."""

from pfp.infrastructure.workflow_runtime import WorkflowRuntime

from . import workflow

runtime = WorkflowRuntime(workflow)


def main(argv=None):
    return runtime.main(argv)
