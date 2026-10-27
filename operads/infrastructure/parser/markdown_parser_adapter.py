"""Lossless CommonMark-aware parser with byte-exact spans and fenced declarations."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import List

import yaml

from operations.domain.rop.result import Err, Ok, Result

from ...application.ports.skill_document_parser_port import SkillDocumentParserPort
from ...domain.entities.composition_v3 import CompositionV3
from ...domain.entities.operation_v3 import OperationV3, PortSpecV3
from ...domain.entities.skill_document_v3 import DocumentLeafNode, SkillDocumentV3
from ...domain.errors.domain_errors import DomainInvariantError, OeopDomainError
from ...domain.value_objects.authority import AuthorityEffect
from ...domain.value_objects.byte_span import SourceByteSpan
from ...domain.value_objects.content_digest import ContentDigest
from ...domain.value_objects.identifier import (
    ColourId,
    DocumentId,
    OperandId,
    OperationId,
    SchemaRef,
    SkillId,
)
from ...domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)
from ...domain.value_objects.operands import InstructionOperand
from ..capability_catalog_compiler import CatalogCompileRefusal, _frontmatter

_LINE_PATTERN = re.compile(r"[^\r\n]*(?:\r\n|\r|\n|$)")
_FENCE_OPENER = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
_DECLARATION_INFOS = {"oewas.operand.v3", "oewas.operation.v3", "oewas.composition.v3"}
_LIST_MARKER = re.compile(r"(?:[-+*]|[0-9]{1,9}[.)])(?=[ \t\r\n]|$)")
_BLOCK_TAGS = (
    "address article aside base basefont blockquote body caption center col colgroup dd "
    "details dialog dir div dl dt fieldset figcaption figure footer form frame frameset "
    "h1 h2 h3 h4 h5 h6 head header hr html iframe legend li link main menu menuitem nav "
    "noframes ol optgroup option p param search section summary table tbody td tfoot th "
    "thead title tr track ul"
)
_HTML_BLOCK_TAG = re.compile(r"</?(?:" + "|".join(_BLOCK_TAGS.split()) + r")(?=[ \t>]|/?>|$)", re.I | re.A)
_HTML_RAW_START = re.compile(r"<(?:pre|script|style|textarea)(?=[ \t>]|$)", re.I | re.A)
_HTML_RAW_END = re.compile(r"</(?:pre|script|style|textarea)>", re.I | re.A)
_ATTR_NAME = r"[A-Za-z_:][A-Za-z0-9_.:-]*"
_ATTR_VALUE = r'''(?:[^ \t\r\n"'=<>`]+|'[^']*'|"[^"]*")'''
_HTML_COMPLETE_TAG = re.compile(
    r"(?:<(?!(?:pre|script|style|textarea)(?=[ \t/>]))[A-Za-z][A-Za-z0-9-]*(?:[ \t]+" + _ATTR_NAME +
    r"(?:[ \t]*=[ \t]*" + _ATTR_VALUE + r")?)*[ \t]*/?>|</[A-Za-z][A-Za-z0-9-]*[ \t]*>)[ \t]*$",
    re.I | re.A,
)


def _string_list(data: dict, field_name: str) -> list[str]:
    """Keep omitted legacy fields, but never repair explicitly malformed contracts."""
    value = data.get(field_name, [])
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a YAML list of strings")
    for index, item in enumerate(value):
        if type(item) is not str:
            raise ValueError(f"{field_name}[{index}] must be a string")
    return value


def _indent(line: str, column: int = 0) -> tuple[int, int]:
    index, end = 0, column
    while index < len(line) and line[index] in " \t":
        end = end + 1 if line[index] == " " else (end // 4 + 1) * 4
        index += 1
    return end - column, index


def _deindent(line: str, spaces: int, column: int = 0) -> str:
    """Remove up to the opener's indentation, including partial four-column tabs."""
    index, end = 0, column
    while index < len(line) and end < column + spaces and line[index] in " \t":
        end = end + 1 if line[index] == " " else (end // 4 + 1) * 4
        index += 1
    return " " * max(0, end - column - spaces) + line[index:]


def _quote_prefix(line: str, column: int):
    width, index = _indent(line, column)
    if width > 3 or line[index:index + 1] != ">":
        return None
    column += width + 1
    rest = line[index + 1:]
    if rest.startswith((" ", "\t")):
        rest = _deindent(rest, 1, column)
        column += 1
    return rest, column


def _thematic(line: str, column: int = 0) -> bool:
    width, index = _indent(line, column)
    return width <= 3 and any(re.fullmatch(r"(?:" + re.escape(c) + r"[ \t]*){3,}",
                                          line[index:].rstrip("\r\n")) for c in "-_*")


def _list_prefix(line: str, column: int, paragraph: bool):
    width, index = _indent(line, column)
    if width > 3 or _thematic(line, column):
        return None
    marker = _LIST_MARKER.match(line, index)
    if marker is None:
        return None
    rest = line[marker.end():]
    if paragraph and (not rest.strip(" \t\r\n") or
                      marker.group()[0].isdigit() and marker.group()[:-1] != "1"):
        return None
    marker_end = column + width + len(marker.group())
    padding, _ = _indent(rest, marker_end)
    padding = padding if 1 <= padding <= 4 and rest.strip(" \t\r\n") else 1
    return _deindent(rest, padding, marker_end), marker_end + padding, width + len(marker.group()) + padding


def _html_rule(line: str, paragraph: bool, column: int = 0):
    width, index = _indent(line, column)
    if width > 3:
        return False, None
    text = line[index:].rstrip("\r\n")
    if _HTML_RAW_START.match(text):
        return True, _HTML_RAW_END
    for start, end in (("<!--", "-->"), ("<?", "?>"), ("<![CDATA[", "]]>")):
        if text.startswith(start):
            return True, re.compile(re.escape(end))
    if re.match(r"<![A-Za-z]", text):
        return True, re.compile(">")
    if _HTML_BLOCK_TAG.match(text) or not paragraph and _HTML_COMPLETE_TAG.fullmatch(text):
        return True, None  # Types 6/7 end at a blank line, not a matching tag.
    return False, None


def _fence_opener(line: str, column: int = 0):
    width, index = _indent(line, column)
    if width > 3:
        return None
    match = _FENCE_OPENER.fullmatch(line[index:].rstrip("\r\n"))
    if match is None:
        return None
    _, marker, info = match.groups()
    return None if marker[0] == "`" and "`" in info else (width, marker, info.strip(" \t"))


def _interrupts_paragraph(line: str, column: int, *, exiting_item: bool = False) -> bool:
    width, index = _indent(line, column)
    tail = line[index:].rstrip("\r\n")
    return width <= 3 and bool(
        _fence_opener(line, column) or _quote_prefix(line, column) or
        _list_prefix(line, column, not exiting_item) or _thematic(line, column) or
        re.match(r"#{1,6}(?:[ \t]|$)", tail) or re.fullmatch(r"(?:=+|-+)[ \t]*", tail) or
        _html_rule(line, True, column)[0]
    )


@dataclass
class _OpenFence:
    start: int
    indentation: int
    marker: str
    info: str
    body: list[str] = field(default_factory=list)

    def finish(self, end: int, closed: bool):
        body = "".join(self.body)
        if closed:
            # Preserve the original leaf-content separator convention.
            body = re.sub(r"(?:\r\n|\r|\n)$", "", body)
        return self.start, end, self.info, body, closed


def _fenced_blocks(text: str, start: int = 0):
    """Track only block context needed for fences, preserving physical source offsets."""
    containers: list[tuple[str, int]] = []
    fence = None
    leaf = ""
    html_end = None
    for physical in _LINE_PATTERN.finditer(text, start):
        if not physical.group():
            continue
        line, column, matched = physical.group(), 0, 0
        for kind, width in containers:
            if kind == "quote":
                prefix = _quote_prefix(line, column)
                if prefix is None:
                    break
                line, column = prefix
            else:
                indentation, _ = _indent(line, column)
                if line.strip(" \t\r\n") and indentation < width:
                    break
                consumed = min(width, indentation)
                line = _deindent(line, consumed, column)
                column += consumed
            matched += 1
        if matched < len(containers):
            # Laziness belongs to paragraphs, never fenced or HTML block content.
            # A new item (including an ordered sibling numbered >1) is not a
            # lazy continuation of the previous item's paragraph.
            if leaf == "paragraph" and line.strip(" \t\r\n") and not _interrupts_paragraph(
                line, column, exiting_item=containers[matched][0] == "list",
            ):
                continue
            if fence is not None:
                yield fence.finish(physical.start(), False)
                fence = None
            containers = containers[:matched]
            leaf, html_end = "", None
        if fence is not None:
            width, index = _indent(line, column)
            tail = line[index:].rstrip("\r\n")
            if width <= 3 and re.fullmatch(re.escape(fence.marker[0]) +
                                          "{" + str(len(fence.marker)) + r",}[ \t]*", tail):
                # Closing line ending remains in following prose, as before.
                yield fence.finish(physical.start() +
                                   len(physical.group().rstrip("\r\n")), True)
                fence, leaf = None, ""
            else:
                fence.body.append(_deindent(line, fence.indentation, column))
            continue
        if leaf == "html":
            if html_end is None and not line.strip(" \t\r\n"):
                leaf = ""
            else:
                if html_end is not None and html_end.search(line):
                    leaf, html_end = "", None
                continue
        if leaf == "indented":
            if not line.strip(" \t\r\n") or _indent(line, column)[0] >= 4:
                continue
            leaf = ""
        while True:
            quote = _quote_prefix(line, column)
            if quote is not None:
                containers.append(("quote", 0))
                line, column = quote
                leaf = ""
                continue
            item = _list_prefix(line, column, leaf == "paragraph")
            if item is not None:
                line, column, width = item
                containers.append(("list", width))
                leaf = ""
                continue
            break
        opening = _fence_opener(line, column)
        if opening is not None:
            fence = _OpenFence(physical.start(), *opening)
            leaf = "fence"
            continue
        is_html, html_end = _html_rule(line, leaf == "paragraph", column)
        if is_html:
            leaf = "html" if html_end is None or not html_end.search(line) else ""
            continue
        width, index = _indent(line, column)
        tail = line[index:].rstrip("\r\n")
        if not tail or width <= 3 and (
            _thematic(line, column) or re.match(r"#{1,6}(?:[ \t]|$)", tail) or
            leaf == "paragraph" and re.fullmatch(r"(?:=+|-+)[ \t]*", tail) or
            re.match(r"\[[^\]]+\]:[ \t]*\S", tail)
        ):
            leaf = ""
        elif width >= 4 and leaf != "paragraph":
            leaf = "indented"
        else:
            leaf = "paragraph"
    if fence is not None:
        yield fence.finish(len(text), False)


class _UniqueDeclarationLoader(yaml.SafeLoader):
    """Reject repeated source keys without changing defined YAML merge precedence."""

    _merge_key = object()

    def __init__(self, stream):
        super().__init__(stream)
        self._checked_mappings: set[int] = set()

    def flatten_mapping(self, node):
        if id(node) not in self._checked_mappings:
            keys = set()
            for key_node, _ in node.value:
                if key_node.tag == "tag:yaml.org,2002:merge":
                    key = self._merge_key
                elif key_node.tag == "tag:yaml.org,2002:value":
                    # SafeLoader normally retags '=' as a string while flattening.
                    key = key_node.value
                else:
                    key = self.construct_object(key_node)
                if key in keys:
                    raise yaml.constructor.ConstructorError(
                        "while constructing a declaration mapping", node.start_mark,
                        f"duplicate source key {key_node.value!r}", key_node.start_mark,
                    )
                keys.add(key)
            self._checked_mappings.add(id(node))
        super().flatten_mapping(node)


class LosslessMarkdownParserAdapter(SkillDocumentParserPort):
    def parse_document(
        self,
        skill_id: SkillId,
        relative_path: str,
        content: bytes,
    ) -> Result[SkillDocumentV3, OeopDomainError]:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as e:
            return Err(DomainInvariantError(code="ENCODING_ERROR", message=f"UTF-8 decode failed: {e}"))

        raw_digest = ContentDigest.sha256(hashlib.sha256(content).hexdigest())

        # Byte line offset index for byte <-> line/col mapping
        byte_line_offsets: List[int] = [0]
        for ending in re.finditer(rb"\r\n|\r|\n", content):
            byte_line_offsets.append(ending.end())

        def get_span(start_b: int, end_b: int) -> SourceByteSpan:
            # Find line numbers
            start_line = 1
            for l_idx, offset in enumerate(byte_line_offsets):
                if offset <= start_b:
                    start_line = l_idx + 1
                else:
                    break
            start_col = start_b - byte_line_offsets[start_line - 1]

            end_line = 1
            for l_idx, offset in enumerate(byte_line_offsets):
                if offset <= end_b:
                    end_line = l_idx + 1
                else:
                    break
            end_col = end_b - byte_line_offsets[end_line - 1] if end_line <= len(byte_line_offsets) else 0
            return SourceByteSpan(
                start_byte=start_b,
                end_byte=end_b,
                start_line=start_line,
                start_col=start_col,
                end_line=end_line,
                end_col=end_col,
            )

        leaf_nodes: List[DocumentLeafNode] = []
        operands: List[InstructionOperand] = []
        operations: List[OperationV3] = []
        compositions: List[CompositionV3] = []
        semantic_blocks: List[tuple[str, str]] = []

        scan_start = 0
        try:
            _frontmatter(content, relative_path)
        except CatalogCompileRefusal:
            # This general Markdown port does not require catalog frontmatter.
            pass
        else:
            # Recognition belongs to the existing catalog. Its returned body is
            # newline-normalized, so locate the boundary in the original text.
            header_lines = _LINE_PATTERN.finditer(text)
            next(header_lines)  # Existing recognition guarantees an opening line.
            for physical in header_lines:
                if physical.group().rstrip("\r\n") == "---":
                    scan_start = physical.end()
                    break

        last_pos_char = 0
        for m_start_char, m_end_char, info, body, closed in _fenced_blocks(text, scan_start):
            m_start_byte = len(text[:m_start_char].encode("utf-8"))
            m_end_byte = len(text[:m_end_char].encode("utf-8"))
            last_pos_byte = len(text[:last_pos_char].encode("utf-8"))

            if m_start_char > last_pos_char:
                prose_text = text[last_pos_char:m_start_char]
                leaf_nodes.append(DocumentLeafNode(
                    kind="prose",
                    span=get_span(last_pos_byte, m_start_byte),
                    content=prose_text,
                ))

            fence_span = get_span(m_start_byte, m_end_byte)

            if not closed and info in _DECLARATION_INFOS:
                return Err(DomainInvariantError(
                    code="UNCLOSED_OEWAS_FENCE",
                    message=f"Declared {info} block requires a matching closing fence",
                    locus=f"{relative_path}:{fence_span.start_line}",
                ))

            leaf_nodes.append(DocumentLeafNode(
                kind="code_fence",
                span=fence_span,
                content=body,
                info_string=info,
            ))

            # Check for OEWAS V3 declarations
            try:
                if info == "oewas.operand.v3":
                    raw_data = yaml.load(body, Loader=_UniqueDeclarationLoader)
                    if not isinstance(raw_data, dict):
                        return Err(DomainInvariantError(
                            code="MALFORMED_OPERAND_BLOCK",
                            message=f"OEWAS operand block must be a YAML dictionary, got {type(raw_data).__name__}",
                            locus=f"{relative_path}:{fence_span.start_line}",
                        ))
                    data = raw_data
                    semantic_blocks.append((info, yaml.safe_dump(data, sort_keys=True, allow_unicode=True)))
                    op_id = data.get("operand_id", f"op_{len(operands)+1}")
                    kind = data.get("kind", "instruction")
                    inst_body = data.get("body", "")
                    deps_raw = _string_list(data, "dependencies")
                    deps = tuple(OperandId(d) for d in deps_raw)
                    obs = tuple(_string_list(data, "emitted_observations"))
                    operands.append(InstructionOperand(
                        operand_id=OperandId(op_id),
                        kind=str(kind),
                        instruction_body=str(inst_body),
                        span=fence_span,
                        dependencies=deps,
                        emitted_observations=obs,
                    ))

                elif info == "oewas.operation.v3":
                    raw_data = yaml.load(body, Loader=_UniqueDeclarationLoader)
                    if not isinstance(raw_data, dict):
                        return Err(DomainInvariantError(
                            code="MALFORMED_OPERATION_BLOCK",
                            message=f"OEWAS operation block must be a YAML dictionary, got {type(raw_data).__name__}",
                            locus=f"{relative_path}:{fence_span.start_line}",
                        ))
                    data = raw_data
                    semantic_blocks.append((info, yaml.safe_dump(data, sort_keys=True, allow_unicode=True)))
                    op_id = data.get("operation_id", f"{skill_id}:op")
                    inputs_data = data.get("inputs", [])
                    if not isinstance(inputs_data, list):
                        return Err(DomainInvariantError(
                            code="MALFORMED_OPERATION_INPUTS",
                            message=f"Operation inputs must be a YAML list, got {type(inputs_data).__name__}",
                            locus=f"{relative_path}:{fence_span.start_line}",
                        ))
                    for index, port_data in enumerate(inputs_data):
                        if not isinstance(port_data, dict):
                            return Err(DomainInvariantError(
                                code="MALFORMED_OPERATION_INPUTS",
                                message=f"Operation inputs[{index}] must be a YAML dictionary, got {type(port_data).__name__}",
                                locus=f"{relative_path}:{fence_span.start_line}:inputs[{index}]",
                            ))
                    output_data = data.get("output", {})
                    if not isinstance(output_data, dict):
                        return Err(DomainInvariantError(
                            code="MALFORMED_OPERATION_OUTPUT",
                            message="Operation output must be a YAML dictionary",
                            locus=f"{relative_path}:{fence_span.start_line}:output",
                        ))

                    inputs = tuple(
                        PortSpecV3(
                            name=str(p.get("name", "in")),
                            colour_id=ColourId(str(p.get("colour_id", "Data"))),
                            schema_ref=SchemaRef(str(p.get("schema_ref", "schema:any:v1"))),
                            schema_digest=ContentDigest.sha256(str(p.get("schema_digest", "0"*64))),
                            validator_ref=str(p.get("validator_ref", "")),
                            validator_digest=ContentDigest.sha256(str(p.get("validator_digest", "0"*64))),
                        )
                        for p in inputs_data
                    )
                    output = PortSpecV3(
                        name=str(output_data.get("name", "out")),
                        colour_id=ColourId(str(output_data.get("colour_id", "Data"))),
                        schema_ref=SchemaRef(str(output_data.get("schema_ref", "schema:any:v1"))),
                        schema_digest=ContentDigest.sha256(str(output_data.get("schema_digest", "0"*64))),
                        validator_ref=str(output_data.get("validator_ref", "")),
                        validator_digest=ContentDigest.sha256(str(output_data.get("validator_digest", "0"*64))),
                    )
                    op_refs = tuple(OperandId(r) for r in _string_list(data, "operand_refs"))

                    lifecycle = SkillLifecycleV3(
                        declaration=DeclarationFacet(data.get("declaration", "Declared")),
                        schema_binding=SchemaBindingFacet(data.get("schema_binding", "Unbound")),
                        executor_binding=ExecutorBindingFacet(data.get("executor_binding", "Unbound")),
                        validation=ValidationFacet(data.get("validation", "Unchecked")),
                        # A source document cannot grant its own admission. That is
                        # a separate, evidence-backed decision outside this parser.
                        admission=(AdmissionFacet.RETIRED if data.get("admission") == "Retired"
                                   else AdmissionFacet.UNADMITTED),
                        schema_digest=(ContentDigest.sha256(str(data["schema_digest"]))
                                       if "schema_digest" in data else None),
                        executor_digest=(ContentDigest.sha256(str(data["executor_digest"]))
                                         if "executor_digest" in data else None),
                    )
                    effects_raw = _string_list(data, "effects")
                    tools_raw = _string_list(data, "tool_refs")

                    operations.append(OperationV3(
                        operation_id=OperationId(str(op_id)),
                        inputs=inputs,
                        output=output,
                        operand_refs=op_refs,
                        lifecycle=lifecycle,
                        residual_status=str(data.get("residual_status", "unknown")),
                        effects=tuple(effects_raw),
                        tool_refs=tuple(tools_raw),
                        authority_effect=AuthorityEffect(data.get("authority_effect", "None")),
                        authority_ceiling=AuthorityEffect(data.get("authority_ceiling", "None")),
                        invocation_grade=str(data.get("invocation_grade", "entry")),
                        description=str(data.get("description", "")),
                        replacement_operation_id=(OperationId(data["replacement_operation_id"])
                                                  if "replacement_operation_id" in data else None),
                    ))

                elif info == "oewas.composition.v3":
                    raw_data = yaml.load(body, Loader=_UniqueDeclarationLoader)
                    if not isinstance(raw_data, dict):
                        return Err(DomainInvariantError(
                            code="MALFORMED_COMPOSITION_BLOCK",
                            message=f"OEWAS composition block must be a YAML dictionary, got {type(raw_data).__name__}",
                            locus=f"{relative_path}:{fence_span.start_line}",
                        ))
                    data = raw_data
                    semantic_blocks.append((info, yaml.safe_dump(data, sort_keys=True, allow_unicode=True)))
                    comp_id = str(data.get("composition_id", f"comp_{len(compositions)+1}"))
                    t_kind = str(data.get("term_kind", "primitive"))
                    root_op = OperationId(str(data.get("root_operation_id", f"{skill_id}:root")))
                    child_ops = tuple(OperationId(c) for c in _string_list(data, "child_operation_ids"))
                    slots_raw = data.get("slot_bindings", [])
                    if not isinstance(slots_raw, list):
                        return Err(DomainInvariantError(
                            code="MALFORMED_SLOT_BINDINGS",
                            message="slot_bindings must be a list",
                            locus=f"{relative_path}:{fence_span.start_line}",
                        ))
                    if any(
                        not isinstance(s, (list, tuple)) or len(s) != 2
                        or type(s[0]) is not int
                        for s in slots_raw
                    ):
                        return Err(DomainInvariantError(
                            code="MALFORMED_SLOT_BINDINGS",
                            message="each slot binding must be [integer slot, operation id]",
                            locus=f"{relative_path}:{fence_span.start_line}",
                        ))
                    slot_bindings = tuple(
                        (s[0], OperationId(str(s[1])))
                        for s in slots_raw
                    )
                    compositions.append(CompositionV3(
                        composition_id=comp_id,
                        term_kind=t_kind,
                        root_operation_id=root_op,
                        child_operation_ids=child_ops,
                        slot_bindings=slot_bindings,
                        expected_boundary=str(data.get("expected_boundary", "")),
                    ))
            except (yaml.YAMLError, ValueError, TypeError) as parse_exc:
                return Err(DomainInvariantError(
                    code="MALFORMED_OEWAS_DECLARATION",
                    message=f"Failed to parse {info} block: {parse_exc}",
                    locus=f"{relative_path}:{fence_span.start_line}",
                ))

            last_pos_char = m_end_char

        if last_pos_char < len(text):
            last_pos_byte = len(text[:last_pos_char].encode("utf-8"))
            prose_text = text[last_pos_char:]
            leaf_nodes.append(DocumentLeafNode(
                kind="prose",
                span=get_span(last_pos_byte, len(content)),
                content=prose_text,
            ))

        # Cover every typed declaration field, not only IDs and instruction bodies.
        # Prose and YAML presentation whitespace remain outside the semantic digest.
        sem_hasher = hashlib.sha256()
        for kind, normalized_data in semantic_blocks:
            sem_hasher.update(kind.encode("utf-8"))
            sem_hasher.update(b"\x00")
            sem_hasher.update(normalized_data.encode("utf-8"))
            sem_hasher.update(b"\x00")
        semantic_digest = ContentDigest.sha256(sem_hasher.hexdigest())

        doc_id = DocumentId(f"doc_{str(skill_id)}")
        proven_root = operations[0].operation_id if operations else None

        return Ok(SkillDocumentV3(
            document_id=doc_id,
            skill_id=skill_id,
            source_relative_path=relative_path,
            raw_digest=raw_digest,
            semantic_digest=semantic_digest,
            leaf_nodes=tuple(leaf_nodes),
            operands=tuple(operands),
            operations=tuple(operations),
            compositions=tuple(compositions),
            proven_root_operation_id=proven_root,
        ))
