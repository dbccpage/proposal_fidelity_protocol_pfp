"""Local Hugging Face and simulated mechanism adapter with attention distractor key masking and logit intervention.

AuthorityEffect: None.
Clean Architecture Layer: Infrastructure Adapter
"""

from __future__ import annotations

import json
import math
import time
import uuid
from contextlib import contextmanager
from hashlib import sha256
from typing import Any, Callable

from pfp.domain.ports.decode_control_port import (
    ControlKind,
    DecodeControlPort,
    DecodeControlReceipt,
    DecodeControlSpec,
)
from pfp.ffi import get_default_host


class LocalHfMechanismAdapter(DecodeControlPort):
    """Local attention and logit intervention adapter.

    Executes simulated or local HuggingFace model generation with exact
    token filtering under carrier masks and logit bias steering.
    """

    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-7B-Instruct",
        generator: Callable[[str, DecodeControlSpec], tuple[str, list[int]]] | None = None,
        *,
        fixture_mode: bool = False,
    ) -> None:
        self._model_id = model_id
        if type(fixture_mode) is not bool:
            raise TypeError("fixture_mode must be an exact bool")
        self._generator = generator or (self._default_mock_generator if fixture_mode else None)

    def apply_decode_control(
        self,
        spec: DecodeControlSpec,
        prompt: str,
        case_id: str = "case_unknown",
    ) -> tuple[str, DecodeControlReceipt]:
        if self._generator is None:
            raise RuntimeError(
                "EXECUTION_UNAVAILABLE: configure a generator or explicit fixture_mode"
            )
        text, token_ids = self._generator(prompt, spec)

        # Enforce carrier mask if requested
        honored = True
        if spec.control_kind == ControlKind.CARRIER_MASK and spec.carrier_mask is not None:
            allowed = set(spec.carrier_mask.allowed_tokens)
            for t in token_ids:
                if t not in allowed:
                    honored = False
                    break

        receipt_id = f"rcpt_{uuid.uuid4().hex[:12]}"

        allowed_tuple = (
            tuple(sorted(spec.carrier_mask.allowed_tokens)) if spec.carrier_mask is not None else ()
        )
        logit_biases_tuple = (
            tuple(sorted(spec.logit_bias.biases.items())) if spec.logit_bias is not None else ()
        )
        grammar_sha256 = spec.grammar_mask.grammar_sha256 if spec.grammar_mask is not None else None

        receipt = DecodeControlReceipt(
            receipt_id=receipt_id,
            case_id=case_id,
            control_kind=spec.control_kind.value,
            output_tokens=tuple(token_ids),
            allowed_tokens=allowed_tuple,
            logit_biases=logit_biases_tuple,
            grammar_sha256=grammar_sha256,
            honored=honored,
            authority_effect="None",
        )
        return text, receipt

    def verify_decode_receipt(
        self,
        receipt: DecodeControlReceipt,
    ) -> dict[str, Any]:
        """Verify the receipt outside the model using native Rust verifier."""
        try:
            host = get_default_host()
            outcome = host.verify_decode_receipt(receipt.to_dict())
            if outcome.is_ok:
                val = outcome.unwrap()
                return dict(val.get("result", val))
            refusal = outcome.unwrap_err()
            return {
                "status": "REFUSAL",
                "refusal_code": getattr(refusal, "code", "VERIFICATION_ERROR"),
                "detail": str(refusal),
                "authority_effect": "None",
            }
        except Exception as exc:
            return {
                "status": "REFUSAL",
                "refusal_code": "VERIFIER_UNAVAILABLE",
                "detail": type(exc).__name__,
                "authority_effect": "None",
            }

    @staticmethod
    def _default_mock_generator(prompt: str, spec: DecodeControlSpec) -> tuple[str, list[int]]:
        """Deterministic mock generator honoring spec constraints for offline verification."""
        if spec.control_kind == ControlKind.CARRIER_MASK and spec.carrier_mask:
            tokens = list(sorted(spec.carrier_mask.allowed_tokens))[
                : min(5, len(spec.carrier_mask.allowed_tokens))
            ]
            return "CONSISTENT", tokens
        return "CONSISTENT", [101, 102, 103]


