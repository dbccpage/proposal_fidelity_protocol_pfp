//! DDC Tape Parser & Candidate Runtime Law Verifier.
//!
//! Translates Discrete Deformation Calculus (DDC) 8-letter event tapes (ddc.jsonl)
//! into verified operational receipts, enforces candidate runtime laws,
//! and computes exact rational residual contraction receipts.
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

pub const DDC_CANONICAL_LETTERS: &[&str] = core_operad_canon::DdcOp::LETTERS;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DdcParserRefusal {
    pub code: String,
    pub message: String,
    pub locus: String,
}

impl std::fmt::Display for DdcParserRefusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}

impl std::error::Error for DdcParserRefusal {}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DdcParsedStep {
    pub sequence: usize,
    pub letter: String,
    pub parent_sha256: Option<String>,
    pub record_sha256: String,
    pub before_class: String,
    pub after_class: String,
    pub carrier_hash: String,
    pub phi_1: Option<BigRational>,
    pub gamma_2: Option<BigRational>,
}

impl DdcParsedStep {
    pub fn total_residual(&self) -> Option<BigRational> {
        match (&self.phi_1, &self.gamma_2) {
            (None, None) => None,
            (Some(p), None) => Some(p.clone()),
            (None, Some(g)) => Some(g.clone()),
            (Some(p), Some(g)) => Some(p + g),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DdcTapeReceipt {
    pub step_count: usize,
    pub tape_str: String,
    pub hash_chain_valid: bool,
    pub ddc_laws_valid: bool,
    pub law_violations: Vec<String>,
    pub initial_phi1: Option<String>,
    pub initial_gamma2: Option<String>,
    pub terminal_phi1: Option<String>,
    pub terminal_gamma2: Option<String>,
    pub initial_residual: Option<String>,
    pub terminal_residual: Option<String>,
    pub residual_delta: Option<String>,
    pub residual_effect: String,
    pub authority_effect: String,
}

/// Largest decimal exponent magnitude accepted by [`parse_fraction_str`].
///
/// The value is exact for every exponent, but `10^e` is materialised as a
/// big integer; the bound keeps one hostile field from forcing an unbounded
/// allocation.
pub const MAX_DECIMAL_EXPONENT: u32 = 4096;

fn residual_refusal(field: &str, text: &str, reason: &str) -> DdcParserRefusal {
    DdcParserRefusal {
        code: "INVALID_RESIDUAL_TEXT".to_string(),
        message: format!("{field} value {text:?} is not an exact rational: {reason}"),
        locus: "crate::ddc::parser".to_string(),
    }
}

fn is_ascii_digits(text: &str) -> bool {
    !text.is_empty() && text.bytes().all(|b| b.is_ascii_digit())
}

/// Parse an optionally signed decimal `[+-]digits[.digits][(e|E)[+-]digits]`
/// (at least one digit before or after the point) exactly into a rational.
/// Returns `Err(reason)` when the text is not in that grammar.
fn parse_decimal_exact(text: &str) -> Result<BigRational, &'static str> {
    let (negative, body) = match text.as_bytes().first() {
        Some(b'-') => (true, &text[1..]),
        Some(b'+') => (false, &text[1..]),
        _ => (false, text),
    };
    let (mantissa, exponent_text) = match body.find(['e', 'E']) {
        Some(index) => (&body[..index], Some(&body[index + 1..])),
        None => (body, None),
    };
    let (int_part, frac_part) = match mantissa.split_once('.') {
        Some((i, f)) => (i, f),
        None => (mantissa, ""),
    };
    if int_part.is_empty() && frac_part.is_empty() {
        return Err("no digits");
    }
    if (!int_part.is_empty() && !is_ascii_digits(int_part))
        || (!frac_part.is_empty() && !is_ascii_digits(frac_part))
    {
        return Err("mantissa is not decimal digits");
    }
    let exponent: i64 = match exponent_text {
        None => 0,
        Some(e) => {
            let digits = e.strip_prefix(['+', '-']).unwrap_or(e);
            if !is_ascii_digits(digits) {
                return Err("exponent is not decimal digits");
            }
            let magnitude: u32 = digits
                .parse()
                .ok()
                .filter(|m| *m <= MAX_DECIMAL_EXPONENT)
                .ok_or("exponent magnitude exceeds MAX_DECIMAL_EXPONENT")?;
            if e.starts_with('-') {
                -i64::from(magnitude)
            } else {
                i64::from(magnitude)
            }
        }
    };
    let digits = format!("{int_part}{frac_part}");
    let mut numerator: num_bigint::BigInt = digits
        .parse()
        .map_err(|_| "mantissa is not decimal digits")?;
    if negative {
        numerator = -numerator;
    }
    let scale = exponent - frac_part.len() as i64;
    let ten = num_bigint::BigInt::from(10);
    let power = |k: i64| -> Result<num_bigint::BigInt, &'static str> {
        let k = u32::try_from(k).map_err(|_| "decimal scale out of range")?;
        Ok(num_traits::pow::Pow::pow(&ten, k))
    };
    if scale >= 0 {
        Ok(BigRational::from_integer(numerator * power(scale)?))
    } else {
        Ok(BigRational::new(numerator, power(-scale)?))
    }
}

/// Parse residual text exactly.
///
/// * `""` and `"None"` mean the field is absent and yield `Ok(None)`.
/// * `"p/q"` (integers, optional signs, `q != 0`) yields `p/q` in lowest terms.
/// * An integer or a decimal `[+-]d[.d][e[+-]d]` yields its exact value, so
///   `"0.1"` is `1/10`, never the binary float nearest to it.
///
/// Anything else (`"NaN"`, `"inf"`, `"1/0"`, stray characters) is refused with
/// the typed `INVALID_RESIDUAL_TEXT` refusal. No floating point is used.
pub fn parse_fraction_str(val: &str) -> Result<Option<BigRational>, DdcParserRefusal> {
    parse_residual_text("residual", val)
}

fn parse_residual_text(field: &str, val: &str) -> Result<Option<BigRational>, DdcParserRefusal> {
    let trimmed = val.trim();
    if trimmed.is_empty() || trimmed == "None" {
        return Ok(None);
    }
    if let Some((num_s, den_s)) = trimmed.split_once('/') {
        let num: num_bigint::BigInt = num_s
            .trim()
            .parse()
            .map_err(|_| residual_refusal(field, val, "numerator is not an integer"))?;
        let den: num_bigint::BigInt = den_s
            .trim()
            .parse()
            .map_err(|_| residual_refusal(field, val, "denominator is not an integer"))?;
        if den.is_zero() {
            return Err(residual_refusal(field, val, "zero denominator"));
        }
        return Ok(Some(BigRational::new(num, den)));
    }
    if let Ok(n) = trimmed.parse::<num_bigint::BigInt>() {
        return Ok(Some(BigRational::from_integer(n)));
    }
    parse_decimal_exact(trimmed)
        .map(Some)
        .map_err(|reason| residual_refusal(field, val, reason))
}

/// Read one residual field of a DDC payload.
///
/// A missing key or JSON `null` is absent. A string goes through
/// [`parse_fraction_str`]. A JSON integer is taken exactly. Any other JSON
/// value — a non-integral number, a boolean, an array or object — is refused:
/// a JSON number with a fraction part has already been read as a binary float
/// by most readers, so exact residuals must travel as strings.
fn parse_residual_field(
    payload: &BTreeMap<String, serde_json::Value>,
    field: &str,
) -> Result<Option<BigRational>, DdcParserRefusal> {
    match payload.get(field) {
        None | Some(serde_json::Value::Null) => Ok(None),
        Some(serde_json::Value::String(text)) => parse_residual_text(field, text),
        Some(serde_json::Value::Number(number)) => {
            if let Some(n) = number.as_i64() {
                Ok(Some(BigRational::from_integer(n.into())))
            } else if let Some(n) = number.as_u64() {
                Ok(Some(BigRational::from_integer(n.into())))
            } else {
                Err(residual_refusal(
                    field,
                    &number.to_string(),
                    "non-integral JSON number; send the exact value as a string",
                ))
            }
        }
        Some(other) => Err(residual_refusal(
            field,
            &other.to_string(),
            "expected a string, an integer or null",
        )),
    }
}

pub fn format_fraction(val: &BigRational) -> String {
    if val.denom() == &num_bigint::BigInt::from(1) {
        val.numer().to_string()
    } else {
        format!("{}/{}", val.numer(), val.denom())
    }
}

pub fn normalize_rune_letter(raw: &str) -> String {
    let t = raw.trim();
    match t {
        "L" | "Lambda" | "\\Lambda" | "Meta" => "Λ".to_string(),
        other => other.to_string(),
    }
}

pub struct DdcTapeParser;

impl DdcTapeParser {
    pub fn parse_records(
        records: &[serde_json::Value],
    ) -> Result<DdcTapeReceipt, DdcParserRefusal> {
        if records.is_empty() {
            return Err(DdcParserRefusal {
                code: "EMPTY_DDC_TAPE".to_string(),
                message: "DDC tape contains zero action records".to_string(),
                locus: "crate::ddc::parser".to_string(),
            });
        }

        let mut steps = Vec::with_capacity(records.len());
        let mut expected_parent_sha: Option<String> = None;

        for (idx, record) in records.iter().enumerate() {
            let seq = record["sequence"].as_u64().unwrap_or(idx as u64) as usize;
            let parent_sha = record["parent_sha256"].as_str().map(|s| s.to_string());
            let rec_sha = record["record_sha256"].as_str().unwrap_or("").to_string();

            // Hash chain validation
            if parent_sha != expected_parent_sha {
                return Err(DdcParserRefusal {
                    code: "HASH_CHAIN_BROKEN".to_string(),
                    message: format!(
                        "Step {seq} parent_sha256='{}' does not match expected '{}'",
                        parent_sha.as_deref().unwrap_or("None"),
                        expected_parent_sha.as_deref().unwrap_or("None"),
                    ),
                    locus: "crate::ddc::parser".to_string(),
                });
            }

            // Verify SHA256 of payload
            let payload_val = &record["payload"];
            let canonical_payload: BTreeMap<String, serde_json::Value> = match payload_val {
                serde_json::Value::Object(map) => {
                    map.iter().map(|(k, v)| (k.clone(), v.clone())).collect()
                }
                _ => BTreeMap::new(),
            };

            let serialization_refusal = |e: serde_json::Error| DdcParserRefusal {
                code: "SERIALIZATION_ERROR".to_string(),
                message: e.to_string(),
                locus: "crate::ddc::parser".to_string(),
            };
            let mut material_map = BTreeMap::new();
            material_map.insert(
                "parent_sha256",
                serde_json::to_value(&parent_sha).map_err(serialization_refusal)?,
            );
            material_map.insert(
                "payload",
                serde_json::to_value(&canonical_payload).map_err(serialization_refusal)?,
            );
            material_map.insert(
                "sequence",
                serde_json::to_value(seq).map_err(serialization_refusal)?,
            );

            let material_bytes =
                serde_json::to_vec(&material_map).map_err(|e| DdcParserRefusal {
                    code: "SERIALIZATION_ERROR".to_string(),
                    message: e.to_string(),
                    locus: "crate::ddc::parser".to_string(),
                })?;

            let mut hasher = Sha256::new();
            hasher.update(&material_bytes);
            let computed_rec_sha = hex::encode(hasher.finalize());

            if !rec_sha.is_empty() && rec_sha != computed_rec_sha {
                return Err(DdcParserRefusal {
                    code: "HASH_CHAIN_BROKEN".to_string(),
                    message: format!(
                        "Step {seq} record_sha256 '{rec_sha}' does not match computed '{computed_rec_sha}'"
                    ),
                    locus: "crate::ddc::parser".to_string(),
                });
            }

            let raw_letter = canonical_payload
                .get("letter")
                .and_then(|v| v.as_str())
                .unwrap_or("M");
            let norm_letter = normalize_rune_letter(raw_letter);

            let phi_1 = parse_residual_field(&canonical_payload, "phi_1")?;
            let gamma_2 = parse_residual_field(&canonical_payload, "gamma_2")?;

            steps.push(DdcParsedStep {
                sequence: seq,
                letter: norm_letter,
                parent_sha256: parent_sha,
                record_sha256: computed_rec_sha.clone(),
                before_class: canonical_payload
                    .get("before_class")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string(),
                after_class: canonical_payload
                    .get("after_class")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string(),
                carrier_hash: canonical_payload
                    .get("carrier_hash")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string(),
                phi_1,
                gamma_2,
            });

            expected_parent_sha = Some(computed_rec_sha);
        }

        // Verify Candidate Laws
        let mut violations = Vec::new();
        let mut terminal_seen = false;
        let mut prev_phi1: Option<&BigRational> = None;

        for step in &steps {
            if !DDC_CANONICAL_LETTERS.contains(&step.letter.as_str()) {
                violations.push(format!(
                    "CanonicalAlphabet: step {} rune '{}' not in canonical alphabet",
                    step.sequence, step.letter
                ));
            }

            if terminal_seen {
                violations.push(format!(
                    "TerminalAbsorbing: step {} '{}' appeared after terminalization 'T'",
                    step.sequence, step.letter
                ));
            }

            if step.letter == "T" {
                terminal_seen = true;
            }

            if step.letter == "E" {
                if let (Some(prev), Some(curr)) = (prev_phi1, &step.phi_1) {
                    if curr > prev {
                        violations.push(format!(
                            "ExactRepairIncreasedPhi1: step {} 'E' increased phi_1 from {} to {}",
                            step.sequence,
                            format_fraction(prev),
                            format_fraction(curr),
                        ));
                    }
                }
            }

            if let Some(ref p) = step.phi_1 {
                prev_phi1 = Some(p);
            }
        }

        let ddc_laws_valid = violations.is_empty();

        // Calculate Residual Contraction
        let init_phi1 = steps.first().and_then(|s| s.phi_1.as_ref());
        let init_gamma2 = steps.first().and_then(|s| s.gamma_2.as_ref());
        let term_phi1 = steps.last().and_then(|s| s.phi_1.as_ref());
        let term_gamma2 = steps.last().and_then(|s| s.gamma_2.as_ref());

        let init_tot = steps.first().and_then(|s| s.total_residual());
        let term_tot = steps.last().and_then(|s| s.total_residual());

        let (residual_delta, residual_effect) = match (&init_tot, &term_tot) {
            (Some(i), Some(t)) => {
                let delta = t - i;
                let effect = if t.is_zero() {
                    "exact".to_string()
                } else if delta.is_negative() {
                    "contractive".to_string()
                } else {
                    "non_contractive".to_string()
                };
                (Some(format_fraction(&delta)), effect)
            }
            _ => (None, "unknown".to_string()),
        };

        let tape_str = steps
            .iter()
            .map(|s| s.letter.as_str())
            .collect::<Vec<_>>()
            .join(".");

        Ok(DdcTapeReceipt {
            step_count: steps.len(),
            tape_str,
            hash_chain_valid: true,
            ddc_laws_valid,
            law_violations: violations,
            initial_phi1: init_phi1.map(format_fraction),
            initial_gamma2: init_gamma2.map(format_fraction),
            terminal_phi1: term_phi1.map(format_fraction),
            terminal_gamma2: term_gamma2.map(format_fraction),
            initial_residual: init_tot.as_ref().map(format_fraction),
            terminal_residual: term_tot.as_ref().map(format_fraction),
            residual_delta,
            residual_effect,
            authority_effect: "None".to_string(),
        })
    }

