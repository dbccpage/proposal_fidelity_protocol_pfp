"""Compare one-pass prompt substitution with a naive sequence of replacements."""
import argparse
import json
from pathlib import Path
from string import Template
import sys
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

TEMPLATES = {
    "question_first": "Question: ${question}\nData: ${data}\n",
    "data_first": "Data: ${data}\nQuestion: ${question}\n",
}


class Request(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    template: Literal["question_first", "data_first"]
    question: Annotated[StrictStr, Field(min_length=1, max_length=512)]
    data: Annotated[StrictStr, Field(max_length=2048)]


class Result(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    rendered: StrictStr
    sequential: StrictStr
    differs: bool
    utf8_bytes: Annotated[StrictInt, Field(ge=0)]
    codepoints: Annotated[StrictInt, Field(ge=0)]
    provider_calls: Literal[0] = 0


def render(value):
    job = Request.model_validate(value)
    template = TEMPLATES[job.template]
    sequential = template.replace("${data}", job.data).replace("${question}", job.question)
    rendered = Template(template).substitute(question=job.question, data=job.data)
    return Result(rendered=rendered, sequential=sequential, differs=rendered != sequential,
                  utf8_bytes=len(rendered.encode("utf-8")), codepoints=len(rendered))


def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def default_job():
    return {"template": "question_first", "question": "Return the literal data.",
            "data": "The data contains ${question}; do not expand it."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="UTF-8 JSON request; at most 16384 bytes")
    args = parser.parse_args(argv)
    try:
        value = default_job()
        if args.input is not None:
            with args.input.open("rb") as stream:
                raw = stream.read(16385)
            if len(raw) > 16384:
                raise ValueError("Input exceeds 16384 bytes")
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)
        result = render(value)
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({"status": "INVALID", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(result.model_dump_json())
    return 0


if __name__ == "__main__":
    sys.exit(main())