class HfLocalRunner:
    """Injected, pinned eager HF model with reversible Llama-family interventions.

    Loading/downloading belongs to outer composition. This runner uses actual
    tokenizer offsets, logits and activations; it never substitutes fixture output.
    Finite token tries enforce a declared language, not semantic correctness.
    """

    def __init__(self, model, tokenizer, *, model_id, revision):
        import torch
        if (not model_id or type(revision) is not str or len(revision) != 40
                or any(c not in "0123456789abcdef" for c in revision)):
            raise ValueError("LOCAL_MODEL_REVISION_REQUIRED")
        if getattr(model.config, "_attn_implementation", None) != "eager":
            raise ValueError("EAGER_ATTENTION_REQUIRED")
        if not getattr(tokenizer, "is_fast", False):
            raise ValueError("EXACT_TOKENIZER_OFFSETS_REQUIRED")
        self.model, self.tokenizer = model.eval(), tokenizer
        self.layers = model.model.layers
        self.torch = torch
        self.pipeline = dict(model_id=model_id, revision=revision, dtype=str(next(model.parameters()).dtype),
            attention="eager", tokenizer_sha256=sha256(json.dumps(tokenizer.get_vocab(),
                sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            runtime=torch.__version__, authority_effect="None")

    def render(self, turn):
        return self.tokenizer.apply_chat_template([dict(role="system", content=turn.prompt.system),
            dict(role="user", content=turn.prompt.user)], tokenize=False, add_generation_prompt=True)

    def carrier_positions(self, text, spans):
        mapped = self.tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
        if any(type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text) for a, b in spans):
            raise ValueError("INVALID_CARRIER_CHARACTER_SPAN")
        return tuple(i for i, (a, b) in enumerate(mapped["offset_mapping"])
            if a < b and any(a < end and start < b for start, end in spans))

    @contextmanager
    def interventions(self, *, attention=None, heads=None, patch=None, residual=None):
        torch, handles, readouts = self.torch, [], []
        def layer_id(value):
            if type(value) is not int or not 0 <= value < len(self.layers):
                raise ValueError("LAYER_ID_OUT_OF_RANGE")
        def bounded(value, low, high):
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError("INTERVENTION_SCALAR_OUT_OF_RANGE")
        if attention is not None:
            selected_layers = attention["layers"]
            if (type(selected_layers) not in (tuple, list) or not selected_layers
                    or len(set(selected_layers)) != len(selected_layers)):
                raise ValueError("NONEMPTY_UNIQUE_ATTENTION_LAYERS_REQUIRED")
            for value in selected_layers:
                layer_id(value)
            bounded(attention["delta"], 0, 16)
        for spec in (heads, patch, residual):
            if spec is not None:
                layer_id(spec["layer"])
        if heads is not None:
            if type(heads["heads"]) not in (tuple, list) or not heads["heads"] or len(set(heads["heads"])) != len(heads["heads"]):
                raise ValueError("NONEMPTY_UNIQUE_HEADS_REQUIRED")
            bounded(heads["alpha"], 0, 3)
        if residual is not None:
            bounded(residual["alpha"], -4, 4)
        try:
            for index, layer in enumerate(self.layers):
                if attention is not None and index in attention["layers"]:
                    delta, positions = float(attention["delta"]), tuple(attention["positions"])
                    if not positions or any(type(p) is not int or p < 0 for p in positions):
                        raise ValueError("ATTENTION_KEY_POSITIONS_REQUIRED")

                    def bias(_module, args, kwargs, *, delta=delta, positions=positions, index=index):
                        mask = kwargs.get("attention_mask")
                        if mask is None or mask.ndim != 4 or max(positions) >= mask.shape[-1]:
                            raise ValueError("EAGER_ATTENTION_MASK_UNAVAILABLE")
                        changed = mask.clone()
                        changed[..., list(positions)] += delta
                        readouts.append(dict(kind="attention", layer=index, delta=delta,
                            changed_entries=int(torch.count_nonzero(changed != mask).item())))
                        return args, {**kwargs, "attention_mask": changed}

                    handles.append(layer.self_attn.register_forward_pre_hook(bias, with_kwargs=True))
                selected = tuple(heads["heads"]) if heads is not None and heads["layer"] == index else ()
                patched = patch is not None and patch["layer"] == index
                if selected or patched:
                    count = self.model.config.num_attention_heads
                    if any(type(h) is not int or not 0 <= h < count for h in selected):
                        raise ValueError("HEAD_ID_OUT_OF_RANGE")

                    def project(_module, args, *, selected=selected, patched=patched, index=index):
                        original = args[0]
                        value = original.clone().reshape(*original.shape[:-1], count, -1)
                        if selected:
                            value[..., list(selected), :] *= float(heads["alpha"])
                        if patched:
                            head = patch["head"]
                            if type(head) is not int or not 0 <= head < count:
                                raise ValueError("HEAD_ID_OUT_OF_RANGE")
                            source = patch["value"].to(value)
                            if source.shape != value[..., -1, head, :].shape:
                                raise ValueError("HEAD_PATCH_SHAPE_MISMATCH")
                            value[..., -1, head, :] = source
                        output = value.reshape_as(original)
                        readouts.append(dict(kind="head", layer=index,
                            changed_norm=float((output - original).norm().item())))
                        return (output, *args[1:])

                    handles.append(layer.self_attn.o_proj.register_forward_pre_hook(project))
                if residual is not None and residual["layer"] == index:
                    def add(_module, _args, output, *, index=index):
                        hidden = output[0] if isinstance(output, tuple) else output
                        vector = residual["vector"].to(hidden)
                        if vector.shape != hidden.shape[-1:]:
                            raise ValueError("RESIDUAL_VECTOR_SHAPE_MISMATCH")
                        changed = hidden.clone()
                        changed[:, -1, :] += float(residual["alpha"]) * vector
                        readouts.append(dict(kind="residual", layer=index,
                            changed_norm=float((changed - hidden).norm().item())))
                        return (changed, *output[1:]) if isinstance(output, tuple) else changed

                    handles.append(layer.register_forward_hook(add))
            yield readouts
        finally:
            for handle in reversed(handles):
                handle.remove()

    def forward(self, text, *, attention=None, heads=None, patch=None, residual=None):
        inputs = self.tokenizer(text, return_tensors="pt", add_special_tokens=False)
        with self.torch.inference_mode(), self.interventions(attention=attention, heads=heads,
                patch=patch, residual=residual) as readouts:
            output = self.model(**inputs, use_cache=False)
        return output.logits[:, -1, :].detach().clone(), readouts

    def capture(self, text, *, layer, kind, head=None):
        if type(layer) is not int or not 0 <= layer < len(self.layers):
            raise ValueError("LAYER_ID_OUT_OF_RANGE")
        values = []
        if kind == "head":
            count = self.model.config.num_attention_heads
            if type(head) is not int or not 0 <= head < count:
                raise ValueError("HEAD_ID_OUT_OF_RANGE")
            def take(_module, args):
                value = args[0].reshape(*args[0].shape[:-1], count, -1)
                values.append(value[:, -1, head, :].detach().clone())
            handle = self.layers[layer].self_attn.o_proj.register_forward_pre_hook(take)
        elif kind == "residual":
            def take(_module, _args, output):
                value = output[0] if isinstance(output, tuple) else output
                values.append(value[:, -1, :].detach().clone())
            handle = self.layers[layer].register_forward_hook(take)
        else:
            raise ValueError("ACTIVATION_KIND_UNAVAILABLE")
        try:
            self.forward(text)
        finally:
            handle.remove()
        return values[0]

    def generate(self, turn, *, seed, max_tokens=128, temperature=0, allowed_replies=None,
                 attention=None, heads=None, patch=None, residual=None, use_cache=True,
                 logit_bias=None):
        from transformers import LogitsProcessor, LogitsProcessorList
        torch = self.torch
        if type(seed) is not int or type(max_tokens) is not int or not 1 <= max_tokens <= 512:
            raise ValueError("BOUNDED_LOCAL_GENERATION_REQUIRED")
        if type(temperature) not in (int, float) or not 0 <= temperature <= 2:
            raise ValueError("BOUNDED_TEMPERATURE_REQUIRED")
        text = self.render(turn)
        inputs = self.tokenizer(text, return_tensors="pt", add_special_tokens=False)
        prompt_length = inputs["input_ids"].shape[1]
        if prompt_length + max_tokens > self.model.config.max_position_embeddings:
            raise ValueError("LOCAL_CONTEXT_LIMIT")
        processors = LogitsProcessorList()
        logit_readouts = []
        if logit_bias is not None:
            if (type(logit_bias) is not dict or not logit_bias or any(type(token) is not int
                    or not 0 <= token < self.model.config.vocab_size or type(delta) not in (int, float)
                    or not -16 <= delta <= 16 for token, delta in logit_bias.items())):
                raise ValueError("BOUNDED_LOGIT_BIAS_REQUIRED")
            class Bias(LogitsProcessor):
                def __call__(self, input_ids, scores):
                    result = scores.clone()
                    for token, delta in logit_bias.items():
                        result[:, token] += delta
                    logit_readouts.append(dict(changed_entries=int(torch.count_nonzero(result != scores)),
                        biases=logit_bias))
                    return result
            processors.append(Bias())
        if allowed_replies is not None:
            if type(allowed_replies) is not list or not 1 <= len(allowed_replies) <= 1024:
                raise ValueError("BOUNDED_FINITE_LANGUAGE_REQUIRED")
            vocabulary = [tuple(self.tokenizer.encode(reply, add_special_tokens=False)) for reply in allowed_replies]
            eos = self.tokenizer.eos_token_id
            if not vocabulary or any(not row for row in vocabulary) or eos is None:
                raise ValueError("FINITE_TOKEN_LANGUAGE_UNAVAILABLE")
            class Trie(LogitsProcessor):
                def __call__(self, input_ids, scores):
                    prefix = tuple(input_ids[0, prompt_length:].tolist())
                    allowed = {row[len(prefix)] for row in vocabulary if len(row) > len(prefix) and row[:len(prefix)] == prefix}
                    if prefix in vocabulary:
                        allowed.add(eos)
                    if not allowed:
                        raise ValueError("FINITE_TOKEN_PREFIX_REFUSED")
                    masked = torch.full_like(scores, float("-inf"))
                    masked[:, list(allowed)] = scores[:, list(allowed)]
                    return masked
            processors.append(Trie())
        began = time.monotonic()
        with torch.random.fork_rng(), torch.inference_mode(), self.interventions(attention=attention,
                heads=heads, patch=patch, residual=residual) as readouts:
            torch.manual_seed(seed)
            kwargs = dict(max_new_tokens=max_tokens, do_sample=temperature > 0,
                use_cache=use_cache, logits_processor=processors,
                pad_token_id=self.tokenizer.eos_token_id, eos_token_id=self.tokenizer.eos_token_id)
            if temperature > 0:
                kwargs["temperature"] = float(temperature)
            generated = self.model.generate(**inputs, **kwargs)[0, prompt_length:].tolist()
        raw = self.tokenizer.decode(generated, skip_special_tokens=True).encode("utf-8")
        return dict(raw_reply=raw, token_ids=generated, seed=seed, temperature=temperature,
            prompt=text, prompt_sha256=sha256(text.encode()).hexdigest(), pipeline=self.pipeline,
            input_tokens=int(prompt_length), output_tokens=len(generated), logit_readouts=logit_readouts,
            intervention_readouts=readouts, elapsed_seconds=time.monotonic() - began,
            provider_calls=0, billed_usd="0", compute_pricing="UNPRICED_LOCAL_CPU",
            enforcement="FINITE_TOKEN_TRIE" if allowed_replies is not None else "NONE",
            language_sha256=sha256(json.dumps(allowed_replies, separators=(",", ":")).encode()).hexdigest()
                if allowed_replies is not None else None)

    def cache_parity(self, text, *, steps=4, keep_positions=None):
        """Compare real incremental-cache and full recomputation token for token.

        Optional key/value selection is an exploratory surgery. A mismatch is
        returned literally; it cannot license F-reuse or protected-text deletion.
        """
        torch = self.torch
        if type(steps) is not int or not 1 <= steps <= 16:
            raise ValueError("BOUNDED_CACHE_PROBE_REQUIRED")
        inputs = self.tokenizer(text, return_tensors="pt", add_special_tokens=False)
        ids = inputs["input_ids"]
        with torch.inference_mode():
            prefix = self.model(input_ids=ids, use_cache=True)
            cache, cached, full = prefix.past_key_values, [], []
            if keep_positions is not None:
                if not keep_positions or any(type(p) is not int or not 0 <= p < ids.shape[1] for p in keep_positions) or len(set(keep_positions)) != len(keep_positions):
                    raise ValueError("CACHE_POSITIONS_INVALID")
                selection = torch.tensor(sorted(keep_positions))
                for layer in cache.layers:
                    layer.keys = layer.keys.index_select(-2, selection)
                    layer.values = layer.values.index_select(-2, selection)
            next_logits = prefix.logits[:, -1, :]
            actual = ids
            for _ in range(steps):
                token = next_logits.argmax(-1, keepdim=True)
                reference = self.model(input_ids=actual, use_cache=False).logits[:, -1, :].argmax(-1, keepdim=True)
                cached.append(int(token.item()))
                full.append(int(reference.item()))
                actual = torch.cat((actual, token), dim=1)
                out = self.model(input_ids=token, past_key_values=cache, use_cache=True,
                    cache_position=torch.tensor([actual.shape[1] - 1]))
                cache, next_logits = out.past_key_values, out.logits[:, -1, :]
        return dict(cached_token_ids=cached, full_recompute_token_ids=full, token_exact=cached == full,
            kept_positions=keep_positions, original_tokens=int(ids.shape[1]), provider_calls=0,
            scope="FINITE_CACHE_MECHANICS_NOT_C007_LONG_HORIZON_RESULT")
