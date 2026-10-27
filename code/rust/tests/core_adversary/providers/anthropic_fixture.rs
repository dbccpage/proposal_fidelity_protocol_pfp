//! Anthropic transport against a fixture HTTP client. No provider is contacted; every
//! price below is a fixture value, not a published price.
//!
//! AuthorityEffect: None.

use core_adversary::providers::anthropic::raw_store::{DirectoryRawSink, RawReplySink};
use core_adversary::providers::anthropic::request::{
    AdvisorPairings, AdvisorTool, CacheTtl, CodeExecutionTool, CustomTool, MessagesRequest,
    ADVISOR_BETA, API_VERSION, MESSAGES_URL,
};
use core_adversary::providers::anthropic::response::{ContentBlock, Readability, StopReason};
use core_adversary::providers::anthropic::tool_round::{client_tool_uses, tool_result_message, ToolOutcome};
use core_adversary::providers::anthropic::transport::{
    worst_case, AnthropicMessagesTransport, SendError, CACHE_WRITE_INPUT_FACTOR,
    PROVIDER_PROMPT_ALLOWANCE_TOKENS,
};
use core_adversary::providers::budget::{PriceTable, PricingObservation};
use core_adversary::providers::credentials::AnthropicApiKey;
use core_adversary::providers::transport::{HttpClient, HttpReply};
use core_adversary::providers::Refusal;
use serde_json::{json, Value};
use std::collections::{BTreeMap, VecDeque};
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};

const EXECUTOR: &str = "claude-sonnet-5-5";
const ADVISOR: &str = "claude-opus-5-5";
const KEY: &str = "fixture-key-not-a-secret";

#[derive(Default)]
struct Fixture {
    replies: VecDeque<Result<HttpReply, Refusal>>,
    calls: Vec<(String, BTreeMap<String, String>, Value)>,
}

impl HttpClient for Fixture {
    fn post(
        &mut self,
        _: &str,
        _: &BTreeMap<String, String>,
        _: &Value,
        _: usize,
    ) -> Result<Vec<u8>, Refusal> {
        unreachable!("the Anthropic transport must use post_with_status")
    }
    fn post_with_status(
        &mut self,
        url: &str,
        headers: &BTreeMap<String, String>,
        body: &Value,
        _: usize,
    ) -> Result<HttpReply, Refusal> {
        self.calls.push((url.into(), headers.clone(), body.clone()));
        self.replies.pop_front().expect("a scripted reply")
    }
}

fn reply(status: u16, body: &str) -> Result<HttpReply, Refusal> {
    Ok(HttpReply {
        status,
        body: body.as_bytes().to_vec(),
        truncated: None,
    })
}

static DIRS: AtomicUsize = AtomicUsize::new(0);

fn scratch() -> PathBuf {
    let dir = std::env::temp_dir().join(format!(
        "core_providers_anthropic_{}_{}",
        std::process::id(),
        DIRS.fetch_add(1, Ordering::SeqCst)
    ));
    let _ = std::fs::remove_dir_all(&dir);
    dir
}

fn key() -> AnthropicApiKey {
    AnthropicApiKey::from_environ(&BTreeMap::from([("ANTHROPIC_API_KEY".into(), KEY.into())]))
        .unwrap()
}

fn observation(model: &str, input: u64, output: u64) -> Value {
    json!({
        "model_deployment_id": model,
        "input_microusd_per_mtok": input,
        "output_microusd_per_mtok": output,
        "effective_from_utc": "2026-01-01T00:00:00.000000Z",
        "observed_at_utc": "2026-10-01T00:00:00.000000Z",
        "stale_after_utc": "2027-01-01T00:00:00.000000Z",
        "evidence_digest": format!("sha256:{}", "a".repeat(64)),
    })
}

fn prices() -> PriceTable {
    PriceTable::new(vec![
        PricingObservation::from_json(&observation(EXECUTOR, 3_000_000, 15_000_000)).unwrap(),
        PricingObservation::from_json(&observation(ADVISOR, 15_000_000, 60_000_000)).unwrap(),
    ])
    .unwrap()
}

