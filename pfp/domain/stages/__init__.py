"""PFP Stages, Modes, and Demos Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .cartesian_matrix_types import CartesianCoordinate, DimensionDefinition, SamplingSlice
    from .demos import CheckResult, DemoCatalog, DemoRunReceipt, DemoSpec
    from .mode_catalog import CLUSTER_MEMBERS, ManifestModeRef, ModeCatalog, ModeCatalogEntry, ModeCluster, ModeContractHeader
    from .modes import AuthorityEffect, ModeClusterRef, ModeFile, ModesManifest, ModeSummary, VerifierContract
    from .stages import HOST_STAGES, SEAT_BY_STAGE, STAGE_COUNT, STAGE_NAMES_BY_INDEX, BaseStageResponse, ChallengeReplay, ControllerStageRef, Executor, InputContract, ReplayOutcome, ResponseModel, Stage1Response, Stage2Response, Stage3Response, Stage4Response, Stage5Response, Stage6Response, Stage7Response, Stage8Response, Stage9Response, Stage10Response, Stage11Response, StageController, StageFile, StageName, StageTransition, WitnessReplay, replay_outcome

__all__ = ['AuthorityEffect', 'BaseStageResponse', 'CLUSTER_MEMBERS', 'ChallengeReplay', 'CartesianCoordinate', 'CheckResult', 'ControllerStageRef', 'DemoCatalog', 'DemoRunReceipt', 'DemoSpec', 'DimensionDefinition', 'Executor', 'InputContract', 'ManifestModeRef', 'ModeCatalog', 'ModeCatalogEntry', 'ModeCluster', 'ModeClusterRef', 'ModeContractHeader', 'ModeFile', 'ModesManifest', 'ModeSummary', 'HOST_STAGES', 'SEAT_BY_STAGE', 'STAGE_COUNT', 'ReplayOutcome', 'ResponseModel', 'STAGE_NAMES_BY_INDEX', 'Stage1Response', 'Stage2Response', 'Stage3Response', 'Stage4Response', 'Stage5Response', 'Stage6Response', 'Stage7Response', 'Stage8Response', 'Stage9Response', 'Stage10Response', 'Stage11Response', 'StageController', 'StageFile', 'StageName', 'StageTransition', 'VerifierContract', 'WitnessReplay', 'replay_outcome']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CartesianCoordinate': ('.cartesian_matrix_types', 'CartesianCoordinate'),
    'DimensionDefinition': ('.cartesian_matrix_types', 'DimensionDefinition'),
    'SamplingSlice': ('.cartesian_matrix_types', 'SamplingSlice'),
    'CheckResult': ('.demos', 'CheckResult'),
    'DemoCatalog': ('.demos', 'DemoCatalog'),
    'DemoRunReceipt': ('.demos', 'DemoRunReceipt'),
    'DemoSpec': ('.demos', 'DemoSpec'),
    'CLUSTER_MEMBERS': ('.mode_catalog', 'CLUSTER_MEMBERS'),
    'ManifestModeRef': ('.mode_catalog', 'ManifestModeRef'),
    'ModeCatalog': ('.mode_catalog', 'ModeCatalog'),
    'ModeCatalogEntry': ('.mode_catalog', 'ModeCatalogEntry'),
    'ModeCluster': ('.mode_catalog', 'ModeCluster'),
    'ModeContractHeader': ('.mode_catalog', 'ModeContractHeader'),
    'AuthorityEffect': ('.modes', 'AuthorityEffect'),
    'ModeClusterRef': ('.modes', 'ModeClusterRef'),
    'ModeFile': ('.modes', 'ModeFile'),
    'ModesManifest': ('.modes', 'ModesManifest'),
    'ModeSummary': ('.modes', 'ModeSummary'),
    'VerifierContract': ('.modes', 'VerifierContract'),
    'HOST_STAGES': ('.stages', 'HOST_STAGES'),
    'SEAT_BY_STAGE': ('.stages', 'SEAT_BY_STAGE'),
    'STAGE_COUNT': ('.stages', 'STAGE_COUNT'),
    'STAGE_NAMES_BY_INDEX': ('.stages', 'STAGE_NAMES_BY_INDEX'),
    'BaseStageResponse': ('.stages', 'BaseStageResponse'),
    'ChallengeReplay': ('.stages', 'ChallengeReplay'),
    'ControllerStageRef': ('.stages', 'ControllerStageRef'),
    'Executor': ('.stages', 'Executor'),
    'InputContract': ('.stages', 'InputContract'),
    'ReplayOutcome': ('.stages', 'ReplayOutcome'),
    'ResponseModel': ('.stages', 'ResponseModel'),
    'Stage1Response': ('.stages', 'Stage1Response'),
    'Stage2Response': ('.stages', 'Stage2Response'),
    'Stage3Response': ('.stages', 'Stage3Response'),
    'Stage4Response': ('.stages', 'Stage4Response'),
    'Stage5Response': ('.stages', 'Stage5Response'),
    'Stage6Response': ('.stages', 'Stage6Response'),
    'Stage7Response': ('.stages', 'Stage7Response'),
    'Stage8Response': ('.stages', 'Stage8Response'),
    'Stage9Response': ('.stages', 'Stage9Response'),
    'Stage10Response': ('.stages', 'Stage10Response'),
    'Stage11Response': ('.stages', 'Stage11Response'),
    'StageController': ('.stages', 'StageController'),
    'StageFile': ('.stages', 'StageFile'),
    'StageName': ('.stages', 'StageName'),
    'StageTransition': ('.stages', 'StageTransition'),
    'WitnessReplay': ('.stages', 'WitnessReplay'),
    'replay_outcome': ('.stages', 'replay_outcome'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
