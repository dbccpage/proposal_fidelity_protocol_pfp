"""Injected dialogue rendering with explicit provider failure."""

from operations.domain.rop.result import Err, Ok, Refusal, Result

from .dialogue_personas import render_offline_dialogue
from .dialogue_ports import DialogueProvider


class DialogueSynthesizer:
    def __init__(self, provider: DialogueProvider | None = None) -> None:
        self.provider = provider

    def render_dialogue(self, speaker: str, cue: str, context: str = "") -> Result[str, Refusal]:
        speaker, cue = speaker.strip(), cue.strip()
        if self.provider is None:
            return Ok(render_offline_dialogue(speaker, cue))
        result = self.provider.generate(speaker, cue, context)
        if isinstance(result, Err):
            return result
        if not isinstance(result.value, str) or not result.value.strip():
            return Err(
                Refusal("DIALOGUE_REPLY_EMPTY", "Dialogue provider returned no text.", __name__)
            )
        return Ok(result.value.strip())