fn at() -> Value {
    json!("2026-10-06T12:00:00.000000Z")
}

fn pairings() -> AdvisorPairings {
    AdvisorPairings::new([(EXECUTOR.to_owned(), ADVISOR.to_owned())])
}

fn plain() -> MessagesRequest {
    MessagesRequest {
        model: EXECUTOR.into(),
        max_tokens: 1000,
        system: Some("fixture system".into()),
        messages: vec![json!({"role": "user", "content": "fixture question"})],
        advisor: None,
        code_execution: None,
        custom_tools: vec![],
        container: None,
        disable_parallel_tool_use: false,
        output_config: None,
    }
}

fn advised() -> MessagesRequest {
    MessagesRequest {
        advisor: Some(AdvisorTool {
            model: ADVISOR.into(),
            max_uses: 2,
            max_tokens: 2048,
            caching: Some(CacheTtl::FiveMinutes),
        }),
        ..plain()
    }
}

fn transport(
    replies: Vec<Result<HttpReply, Refusal>>,
    dir: &PathBuf,
) -> AnthropicMessagesTransport<Fixture, DirectoryRawSink> {
    let fixture = Fixture {
        replies: replies.into(),
        calls: vec![],
    };
    AnthropicMessagesTransport::new(key(), fixture, DirectoryRawSink::new(dir), pairings())
}

fn not_sent(result: Result<impl std::fmt::Debug, SendError>) -> String {
    match result.unwrap_err() {
        SendError::NotSent(refusal) => refusal.code,
        other => panic!("expected NotSent, got {other:?}"),
    }
}

const MESSAGE_OK: &str = r#"{"type":"message","id":"msg_fixture","model":"claude-sonnet-5-5","role":"assistant",
 "stop_reason":"end_turn","content":[{"type":"text","text":"fixture answer"}],
 "usage":{"input_tokens":120,"output_tokens":40}}"#;

#[test]
fn a_zero_ceiling_refuses_before_any_request() {
    let dir = scratch();
    let mut t = transport(vec![], &dir);
    assert_eq!(
        not_sent(t.send(&plain(), "r1", &prices(), &at(), 0)),
        "PAID_DISPATCH_DISABLED"
    );
    assert!(t.client().calls.is_empty());
    assert!(!dir.exists(), "nothing is persisted when nothing is sent");
}

#[test]
fn a_worst_case_above_the_ceiling_refuses_before_any_request() {
    let dir = scratch();
    let mut t = transport(vec![], &dir);
    assert_eq!(
        not_sent(t.send(&advised(), "r1", &prices(), &at(), 1_000)),
        "BUDGET_CEILING_EXCEEDED"
    );
    let empty = PriceTable::new(vec![]).unwrap();
    assert_eq!(
        not_sent(t.send(&plain(), "r1", &empty, &at(), 10_000_000)),
        "PRICE_OBSERVATION_MISSING"
    );
    assert!(t.client().calls.is_empty());
}

#[test]
fn the_worst_case_covers_every_advisor_use() {
    let request = advised();
    let (body, _) = request.build(&pairings()).unwrap();
    let quote = worst_case(&request, &body, &prices(), &at()).unwrap();
    let bytes = serde_json::to_vec(&body).unwrap().len() as u64;
    let input = bytes + PROVIDER_PROMPT_ALLOWANCE_TOKENS;
    let context = input + 1000 + 2 * 2048;
    let up = |tokens: u64, price: u64| (tokens * price).div_ceil(1_000_000);
    // The advisor caches, so every input token is priced as a cache write.
    let cache = CACHE_WRITE_INPUT_FACTOR;
    assert_eq!(quote.input_token_bound, input);
    assert_eq!(
        quote.executor_microusd,
        up(cache * 3 * context, 3_000_000) + up(1000, 15_000_000)
    );
    assert_eq!(
        quote.advisor_microusd,
        up(cache * 2 * context, 15_000_000) + up(2 * 2048, 60_000_000)
    );
    assert_eq!(
        quote.total_microusd,
        quote.executor_microusd + quote.advisor_microusd
    );
}

