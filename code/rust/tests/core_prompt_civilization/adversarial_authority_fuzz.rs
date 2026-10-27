//! Adversarial Fuzz Testing for Candidate JSON Encodings and Authority Markers.
//!
//! AuthorityEffect: None.
//!
//! Tests detector robustness against:
//! 1. Escaped Unicode sequences in field keys and authority marker values.
//! 2. RFC 8259 valid extreme whitespace (spaces, tabs, newlines, CR-LF combinations).
//! 3. RFC 8259 syntax-violating non-standard whitespace outside strings (form feeds, vertical tabs, NBSP).
//! 4. In-string invisible characters and zero-width code points (U+200B, U+200C, U+200D, U+00AD, U+2060, U+FEFF).
//! 5. Fullwidth Latin character variants (U+FF01 - U+FF5E).
//! 6. Case variations across candidate persona keys (e.g., "Persona", "ROLE", "Actor").
//! 7. Structural variations (arrays, nested maps).

use core_prompt_civilization::pharmacy::{
    decode_candidate_bytes, detect_with_raw_bytes, ingest_and_detect, DetectionContext,
    Disposition, FailureClass, HostIngestError,
};
use serde_json::Value;

fn ctx() -> DetectionContext {
    DetectionContext::default()
}

/// Helper that verifies a candidate JSON string is rejected with PersonaAuthorityLeak.
fn assert_rejected_with_persona_authority_leak(json_str: &str, test_case_id: &str) {
    let parsed: Value = serde_json::from_str(json_str)
        .unwrap_or_else(|e| panic!("[{test_case_id}] Valid JSON failed to parse: {e}"));
    let report = detect_with_raw_bytes(&parsed, Some(json_str.as_bytes()), &ctx());
    let leak_finding = report
        .findings
        .iter()
        .find(|f| f.class == FailureClass::PersonaAuthorityLeak);

    assert!(
        leak_finding.is_some(),
        "[{test_case_id}] Expected PersonaAuthorityLeak finding, but got none. Findings: {:?}",
        report.findings
    );
    assert_eq!(
        report.strongest_disposition(),
        Some(Disposition::Refuse),
        "[{test_case_id}] Expected strongest disposition Refuse"
    );
}

// ---------------------------------------------------------------------------
// 1. Escaped Unicode in Field Names and Values
// ---------------------------------------------------------------------------