    pub fn parse_jsonl(jsonl_content: &str) -> Result<DdcTapeReceipt, DdcParserRefusal> {
        let mut records = Vec::new();
        for line in jsonl_content.lines() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            let val: serde_json::Value =
                serde_json::from_str(trimmed).map_err(|e| DdcParserRefusal {
                    code: "JSON_PARSE_ERROR".to_string(),
                    message: e.to_string(),
                    locus: "crate::ddc::parser".to_string(),
                })?;
            records.push(val);
        }
        Self::parse_records(&records)
    }
}

// Origin: engine/crates_rs/core_wdp/src/ddc/parser.rs
// Claim: urn:core:crates_rs:core-wdp:parser:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(n.into(), d.into())
    }

    #[test]
    fn decimal_text_is_parsed_exactly() {
        assert_eq!(parse_fraction_str("0.1"), Ok(Some(q(1, 10))));
        assert_eq!(parse_fraction_str(" -2.50 "), Ok(Some(q(-5, 2))));
        assert_eq!(parse_fraction_str("+.5"), Ok(Some(q(1, 2))));
        assert_eq!(parse_fraction_str("3."), Ok(Some(q(3, 1))));
        assert_eq!(parse_fraction_str("1.5e2"), Ok(Some(q(150, 1))));
        assert_eq!(parse_fraction_str("25E-3"), Ok(Some(q(1, 40))));
        assert_eq!(parse_fraction_str("1e+3"), Ok(Some(q(1000, 1))));
    }

    #[test]
    fn rational_and_integer_text_are_parsed_exactly() {
        assert_eq!(parse_fraction_str("3/4"), Ok(Some(q(3, 4))));
        assert_eq!(parse_fraction_str("2/4"), Ok(Some(q(1, 2))));
        assert_eq!(parse_fraction_str("-6/-4"), Ok(Some(q(3, 2))));
        assert_eq!(parse_fraction_str("7"), Ok(Some(q(7, 1))));
        assert_eq!(parse_fraction_str("-0"), Ok(Some(q(0, 1))));
    }

    #[test]
    fn absent_markers_are_none() {
        assert_eq!(parse_fraction_str(""), Ok(None));
        assert_eq!(parse_fraction_str("  "), Ok(None));
        assert_eq!(parse_fraction_str("None"), Ok(None));
    }

    #[test]
    fn garbage_and_non_finite_text_is_refused() {
        for bad in [
            "NaN", "nan", "inf", "-inf", "infinity", "1/0", "abc", "1.2.3", "1e", "e5", ".", "-",
            "1/x", "0x10", "1,5", "1e99999",
        ] {
            let refusal = parse_fraction_str(bad).expect_err(bad);
            assert_eq!(refusal.code, "INVALID_RESIDUAL_TEXT", "{bad}");
        }
    }

    #[test]
    fn residual_fields_fail_closed_on_non_exact_json() {
        let mut payload = BTreeMap::new();
        payload.insert("phi_1".to_string(), serde_json::json!(0.1));
        assert_eq!(
            parse_residual_field(&payload, "phi_1").map_err(|r| r.code),
            Err("INVALID_RESIDUAL_TEXT".to_string())
        );
        payload.insert("phi_1".to_string(), serde_json::json!(true));
        assert!(parse_residual_field(&payload, "phi_1").is_err());
        payload.insert("phi_1".to_string(), serde_json::json!(3));
        assert_eq!(parse_residual_field(&payload, "phi_1"), Ok(Some(q(3, 1))));
        payload.insert("phi_1".to_string(), serde_json::Value::Null);
        assert_eq!(parse_residual_field(&payload, "phi_1"), Ok(None));
        assert_eq!(parse_residual_field(&payload, "gamma_2"), Ok(None));
        payload.insert("phi_1".to_string(), serde_json::json!("0.1"));
        assert_eq!(parse_residual_field(&payload, "phi_1"), Ok(Some(q(1, 10))));
    }

    #[test]
    fn tape_with_garbage_residual_is_refused() {
        let tape = r#"{"sequence":0,"parent_sha256":null,"payload":{"letter":"C","phi_1":"NaN"}}"#;
        let refusal = DdcTapeParser::parse_jsonl(tape).expect_err("garbage phi_1 must refuse");
        assert_eq!(refusal.code, "INVALID_RESIDUAL_TEXT");
    }

    #[test]
    fn tape_with_decimal_residual_reports_exact_fraction() {
        let tape = r#"{"sequence":0,"parent_sha256":null,"payload":{"letter":"T","phi_1":"0.1","gamma_2":"0"}}"#;
        let receipt = DdcTapeParser::parse_jsonl(tape).expect("decimal residual parses");
        assert_eq!(receipt.initial_phi1.as_deref(), Some("1/10"));
        assert_eq!(receipt.terminal_residual.as_deref(), Some("1/10"));
    }
}
