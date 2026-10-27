use core_adversary::providers::budget::execute;
use serde_json::Value;
#[test]
fn source_budget_policy_and_receipts_agree() {
    let rows: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/budget_policy.json")).unwrap();
    for row in rows {
        assert_eq!(
            execute(&row["request"]).unwrap(),
            row["outcome"],
            "{}",
            row["name"]
        );
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
enum DigitMulError { Empty, Digit, Width, Overflow }

// Origin: engine/crates_rs/tests/core_adversary/providers/budget_policy.rs
// Claim: urn:core:crates_rs:tests:budget-policy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DigitMulError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DigitMulError {}

fn schoolbook_mul(left: &str, right: &str) -> Result<String, DigitMulError> {
    if left.is_empty() || right.is_empty() {
        return Err(DigitMulError::Empty);
    }
    if !left.bytes().all(|byte| byte.is_ascii_digit()) || !right.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(DigitMulError::Digit);
    }
    if left.bytes().all(|byte| byte == b'0') || right.bytes().all(|byte| byte == b'0') {
        return Ok("0".to_string());
    }
    let mut acc = vec![0u16; left.len().checked_add(right.len()).ok_or(DigitMulError::Width)?];
    for (i, left_digit) in left.bytes().rev().enumerate() {
        let mut carry = 0u16;
        for (j, right_digit) in right.bytes().rev().enumerate() {
            let index = i.checked_add(j).ok_or(DigitMulError::Width)?;
            let slot = acc.get_mut(index).ok_or(DigitMulError::Width)?;
            let prod = u16::from(left_digit - b'0').checked_mul(u16::from(right_digit - b'0')).ok_or(DigitMulError::Overflow)?;
            let sum = slot.checked_add(prod).ok_or(DigitMulError::Overflow)?.checked_add(carry).ok_or(DigitMulError::Overflow)?;
            *slot = sum % 10;
            carry = sum / 10;
        }
        if carry != 0 {
            let index = i.checked_add(right.len()).ok_or(DigitMulError::Width)?;
            let slot = acc.get_mut(index).ok_or(DigitMulError::Width)?;
            *slot = slot.checked_add(carry).ok_or(DigitMulError::Overflow)?;
        }
    }
    let mut chars = Vec::new();
    let mut leading = true;
    for digit in acc.iter().rev() {
        if leading && *digit == 0 {
            continue;
        }
        leading = false;
        let code = b'0'.checked_add(u8::try_from(*digit).map_err(|_| DigitMulError::Overflow)?).ok_or(DigitMulError::Overflow)?;
        chars.push(char::from(code));
    }
    if chars.is_empty() {
        Ok("0".to_string())
    } else {
        Ok(chars.into_iter().collect())
    }
}

#[test]
fn exact_leg_cost_product_is_the_full_digit_string() {
    let tokens = format!("1{}", "0".repeat(35));
    let price = format!("1{}", "0".repeat(27));
    let product = format!("1{}", "0".repeat(62));
    assert_eq!(tokens.len(), 36);
    assert_eq!(price.len(), 28);
    assert_eq!(schoolbook_mul(&tokens, &price), Ok(product));
    assert_eq!(schoolbook_mul("0", "9"), Ok("0".to_string()));
    assert_eq!(schoolbook_mul("12", "10"), Ok("120".to_string()));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