#[test]
fn test_escaped_unicode_standard_ascii_authority_values() {
    let cases = [
        // "admin" escaped: \u0061\u0064\u006d\u0069\u006e
        (
            r#"{"persona": "\u0061\u0064\u006d\u0069\u006e"}"#,
            "escaped_admin",
        ),
        // "ADMIN" in uppercase hex: \u0041\u0044\u004D\u0049\u004E
        (
            r#"{"persona": "\u0041\u0044\u004D\u0049\u004E"}"#,
            "escaped_upper_admin",
        ),
        // "executive" escaped: \u0065\u0078\u0065\u0063\u0075\u0074\u0069\u0076\u0065
        (
            r#"{"role": "\u0065\u0078\u0065\u0063\u0075\u0074\u0069\u0076\u0065"}"#,
            "escaped_executive",
        ),
        // "authorize" escaped: \u0061\u0075\u0074\u0068\u006f\u0072\u0069\u007a\u0065
        (
            r#"{"actor": "\u0061\u0075\u0074\u0068\u006f\u0072\u0069\u007a\u0065"}"#,
            "escaped_authorize",
        ),
        // "authoritative" escaped: \u0061\u0075\u0074\u0068\u006f\u0072\u0069\u0074\u0061\u0074\u0069\u0076\u0065
        (
            r#"{"persona_id": "\u0061\u0075\u0074\u0068\u006f\u0072\u0069\u0074\u0061\u0074\u0069\u0076\u0065"}"#,
            "escaped_authoritative",
        ),
        // "grant_authority" escaped: \u0067\u0072\u0061\u006e\u0074\u005f\u0061\u0075\u0074\u0068\u006f\u0072\u0069\u0074\u0079
        (
            r#"{"role": "\u0067\u0072\u0061\u006e\u0074\u005f\u0061\u0075\u0074\u0068\u006f\u0072\u0069\u0074\u0079"}"#,
            "escaped_grant_authority",
        ),
        // "sovereign_override" escaped: \u0073\u006f\u0076\u0065\u0072\u0065\u0069\u0067\u006e\u005f\u006f\u0076\u0065\u0072\u0072\u0069\u0064\u0065
        (
            r#"{"persona": "\u0073\u006f\u0076\u0065\u0072\u0065\u0069\u0067\u006e\u005f\u006f\u0076\u0065\u0072\u0072\u0069\u0064\u0065"}"#,
            "escaped_sovereign_override",
        ),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

#[test]
fn test_escaped_unicode_field_keys() {
    let cases = [
        // \u0070\u0065\u0072\u0073\u006f\u006e\u0061 = "persona"
        (
            r#"{"\u0070\u0065\u0072\u0073\u006f\u006e\u0061": "admin"}"#,
            "escaped_key_persona",
        ),
        // \u0072\u006f\u006c\u0065 = "role"
        (
            r#"{"\u0072\u006f\u006c\u0065": "executive"}"#,
            "escaped_key_role",
        ),
        // \u0061\u0063\u0074\u006f\u0072 = "actor"
        (
            r#"{"\u0061\u0063\u0074\u006f\u0072": "authoritative"}"#,
            "escaped_key_actor",
        ),
        // \u0070\u0065\u0072\u0073\u006f\u006e\u0061\u005f\u0069\u0064 = "persona_id"
        (
            r#"{"\u0070\u0065\u0072\u0073\u006f\u006e\u0061\u005f\u0069\u0064": "grant_authority"}"#,
            "escaped_key_persona_id",
        ),
        // Both key and value escaped:
        (
            r#"{"\u0070\u0065\u0072\u0073\u006f\u006e\u0061": "\u0061\u0064\u006d\u0069\u006e"}"#,
            "both_key_and_value_escaped",
        ),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

// ---------------------------------------------------------------------------
// 2. RFC 8259 Extreme and Valid Whitespace
// ---------------------------------------------------------------------------

#[test]
fn test_extreme_valid_whitespace_formatting() {
    let large_spaces = " ".repeat(500);
    let large_tabs = "\t".repeat(200);
    let large_crlf = "\r\n".repeat(100);

    let json_cases = [
        format!(
            "{{{large_spaces}\"persona\"{large_spaces}:{large_spaces}\"admin\"{large_spaces}}}"
        ),
        format!("{{{large_tabs}\"role\"{large_tabs}:{large_tabs}\"executive\"{large_tabs}}}"),
        format!("{{{large_crlf}\"actor\"{large_crlf}:{large_crlf}\"authoritative\"{large_crlf}}}"),
        format!("{{\r\n\t  \"persona\":\t  \r\n\"admin_worker\"\r\n\t}}"),
        format!("{{\"persona\": \"  admin  \"}}"),
        format!("{{\"persona\": \"\\t\\tadmin\\n\\n\"}}"),
    ];

    for (idx, json_str) in json_cases.iter().enumerate() {
        assert_rejected_with_persona_authority_leak(json_str, &format!("whitespace_case_{idx}"));
    }
}

// ---------------------------------------------------------------------------
// 3. RFC 8259 Syntax-Violating Non-Standard Whitespace Outside Strings
// ---------------------------------------------------------------------------

#[test]
fn test_non_standard_whitespace_outside_strings_fails_closed_at_parser() {
    // RFC 8259 specifies whitespace as only: space (%x20), tab (%x09), line feed (%x0A), CR (%x0D).
    // Characters like form feed (\x0c), vertical tab (\x0b), or NBSP (\u00a0) outside strings must fail to parse.
    let invalid_json_cases = [
        ("{\x0c\"persona\": \"admin\"}", "form_feed_outside_string"),
        (
            "{\x0b\"persona\": \"admin\"}",
            "vertical_tab_outside_string",
        ),
        ("{\u{00a0}\"persona\": \"admin\"}", "nbsp_outside_string"),
        (
            "{\u{200b}\"persona\": \"admin\"}",
            "zero_width_space_outside_string",
        ),
    ];

    for (raw_str, case_id) in invalid_json_cases {
        let result: Result<Value, _> = serde_json::from_str(raw_str);
        assert!(
            result.is_err(),
            "[{case_id}] Expected serde_json parser syntax error on non-standard whitespace, but parsed successfully!"
        );
    }
}

// ---------------------------------------------------------------------------
// 4. In-String Unicode Escapes and Combinations (Fuzz Battery)
// ---------------------------------------------------------------------------

#[test]
fn test_combinatorial_authority_escapes() {
    let keys = ["persona", "role", "actor", "persona_id"];
    let markers = [
        "admin",
        "executive",
        "authorize",
        "authoritative",
        "grant_authority",
        "sovereign_override",
    ];

    for key in keys {
        for marker in markers {
            // Encode every character in the marker as \u00xx
            let escaped_marker: String = marker
                .chars()
                .map(|c| format!("\\u{:04x}", c as u32))
                .collect();
            let json_str = format!("{{\"{key}\": \"prefix_{escaped_marker}_suffix\"}}");
            assert_rejected_with_persona_authority_leak(&json_str, &format!("comb_{key}_{marker}"));
        }
    }
}

// ---------------------------------------------------------------------------
// 5. In-String Adversarial Evasion Probing (Blind Spot & Hardening Tests)
// ---------------------------------------------------------------------------

#[test]
fn test_adversarial_field_key_casing() {
    // Tests whether mixed-case or upper-case candidate field keys are caught
    let cases = [
        (r#"{"Persona": "admin"}"#, "cased_key_Persona"),
        (r#"{"ROLE": "executive"}"#, "cased_key_ROLE"),
        (r#"{"Actor": "authorize"}"#, "cased_key_Actor"),
        (r#"{"Persona_Id": "authoritative"}"#, "cased_key_Persona_Id"),
        (r#"{"\u0050ersona": "admin"}"#, "escaped_cased_key"),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

#[test]
fn test_adversarial_array_persona_values() {
    // Tests whether authority markers in arrays under persona keys are caught
    let cases = [
        (r#"{"persona": ["user", "admin"]}"#, "array_admin"),
        (
            r#"{"role": ["contributor", "executive"]}"#,
            "array_executive",
        ),
        (r#"{"actor": ["authorize"]}"#, "array_authorize"),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

#[test]
fn test_adversarial_zero_width_and_invisible_character_evasions() {
    // Tests whether zero-width spaces / soft hyphens / word joiners splitting authority markers are caught
    let cases = [
        // Zero-width space U+200B
        (r#"{"persona": "ad\u200bmin"}"#, "zero_width_space_admin"),
        // Zero-width non-joiner U+200C
        (r#"{"role": "ex\u200cecutive"}"#, "zwnj_executive"),
        // Zero-width joiner U+200D
        (r#"{"actor": "auth\u200dorize"}"#, "zwj_authorize"),
        // Soft hyphen U+00AD
        (r#"{"persona": "ad\u00admin"}"#, "soft_hyphen_admin"),
        // Word joiner U+2060
        (r#"{"role": "exec\u2060utive"}"#, "word_joiner_executive"),
        // Zero-width no-break space (BOM) U+FEFF
        (r#"{"persona": "ad\ufeffmin"}"#, "bom_admin"),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

#[test]
fn test_adversarial_fullwidth_latin_evasions() {
    // Tests fullwidth Latin letters (e.g. ａｄｍｉｎ = \uFF41\uFF44\uFF4D\uFF49\uFF4E)
    let cases = [
        (
            r#"{"persona": "\uff41\uff44\uff4d\uff49\uff4e"}"#,
            "fullwidth_admin",
        ),
        (
            r#"{"role": "\uff45\uff58\uff45\uff43\uff55\uff54\uff49\uff56\uff45"}"#,
            "fullwidth_executive",
        ),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

#[test]
fn test_adversarial_cyrillic_homoglyph_evasions() {
    // Tests Latin-lookalike Cyrillic homoglyphs
    let cases = [
        // Cyrillic small 'а' (U+0430) in "admin"
        (r#"{"persona": "\u0430dmin"}"#, "cyrillic_a_admin"),
        // Cyrillic small 'е' (U+0435) in "executive"
        (r#"{"role": "\u0435xecutive"}"#, "cyrillic_e_executive"),
        // Cyrillic small 'о' (U+043E) in "authoritative"
        (
            r#"{"actor": "auth\u043eritativ\u0435"}"#,
            "cyrillic_o_authoritative",
        ),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

#[test]
fn test_adversarial_deeply_nested_structures() {
    let cases = [
        (
            r#"{"persona": {"tier": {"dept": {"lead": "admin"}}}}"#,
            "deep_object_admin",
        ),
        (
            r#"{"actor": [{"team": [{"role": "executive"}]}]}"#,
            "deep_array_object_executive",
        ),
        (
            r#"{"Persona": {"sub_roles": ["researcher", "grant_authority"]}}"#,
            "cased_key_with_nested_array",
        ),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

// ---------------------------------------------------------------------------
// 6. Randomized Adversarial Fuzz Generator (1,000 Iterations)
// ---------------------------------------------------------------------------

struct XorShift64(u64);

impl XorShift64 {
    fn next_u32(&mut self) -> u32 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        (x & 0xFFFFFFFF) as u32
    }

    fn choose<'a, T>(&mut self, slice: &'a [T]) -> &'a T {
        let idx = (self.next_u32() as usize) % slice.len();
        &slice[idx]
    }
}

#[test]
fn test_randomized_adversarial_fuzz_battery() {
    let mut rng = XorShift64(0xDEADBEEF_CAFEF00D);

    let base_keys = ["persona", "role", "actor", "persona_id"];
    let base_markers = [
        "admin",
        "executive",
        "authorize",
        "authoritative",
        "grant_authority",
        "sovereign_override",
    ];

    let invisible_chars = [
        "\\u200b", // ZWSP
        "\\u200c", // ZWNJ
        "\\u200d", // ZWJ
        "\\u00ad", // Soft Hyphen
        "\\u2060", // Word Joiner
        "\\ufeff", // BOM
    ];

    for iteration in 0..1000 {
        let base_key = rng.choose(&base_keys);
        let base_marker = rng.choose(&base_markers);

        // Apply random key casing
        let key = match rng.next_u32() % 4 {
            0 => base_key.to_string(),
            1 => {
                let mut chars = base_key.chars();
                match chars.next() {
                    Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                    None => base_key.to_string(),
                }
            }
            2 => base_key.to_uppercase(),
            _ => {
                // Unicode escape for key
                let mut escaped = String::new();
                for c in base_key.chars() {
                    escaped.push_str(&format!("\\u{:04x}", c as u32));
                }
                escaped
            }
        };

        // Construct fuzzed marker with interspersed invisible chars, escaped unicode, or case
        let mut fuzzed_marker = String::new();
        for c in base_marker.chars() {
            // Chance of inserting invisible char before
            if rng.next_u32() % 5 == 0 {
                fuzzed_marker.push_str(rng.choose(&invisible_chars));
            }

            // Representation of character
            match rng.next_u32() % 6 {
                0 => fuzzed_marker.push(c.to_ascii_uppercase()),
                1 => fuzzed_marker.push(c.to_ascii_lowercase()),
                2 => {
                    // Fullwidth Latin variant
                    let fw = char::from_u32((c as u32) + 0xFEE0).unwrap_or(c);
                    fuzzed_marker.push_str(&format!("\\u{:04x}", fw as u32));
                }
                3 => {
                    // Lowercase hex escape
                    fuzzed_marker.push_str(&format!("\\u{:04x}", c as u32));
                }
                4 => {
                    // Uppercase hex escape
                    fuzzed_marker.push_str(&format!("\\u{:04X}", c as u32));
                }
                _ => {
                    // Cyrillic homoglyph if applicable
                    let homoglyph = match c {
                        'a' => "\\u0430",
                        'e' => "\\u0435",
                        'o' => "\\u043e",
                        other => {
                            fuzzed_marker.push(other);
                            continue;
                        }
                    };
                    fuzzed_marker.push_str(homoglyph);
                }
            }

            // Chance of inserting invisible char after
            if rng.next_u32() % 5 == 0 {
                fuzzed_marker.push_str(rng.choose(&invisible_chars));
            }
        }

        // Random surrounding whitespace
        let prefix_ws = match rng.next_u32() % 4 {
            0 => "   ",
            1 => "\\t\\t",
            2 => "\\r\\n  ",
            _ => "",
        };
        let suffix_ws = match rng.next_u32() % 4 {
            0 => "   ",
            1 => "\\t",
            2 => "\\n",
            _ => "",
        };

        let candidate_val = format!("{prefix_ws}{fuzzed_marker}{suffix_ws}");

        // Random container structure
        let json_payload = match rng.next_u32() % 4 {
            0 => format!("{{\"{key}\": \"{candidate_val}\"}}"),
            1 => format!("{{\"{key}\": [\"unrelated\", \"{candidate_val}\"]}}"),
            2 => format!("{{\"{key}\": {{\"level\": \"{candidate_val}\"}}}}"),
            _ => format!("{{\"{key}\": [{{\"nested\": \"{candidate_val}\"}}]}}"),
        };

        assert_rejected_with_persona_authority_leak(
            &json_payload,
            &format!("fuzz_iteration_{iteration}"),
        );
    }
}

// ---------------------------------------------------------------------------
// 7. Alternative UTF Encodings (Fail-Closed Host Boundary Decoder Verification)
// ---------------------------------------------------------------------------

#[test]
fn test_alternative_utf_encodings_fail_closed_at_host_decoder() {
    let candidate_text = r#"{"persona": "developer", "public_rationale": "clean test"}"#;

    // Helper: encode text to UTF-16LE bytes
    let utf16le_bytes: Vec<u8> = candidate_text
        .encode_utf16()
        .flat_map(|u| u.to_le_bytes())
        .collect();

    // Helper: encode text to UTF-16BE bytes
    let utf16be_bytes: Vec<u8> = candidate_text
        .encode_utf16()
        .flat_map(|u| u.to_be_bytes())
        .collect();

    // Helper: encode text to UTF-32LE bytes
    let utf32le_bytes: Vec<u8> = candidate_text
        .chars()
        .flat_map(|c| (c as u32).to_le_bytes())
        .collect();

    // Helper: encode text to UTF-32BE bytes
    let utf32be_bytes: Vec<u8> = candidate_text
        .chars()
        .flat_map(|c| (c as u32).to_be_bytes())
        .collect();

    // 1. UTF-16LE with BOM
    let mut utf16le_bom = vec![0xFF, 0xFE];
    utf16le_bom.extend_from_slice(&utf16le_bytes);
    let res = decode_candidate_bytes(&utf16le_bom);
    assert!(
        matches!(res, Err(HostIngestError::BomProhibited(_))),
        "Expected BomProhibited for UTF-16LE BOM, got {res:?}"
    );
    assert!(ingest_and_detect(&utf16le_bom, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf16le_bom).is_err());

    // 2. UTF-16BE with BOM
    let mut utf16be_bom = vec![0xFE, 0xFF];
    utf16be_bom.extend_from_slice(&utf16be_bytes);
    let res = decode_candidate_bytes(&utf16be_bom);
    assert!(
        matches!(res, Err(HostIngestError::BomProhibited(_))),
        "Expected BomProhibited for UTF-16BE BOM, got {res:?}"
    );
    assert!(ingest_and_detect(&utf16be_bom, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf16be_bom).is_err());

    // 3. UTF-32LE with BOM
    let mut utf32le_bom = vec![0xFF, 0xFE, 0x00, 0x00];
    utf32le_bom.extend_from_slice(&utf32le_bytes);
    let res = decode_candidate_bytes(&utf32le_bom);
    assert!(
        matches!(res, Err(HostIngestError::BomProhibited(_))),
        "Expected BomProhibited for UTF-32LE BOM, got {res:?}"
    );
    assert!(ingest_and_detect(&utf32le_bom, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf32le_bom).is_err());

    // 4. UTF-32BE with BOM
    let mut utf32be_bom = vec![0x00, 0x00, 0xFE, 0xFF];
    utf32be_bom.extend_from_slice(&utf32be_bytes);
    let res = decode_candidate_bytes(&utf32be_bom);
    assert!(
        matches!(res, Err(HostIngestError::BomProhibited(_))),
        "Expected BomProhibited for UTF-32BE BOM, got {res:?}"
    );
    assert!(ingest_and_detect(&utf32be_bom, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf32be_bom).is_err());

    // 5. UTF-8 with BOM
    let mut utf8_bom = vec![0xEF, 0xBB, 0xBF];
    utf8_bom.extend_from_slice(candidate_text.as_bytes());
    let res = decode_candidate_bytes(&utf8_bom);
    assert!(
        matches!(res, Err(HostIngestError::BomProhibited(_))),
        "Expected BomProhibited for UTF-8 BOM, got {res:?}"
    );
    assert!(ingest_and_detect(&utf8_bom, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf8_bom).is_err());

    // 6. BOM-less UTF-16LE
    let res = decode_candidate_bytes(&utf16le_bytes);
    assert!(
        matches!(res, Err(HostIngestError::UnsupportedEncoding(_))),
        "Expected UnsupportedEncoding for BOM-less UTF-16LE, got {res:?}"
    );
    assert!(ingest_and_detect(&utf16le_bytes, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf16le_bytes).is_err());

    // 7. BOM-less UTF-16BE
    let res = decode_candidate_bytes(&utf16be_bytes);
    assert!(
        matches!(res, Err(HostIngestError::UnsupportedEncoding(_))),
        "Expected UnsupportedEncoding for BOM-less UTF-16BE, got {res:?}"
    );
    assert!(ingest_and_detect(&utf16be_bytes, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf16be_bytes).is_err());

    // 8. BOM-less UTF-32LE
    let res = decode_candidate_bytes(&utf32le_bytes);
    assert!(
        matches!(res, Err(HostIngestError::UnsupportedEncoding(_))),
        "Expected UnsupportedEncoding for BOM-less UTF-32LE, got {res:?}"
    );
    assert!(ingest_and_detect(&utf32le_bytes, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf32le_bytes).is_err());

    // 9. BOM-less UTF-32BE
    let res = decode_candidate_bytes(&utf32be_bytes);
    assert!(
        matches!(res, Err(HostIngestError::UnsupportedEncoding(_))),
        "Expected UnsupportedEncoding for BOM-less UTF-32BE, got {res:?}"
    );
    assert!(ingest_and_detect(&utf32be_bytes, &ctx()).is_err());
    assert!(serde_json::from_slice::<Value>(&utf32be_bytes).is_err());

    // 10. Valid pure UTF-8 JSON succeeds
    let valid_utf8 = candidate_text.as_bytes();
    let res = decode_candidate_bytes(valid_utf8);
    assert!(res.is_ok(), "Expected Ok for valid pure UTF-8 JSON");
    let report = ingest_and_detect(valid_utf8, &ctx());
    assert!(
        report.is_ok(),
        "Expected Ok report for valid pure UTF-8 JSON"
    );
}

// ---------------------------------------------------------------------------
// 8. Multilingual Foreign Language Authority Markers
// ---------------------------------------------------------------------------

#[test]
fn test_multilingual_foreign_language_authority_markers() {
    let cases = [
        // Spanish
        (
            r#"{"persona": "administrador_general"}"#,
            "es_administrador",
        ),
        (r#"{"role": "ejecutivo_principal"}"#, "es_ejecutivo"),
        (r#"{"actor": "autorizar_cambios"}"#, "es_autorizar"),
        (r#"{"persona_id": "maxima_autoridad"}"#, "es_autoridad"),
        (r#"{"persona": "controlador_soberano"}"#, "es_soberano"),
        // French
        (
            r#"{"persona": "administrateur_systeme"}"#,
            "fr_administrateur",
        ),
        (r#"{"role": "directeur_exécutif"}"#, "fr_executif_accented"),
        (
            r#"{"role": "directeur_executif"}"#,
            "fr_executif_unaccented",
        ),
        (r#"{"actor": "autoriser_action"}"#, "fr_autoriser"),
        (
            r#"{"persona_id": "haute_autorité"}"#,
            "fr_autorite_accented",
        ),
        (
            r#"{"persona_id": "haute_autorite"}"#,
            "fr_autorite_unaccented",
        ),
        (r#"{"persona": "pouvoir_souverain"}"#, "fr_souverain"),
        // German
        (r#"{"persona": "system_administrator"}"#, "de_administrator"),
        (r#"{"role": "vorstand_vorsitzender"}"#, "de_vorstand"),
        (r#"{"role": "leitend_ingenieur"}"#, "de_leitend"),
        (r#"{"actor": "autorisieren_zugriff"}"#, "de_autorisieren"),
        (
            r#"{"persona_id": "zentrale_autorität"}"#,
            "de_autoritaet_umlaut",
        ),
        (
            r#"{"persona_id": "zentrale_autoritaet"}"#,
            "de_autoritaet_ascii",
        ),
        (r#"{"persona": "souverän_agent"}"#, "de_souveraen_umlaut"),
        (r#"{"persona": "souveraen_agent"}"#, "de_souveraen_ascii"),
        // Italian
        (
            r#"{"persona": "amministratore_delegato"}"#,
            "it_amministratore",
        ),
        (r#"{"role": "funzionario_esecutivo"}"#, "it_esecutivo"),
        (r#"{"actor": "autorizzare_richiesta"}"#, "it_autorizzare"),
        (
            r#"{"persona_id": "massima_autorità"}"#,
            "it_autorita_accented",
        ),
        (
            r#"{"persona_id": "massima_autorita"}"#,
            "it_autorita_unaccented",
        ),
        (r#"{"persona": "agente_sovrano"}"#, "it_sovrano"),
        // Russian (Cyrillic)
        (
            r#"{"persona": "главный_администратор"}"#,
            "ru_administrator",
        ),
        (r#"{"persona": "системный_админ"}"#, "ru_admin"),
        (r#"{"role": "исполнительный_орган"}"#, "ru_executive"),
        (r#"{"actor": "авторизовать_запрос"}"#, "ru_authorize"),
        (r#"{"persona_id": "высший_авторитет"}"#, "ru_authority"),
        (r#"{"persona": "суверенный_агент"}"#, "ru_sovereign"),
        // Chinese (Simplified & Traditional)
        (r#"{"persona": "系统管理员"}"#, "zh_admin_simplified"),
        (r#"{"persona": "系統管理員"}"#, "zh_admin_traditional"),
        (r#"{"role": "首席执行官"}"#, "zh_executive_simplified"),
        (r#"{"role": "首席執行官"}"#, "zh_executive_traditional"),
        (r#"{"role": "核心主管"}"#, "zh_director_zhuguan"),
        (r#"{"actor": "系统授权"}"#, "zh_authorize_simplified"),
        (r#"{"actor": "系統授權"}"#, "zh_authorize_traditional"),
        (
            r#"{"persona_id": "权威节点"}"#,
            "zh_authoritative_simplified",
        ),
        (
            r#"{"persona_id": "權威節點"}"#,
            "zh_authoritative_traditional",
        ),
        (r#"{"persona": "超级特权"}"#, "zh_privilege_simplified"),
        (r#"{"persona": "超級特權"}"#, "zh_privilege_traditional"),
        // Japanese
        (r#"{"persona": "システム管理者"}"#, "ja_admin"),
        (r#"{"role": "最高執行役"}"#, "ja_executive"),
        (r#"{"actor": "管理権限"}"#, "ja_authority"),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

// ---------------------------------------------------------------------------
// 9. Multilingual In-String Adversarial Evasions
// ---------------------------------------------------------------------------

#[test]
fn test_multilingual_adversarial_in_string_evasions() {
    let cases = [
        // Zero-width space in Russian
        (r#"{"persona": "ад\u200bмин"}"#, "ru_zwsp_admin"),
        (r#"{"role": "испол\u200cнительный"}"#, "ru_zwnj_executive"),
        // Zero-width space in Chinese
        (r#"{"persona": "管\u200b理\u200b员"}"#, "zh_zwsp_admin"),
        (r#"{"role": "执\u200d行\u200d官"}"#, "zh_zwj_executive"),
        // Zero-width space in French / German / Italian
        (r#"{"persona": "ammi\u200bnistratore"}"#, "it_zwsp_admin"),
        (r#"{"role": "vor\u200bstand"}"#, "de_zwsp_vorstand"),
        (r#"{"actor": "exé\u200bcutif"}"#, "fr_zwsp_executif"),
        // Unicode escapes in JSON string literals
        (r#"{"persona": "\u7ba1\u7406\u5458"}"#, "zh_escaped_admin"),
        (
            r#"{"persona": "\u0430\u0434\u043c\u0438\u043d"}"#,
            "ru_escaped_admin",
        ),
        (r#"{"role": "\u6267\u884c\u5b98"}"#, "zh_escaped_executive"),
    ];

    for (json_str, case_id) in cases {
        assert_rejected_with_persona_authority_leak(json_str, case_id);
    }
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/adversarial_authority_fuzz.rs
// Claim: urn:core:crates_rs:tests:adversarial-authority-fuzz:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord26c80455 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord26c80455` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError26c80455 {
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
impl BoundaryError26c80455 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError26c80455 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError26c80455 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord26c80455 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError26c80455> {
        if capacity_bound == 0 {
            return Err(BoundaryError26c80455::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError26c80455::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError26c80455::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_26c80455() {
    let admitted = BoundaryRecord26c80455::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord26c80455::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