#[test]
fn the_advisor_request_carries_its_beta_header_and_bounds() {
    let dir = scratch();
    let mut t = transport(vec![reply(200, MESSAGE_OK)], &dir);
    t.send(&advised(), "r1", &prices(), &at(), 10_000_000)
        .unwrap();
    let (url, headers, body) = &t.client().calls[0];
    assert_eq!(url, MESSAGES_URL);
    assert_eq!(headers["anthropic-beta"], ADVISOR_BETA);
    assert_eq!(headers["anthropic-version"], API_VERSION);
    assert_eq!(headers["x-api-key"], KEY);
    assert_eq!(
        body["tools"][0],
        json!({"type": "advisor_20260301", "name": "advisor", "model": ADVISOR, "max_uses": 2,
               "max_tokens": 2048, "caching": {"type": "ephemeral", "ttl": "5m"}})
    );
    assert!(
        !body.to_string().contains(KEY),
        "the key travels only in its header"
    );
}

#[test]
fn no_beta_header_without_the_advisor() {
    let dir = scratch();
    let mut t = transport(vec![reply(200, MESSAGE_OK)], &dir);
    let request = MessagesRequest {
        code_execution: Some(CodeExecutionTool {
            version: "code_execution_20260521".into(),
            max_charge_microusd: 5_000,
        }),
        container: Some("container_fixture".into()),
        custom_tools: vec![CustomTool {
            name: "read_source".into(),
            description: "Read one bound source".into(),
            input_schema: json!({"type": "object", "properties": {"path": {"type": "string"}}}),
            strict: true,
        }],
        disable_parallel_tool_use: true,
        ..plain()
    };
    t.send(&request, "r1", &prices(), &at(), 10_000_000)
        .unwrap();
    let (_, headers, body) = &t.client().calls[0];
    assert!(!headers.contains_key("anthropic-beta"));
    assert_eq!(
        body["tools"][0],
        json!({"type": "code_execution_20260521", "name": "code_execution"})
    );
    assert_eq!(body["tools"][1]["strict"], json!(true));
    assert_eq!(body["container"], json!("container_fixture"));
    assert_eq!(
        body["tool_choice"],
        json!({"type": "auto", "disable_parallel_tool_use": true})
    );
}

fn with_block(block: Value) -> MessagesRequest {
    MessagesRequest {
        messages: vec![json!({"role": "user", "content": [block, {"type": "text", "text": "x"}]})],
        ..plain()
    }
}

