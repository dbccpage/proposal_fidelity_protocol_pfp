"""Pilot 24: bounded checking of a supplied mock repair sequence, not a model."""
import argparse
import json
from pathlib import Path
import sys
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, TypeAdapter
import yaml

TaskId = Annotated[StrictStr, Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")]
Operand = Annotated[StrictInt, Field(ge=-1000, le=1000)]
RawReply = Annotated[StrictStr, Field(max_length=2048)]


class Strict(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, revalidate_instances="always")


class Task(Strict):
    task_id: TaskId
    operation: Literal["add"]
    left: Operand
    right: Operand


class Answer(Strict):
    kind: Literal["answer"]
    task_id: TaskId
    value: Annotated[StrictInt, Field(ge=-10000, le=10000)]


class Abstention(Strict):
    kind: Literal["abstain"]
    task_id: TaskId
    reason: Annotated[StrictStr, Field(min_length=1, max_length=80, pattern=r"\S")]


Reply = TypeAdapter(Annotated[Answer | Abstention, Field(discriminator="kind")])


class Job(Strict):
    task: Task
    max_attempts: Annotated[StrictInt, Field(ge=1, le=3)]
    responses: Annotated[tuple[RawReply, ...], Field(max_length=4, strict=False)]


class Attempt(Strict):
    ordinal: Annotated[StrictInt, Field(ge=1, le=3)]
    outcome: Literal["MALFORMED", "WRONG_TASK", "WRONG_VALUE", "ABSTAINED", "ACCEPTED"]
    raw: RawReply
    detail: StrictStr


class Result(Strict):
    task: Task
    status: Literal["ACCEPTED", "EXHAUSTED"]
    stop_reason: Literal["correct_answer", "attempt_limit", "sequence_end"]
    answer: StrictInt | None
    attempts: Annotated[tuple[Attempt, ...], Field(strict=False)]
    mock_calls: Annotated[StrictInt, Field(ge=0, le=3)]
    provider_calls: Annotated[StrictInt, Field(ge=0, le=0)] = 0
    cost_microusd: Annotated[StrictInt, Field(ge=0, le=0)] = 0


def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError("Non-JSON constant: " + value)


def require_utf8(raw):
    """Return raw unchanged, or raise ValueError when it holds a lone surrogate or other non-UTF-8 text."""
    try:
        raw.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("Text is not encodable as UTF-8: " + str(error)) from None
    return raw


def parse(raw):
    return json.loads(require_utf8(raw), object_pairs_hook=unique_pairs, parse_constant=invalid_constant)


def replay(value):
    job = Job.model_validate(value)
    raw_replies = tuple(job.responses)
    expected = job.task.left + job.task.right
    attempts = []
    for ordinal, raw in enumerate(raw_replies[:job.max_attempts], 1):
        detail = ""
        try:
            reply = Reply.validate_python(parse(raw))
        except (ValueError, RecursionError) as error:
            outcome, detail = "MALFORMED", str(error)
        else:
            if reply.task_id != job.task.task_id:
                outcome = "WRONG_TASK"
            elif isinstance(reply, Abstention):
                outcome = "ABSTAINED"
            elif reply.value != expected:
                outcome = "WRONG_VALUE"
            else:
                outcome = "ACCEPTED"
        attempts.append(Attempt(ordinal=ordinal, outcome=outcome, raw=raw, detail=detail))
        if outcome == "ACCEPTED":
            return Result(task=job.task, status="ACCEPTED", stop_reason="correct_answer", answer=expected,
                          attempts=tuple(attempts), mock_calls=len(attempts))
    reason = "attempt_limit" if len(attempts) == job.max_attempts else "sequence_end"
    return Result(task=job.task, status="EXHAUSTED", stop_reason=reason, answer=None,
                  attempts=tuple(attempts), mock_calls=len(attempts))


def default_job():
    return {"task": {"task_id": "addition", "operation": "add", "left": 19, "right": 23},
            "max_attempts": 2, "responses": ['{"kind":"answer","task_id":"addition","value":41}',
                                             '{"kind":"answer","task_id":"addition","value":42}']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="UTF-8 JSON job, at most 32768 bytes")
    parser.add_argument("--yaml", action="store_true", help="Print the runtime result as YAML")
    args = parser.parse_args(argv)
    try:
        value = default_job()
        if args.input is not None:
            with args.input.open("rb") as stream:
                raw = stream.read(32769)
            if len(raw) > 32768:
                raise ValueError("Input exceeds 32768 bytes")
            value = parse(raw.decode("utf-8"))
        result = replay(value).model_dump(mode="json")
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({"status": "INVALID", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(yaml.safe_dump(result, sort_keys=True) if args.yaml else json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ACCEPTED" else 1


if __name__ == "__main__":
    sys.exit(main())