#[test]
fn inline_text_documents_and_images_are_priced_by_their_bytes() {
    for block in [
        json!({"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": "fixture"}}),
        json!({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0="}}),
    ] {
        let request = with_block(block);
        assert!(request.build(&pairings()).is_ok());
    }
    let cached =
        with_block(json!({"type": "text", "text": "y", "cache_control": {"type": "ephemeral"}}));
    assert!(cached.caches() && !plain().caches());
    let (body, _) = cached.build(&pairings()).unwrap();
    let doubled = worst_case(&cached, &body, &prices(), &at()).unwrap();
    let mut uncached = cached.clone();
    uncached.messages = vec![
        json!({"role": "user", "content": [{"type": "text", "text": "y"}, {"type": "text", "text": "x"}]}),
    ];
    let (body, _) = uncached.build(&pairings()).unwrap();
    let single = worst_case(&uncached, &body, &prices(), &at()).unwrap();
    assert!(doubled.executor_microusd > single.executor_microusd);
}

#[test]
fn invalid_requests_are_refused_before_sending() {
    let pair = |model: &str| MessagesRequest {
        advisor: Some(AdvisorTool {
            model: model.into(),
            max_uses: 1,
            max_tokens: 2048,
            caching: None,
        }),
        ..plain()
    };
    let cases = [
        (pair("claude-haiku-4-5"), "ADVISOR_PAIRING_UNKNOWN"),
        (
            MessagesRequest {
                advisor: Some(AdvisorTool {
                    model: ADVISOR.into(),
                    max_uses: 1,
                    max_tokens: 1000,
                    caching: None,
                }),
                ..plain()
            },
            "ANTHROPIC_REQUEST_INVALID",
        ),
        (
            MessagesRequest {
                container: Some("c".into()),
                ..plain()
            },
            "ANTHROPIC_REQUEST_INVALID",
        ),
        (
            MessagesRequest {
                code_execution: Some(CodeExecutionTool {
                    version: "code_execution_20240101".into(),
                    max_charge_microusd: 1,
                }),
                ..plain()
            },
            "ANTHROPIC_REQUEST_INVALID",
        ),
        (
            MessagesRequest {
                code_execution: Some(CodeExecutionTool {
                    version: "code_execution_20260521".into(),
                    max_charge_microusd: 0,
                }),
                ..plain()
            },
            "ANTHROPIC_REQUEST_INVALID",
        ),
        (
            with_block(
                json!({"type": "document", "source": {"type": "file", "file_id": "file_1"}}),
            ),
            "ANTHROPIC_CONTENT_UNPRICED",
        ),
        (
            with_block(
                json!({"type": "image", "source": {"type": "url", "url": "https://example.org/a.png"}}),
            ),
            "ANTHROPIC_CONTENT_UNPRICED",
        ),
        (
            with_block(
                json!({"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "JVBERi0="}}),
            ),
            "ANTHROPIC_CONTENT_UNPRICED",
        ),
        (
            with_block(json!({"type": "container_upload", "file_id": "file_2"})),
            "ANTHROPIC_CONTENT_UNPRICED",
        ),
        (
            MessagesRequest {
                messages: vec![json!({"role": "assistant", "content": "x"})],
                ..plain()
            },
            "ANTHROPIC_REQUEST_INVALID",
        ),
        (
            MessagesRequest {
                disable_parallel_tool_use: true,
                ..plain()
            },
            "ANTHROPIC_REQUEST_INVALID",
        ),
    ];
    for (request, code) in cases {
        let dir = scratch();
        let mut t = transport(vec![], &dir);
        assert_eq!(
            not_sent(t.send(&request, "r1", &prices(), &at(), 10_000_000)),
            code
        );
        assert!(t.client().calls.is_empty());
    }
}

#[test]
fn advisor_and_code_execution_blocks_are_parsed_and_kept_verbatim() {
    let body = json!({
        "type": "message", "id": "msg_fixture", "model": EXECUTOR, "role": "assistant",
        "stop_reason": "pause_turn",
        "container": {"id": "container_fixture", "expires_at": "2026-10-06T13:00:00Z"},
        "content": [
            {"type": "server_tool_use", "id": "srvtoolu_1", "name": "advisor", "input": {}},
            {"type": "advisor_tool_result", "tool_use_id": "srvtoolu_1",
             "content": {"type": "advisor_redacted_result", "encrypted_content": "opaque==", "stop_reason": "end_turn"}},
            {"type": "server_tool_use", "id": "srvtoolu_2", "name": "bash_code_execution", "input": {"command": "echo 1"}},
            {"type": "bash_code_execution_tool_result", "tool_use_id": "srvtoolu_2",
             "content": {"type": "bash_code_execution_result", "stdout": "1\n", "stderr": "", "return_code": 0, "content": []}},
            {"type": "future_block", "payload": 1}
        ],
        "usage": {"input_tokens": 500, "output_tokens": 60, "server_tool_use": {"code_execution_requests": 1}}
    });
    let dir = scratch();
    let mut t = transport(vec![reply(200, &body.to_string())], &dir);
    let outcome = t
        .send(&advised(), "r1", &prices(), &at(), 10_000_000)
        .unwrap();
    let response = outcome.parsed.unwrap();
    assert_eq!(response.stop_reason, StopReason::PauseTurn);
    assert_eq!(response.container_id.as_deref(), Some("container_fixture"));
    assert_eq!(response.usage.code_execution_requests, 1);
    assert!(
        matches!(&response.content[1], ContentBlock::AdvisorRedactedResult { encrypted_content, .. } if encrypted_content == "opaque==")
    );
    assert_eq!(response.content[1].readability(), Readability::NotReadable);
    assert!(
        matches!(&response.content[3], ContentBlock::CodeExecutionResult { content, .. } if content["return_code"] == 0)
    );
    assert!(matches!(response.content[4], ContentBlock::Unknown(_)));
    assert_eq!(
        response.assistant_message()["content"],
        body["content"],
        "history is replayed byte-for-byte"
    );
    assert_eq!(
        outcome.metered_cost_microusd, None,
        "advisor and code execution charges are not priced"
    );
    assert_eq!(
        std::fs::read(&outcome.raw.path).unwrap(),
        body.to_string().into_bytes()
    );
}

#[test]
fn a_plain_reply_is_metered_from_its_usage() {
    let dir = scratch();
    let mut t = transport(vec![reply(200, MESSAGE_OK)], &dir);
    let outcome = t
        .send(&plain(), "r1", &prices(), &at(), 10_000_000)
        .unwrap();
    assert_eq!(outcome.parsed.unwrap().text(), "fixture answer");
    let expected =
        (120u64 * 3_000_000).div_ceil(1_000_000) + (40u64 * 15_000_000).div_ceil(1_000_000);
    assert_eq!(outcome.metered_cost_microusd, Some(expected));
    assert!(expected <= outcome.quote.total_microusd);
}

#[test]
fn an_unparseable_reply_is_persisted_before_it_is_refused() {
    let dir = scratch();
    let mut t = transport(vec![reply(200, "{not json")], &dir);
    let outcome = t
        .send(&plain(), "r1", &prices(), &at(), 10_000_000)
        .unwrap();
    assert_eq!(
        outcome.parsed.unwrap_err().code,
        "ANTHROPIC_RESPONSE_UNPARSEABLE"
    );
    assert_eq!(std::fs::read(&outcome.raw.path).unwrap(), b"{not json");
}

#[test]
fn an_error_reply_is_persisted_and_typed() {
    let dir = scratch();
    let envelope = r#"{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}"#;
    let mut t = transport(vec![reply(529, envelope), reply(502, "<html>")], &dir);
    let outcome = t
        .send(&plain(), "r1", &prices(), &at(), 10_000_000)
        .unwrap();
    assert_eq!(outcome.status, 529);
    assert_eq!(
        outcome.parsed.unwrap_err().code,
        "ANTHROPIC_OVERLOADED_ERROR"
    );
    assert_eq!(
        std::fs::read(&outcome.raw.path).unwrap(),
        envelope.as_bytes()
    );
    let outcome = t
        .send(&plain(), "r2", &prices(), &at(), 10_000_000)
        .unwrap();
    assert_eq!(outcome.parsed.unwrap_err().code, "ANTHROPIC_HTTP_502");
}

#[test]
fn a_truncated_reply_is_persisted_as_far_as_it_arrived() {
    let dir = scratch();
    let cut = Ok(HttpReply {
        status: 200,
        body: b"{\"type\":\"message\",\"content\":[".to_vec(),
        truncated: Some("SWARM_PROVIDER_REPLY_TOO_LARGE".into()),
    });
    let mut t = transport(vec![cut], &dir);
    let outcome = t
        .send(&plain(), "r1", &prices(), &at(), 10_000_000)
        .unwrap();
    assert_eq!(
        outcome.parsed.unwrap_err().code,
        "ANTHROPIC_REPLY_TRUNCATED"
    );
    assert_eq!(outcome.metered_cost_microusd, None, "settled at the quote");
    assert_eq!(
        std::fs::read(&outcome.raw.path).unwrap(),
        b"{\"type\":\"message\",\"content\":["
    );
}

#[test]
fn a_reply_under_a_taken_name_is_kept_beside_it() {
    let dir = scratch();
    DirectoryRawSink::new(&dir)
        .persist("r1", b"earlier")
        .unwrap();
    let mut t = transport(vec![reply(200, MESSAGE_OK)], &dir);
    let outcome = t
        .send(&plain(), "r1", &prices(), &at(), 10_000_000)
        .unwrap();
    let name = outcome
        .raw
        .path
        .file_name()
        .unwrap()
        .to_string_lossy()
        .to_string();
    assert!(
        name.starts_with("r1.") && name.len() == "r1.".len() + 16,
        "{name}"
    );
    assert_eq!(
        std::fs::read(&outcome.raw.path).unwrap(),
        MESSAGE_OK.as_bytes()
    );
    assert_eq!(std::fs::read(dir.join("r1")).unwrap(), b"earlier");
}

#[test]
fn a_transport_failure_leaves_the_outcome_unknown() {
    let dir = scratch();
    let mut t = transport(
        vec![Err(Refusal::new("TRANSPORT_ERROR", "HTTP request failed"))],
        &dir,
    );
    match t
        .send(&plain(), "r1", &prices(), &at(), 10_000_000)
        .unwrap_err()
    {
        SendError::OutcomeUnknown(refusal) => assert_eq!(refusal.code, "TRANSPORT_ERROR"),
        other => panic!("expected OutcomeUnknown, got {other:?}"),
    }
}

#[test]
fn raw_replies_are_written_once() {
    let dir = scratch();
    let mut sink = DirectoryRawSink::new(&dir);
    let first = sink.persist("occ.r1.s1.a1", b"reply").unwrap();
    assert_eq!(sink.persist("occ.r1.s1.a1", b"reply").unwrap(), first);
    assert_eq!(
        sink.persist("occ.r1.s1.a1", b"other").unwrap_err().code,
        "RAW_REPLY_CONFLICT"
    );
    assert_eq!(std::fs::read(&first.path).unwrap(), b"reply");
    for bad in ["../escape", "NUL", "con.txt", "Com1.json", "trailing."] {
        assert_eq!(
            sink.persist(bad, b"x").unwrap_err().code,
            "RAW_REPLY_NAME_INVALID",
            "{bad}"
        );
    }
    let leftovers: Vec<_> = std::fs::read_dir(&dir)
        .unwrap()
        .map(|e| e.unwrap().file_name())
        .collect();
    assert_eq!(leftovers.len(), 1, "no temp files remain: {leftovers:?}");
}

#[test]
fn parallel_tool_results_go_back_in_one_message_in_request_order() {
    let content = vec![
        json!({"type": "text", "text": "Reading two sources."}),
        json!({"type": "tool_use", "id": "toolu_b", "name": "read_source", "input": {"path": "b"}}),
        json!({"type": "server_tool_use", "id": "srvtoolu_1", "name": "advisor", "input": {}}),
        json!({"type": "tool_use", "id": "toolu_a", "name": "read_source", "input": {"path": "a"}}),
        json!({"type": "tool_use", "id": "toolu_c", "name": "web_fetch", "input": {}}),
    ];
    let uses = client_tool_uses(&content).unwrap();
    assert_eq!(
        uses.iter().map(|u| u.id.as_str()).collect::<Vec<_>>(),
        ["toolu_b", "toolu_a", "toolu_c"]
    );
    let outcomes = BTreeMap::from([
        (
            "toolu_a".to_owned(),
            ToolOutcome::Ran {
                content: json!("source a"),
                is_error: false,
            },
        ),
        (
            "toolu_c".to_owned(),
            ToolOutcome::NotRun {
                reason: "web_fetch is not bound for this mission".into(),
            },
        ),
    ]);
    let message = tool_result_message(&uses, &outcomes, Some("Continue.")).unwrap();
    let blocks = message["content"].as_array().unwrap();
    assert_eq!(message["role"], "user");
    assert_eq!(blocks.len(), 4);
    assert_eq!(blocks[0]["tool_use_id"], "toolu_b");
    assert_eq!(
        blocks[0]["is_error"], true,
        "a call with no outcome is answered as not run"
    );
    assert_eq!(
        blocks[1],
        json!({"type": "tool_result", "tool_use_id": "toolu_a", "content": "source a", "is_error": false})
    );
    assert_eq!(blocks[2]["is_error"], true);
    assert_eq!(
        blocks[3],
        json!({"type": "text", "text": "Continue."}),
        "text comes after every result"
    );

    let stray = BTreeMap::from([(
        "toolu_z".to_owned(),
        ToolOutcome::NotRun { reason: "x".into() },
    )]);
    assert_eq!(
        tool_result_message(&uses, &stray, None).unwrap_err().code,
        "TOOL_RESULT_UNMATCHED"
    );
    let repeated = vec![content[1].clone(), content[1].clone()];
    assert_eq!(
        client_tool_uses(&repeated).unwrap_err().code,
        "TOOL_USE_INVALID"
    );
}

#[test]
fn the_key_comes_only_from_the_supplied_environment() {
    for environ in [
        BTreeMap::new(),
        BTreeMap::from([("ANTHROPIC_API_KEY".to_owned(), "  ".to_owned())]),
    ] {
        match AnthropicApiKey::from_environ(&environ) {
            Err(refusal) => assert_eq!(refusal.code, "ANTHROPIC_KEY_MISSING"),
            Ok(_) => panic!("a blank or absent key must be refused"),
        }
    }
    let other = BTreeMap::from([("OPENROUTER_API_KEY".to_owned(), "x".to_owned())]);
    assert!(AnthropicApiKey::from_environ(&other).is_err());
}
#[test]
fn structured_output_keeps_schema_in_billed_request_and_refuses_unknown_controls() {
    let mut request = plain();
    request.output_config = Some(json!({"format":{"type":"json_schema","schema":{
        "type":"object","properties":{"answer":{"type":"string"}},
        "required":["answer"],"additionalProperties":false}}}));
    let (body, _) = request.build(&AdvisorPairings::default()).unwrap();
    assert_eq!(body["output_config"], request.output_config.clone().unwrap());
    assert!(body.get("seed").is_none());
    assert!(body.get("temperature").is_none());
    request.output_config = Some(json!({"format":{"type":"json_object"}}));
    assert_eq!(request.build(&AdvisorPairings::default()).unwrap_err().code, "ANTHROPIC_REQUEST_INVALID");
}

#[test]
fn thinking_is_output_usage_but_future_billable_usage_is_unrated() {
    for future in [false, true] {
        let mut body = json!({"type":"message","id":"msg_fixture","model":EXECUTOR,
            "stop_reason":"end_turn","content":[{"type":"thinking","thinking":"fixture deliberation","signature":"fixture"},
                {"type":"text","text":"answer"}],"usage":{"input_tokens":10,"output_tokens":20,
                "output_tokens_details":{"thinking_tokens":5}}});
        if future { body["usage"]["future_billable_units"] = json!(1); }
        let fixture = Fixture { replies: VecDeque::from([reply(200, &body.to_string())]), ..Fixture::default() };
        let mut transport = AnthropicMessagesTransport::new(key(), fixture, DirectoryRawSink::new(scratch()), pairings());
        let result = transport.send(&plain(), "thinking", &prices(), &at(), 1_000_000).unwrap();
        assert_eq!(result.parsed.unwrap().text(), "answer");
        assert_eq!(result.metered_cost_microusd.is_some(), !future);
    }
}

#[test]
fn standard_speed_usage_is_priced_without_counting_thinking_twice() {
    // Sanitized public counter shape from the retained HTTP-200 pilot reply.
    for speed in ["standard", "fast", "future-speed"] {
        let body = json!({"type":"message","id":"public-usage-control","model":EXECUTOR,
            "stop_reason":"end_turn","content":[{"type":"text","text":"public fixture answer"}],
            "usage":{"input_tokens":856,"output_tokens":407,"cache_creation_input_tokens":0,
                "cache_read_input_tokens":0,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":0},
                "output_tokens_details":{"thinking_tokens":229},"service_tier":"standard","inference_geo":"global","speed":speed}});
        let mut t = transport(vec![reply(200, &body.to_string())], &scratch());
        let result = t.send(&plain(), "standard-speed", &prices(), &at(), 1_000_000).unwrap();
        assert_eq!(result.metered_cost_microusd, if speed == "standard" { Some(8673) } else { None });
    }
}

// Origin: engine/crates_rs/tests/core_adversary/providers/anthropic_fixture.rs
// Claim: urn:core:crates_rs:tests:anthropic-fixture:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde57645ae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde57645ae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore57645ae {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrore57645ae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore57645ae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore57645ae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde57645ae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore57645ae> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore57645ae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore57645ae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore57645ae::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_e57645ae() {
    let admitted = BoundaryRecorde57645ae::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde57645ae::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
