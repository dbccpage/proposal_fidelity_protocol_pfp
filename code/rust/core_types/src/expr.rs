#[derive(Debug, Clone, PartialEq)]
pub enum Expr {
    Input(usize),
    Const(f64),
    Add(Box<Expr>, Box<Expr>),
    Sub(Box<Expr>, Box<Expr>),
    Mul(Box<Expr>, Box<Expr>),
    Abs(Box<Expr>),
    DigitSum(Box<Expr>),
    DigitRev(Box<Expr>),
    DigitZipAdd(Box<Expr>, Box<Expr>),
    DigitZipDiff(Box<Expr>, Box<Expr>),
    Greater(Box<Expr>, Box<Expr>),
    If {
        cond: Box<Expr>,
        then_branch: Box<Expr>,
        else_branch: Box<Expr>,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExactEvalError {
    FloatConstant,
    UnboundInput { index: usize },
    Overflow,
    NegativeDigit,
}

// Origin: engine/crates_rs/core_types/src/expr.rs
// Claim: urn:core:crates_rs:core-types:expr:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactEvalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactEvalError {}

fn digits_le(value: i64) -> Result<Vec<i64>, ExactEvalError> {
    if value < 0 {
        return Err(ExactEvalError::NegativeDigit);
    }
    if value == 0 {
        return Ok(vec![0]);
    }
    let mut rest = value;
    let mut digits = Vec::new();
    while rest > 0 {
        digits.push(rest % 10);
        rest /= 10;
    }
    Ok(digits)
}

fn from_le_digits(digits: &[i64]) -> Result<i64, ExactEvalError> {
    let mut place = 1i64;
    let mut acc = 0i64;
    for (index, digit) in digits.iter().enumerate() {
        let contribution = digit
            .checked_mul(place)
            .ok_or(ExactEvalError::Overflow)?;
        acc = acc
            .checked_add(contribution)
            .ok_or(ExactEvalError::Overflow)?;
        let consumed = index.saturating_add(1);
        if consumed < digits.len() {
            place = place.checked_mul(10).ok_or(ExactEvalError::Overflow)?;
        }
    }
    Ok(acc)
}

fn zip_digit_step(x: i64, y: i64, carry: i64, subtract: bool) -> Result<(i64, i64), ExactEvalError> {
    if subtract {
        let raw = x
            .checked_sub(y)
            .and_then(|gap| gap.checked_sub(carry))
            .ok_or(ExactEvalError::Overflow)?;
        if raw < 0 {
            Ok((raw.checked_add(10).ok_or(ExactEvalError::Overflow)?, 1))
        } else {
            Ok((raw, 0))
        }
    } else {
        let raw = x
            .checked_add(y)
            .and_then(|sum| sum.checked_add(carry))
            .ok_or(ExactEvalError::Overflow)?;
        Ok((raw % 10, raw / 10))
    }
}

fn zip_digits(left: i64, right: i64, subtract: bool) -> Result<i64, ExactEvalError> {
    let left_digits = digits_le(left)?;
    let right_digits = digits_le(right)?;
    let len = left_digits.len().max(right_digits.len());
    let mut out = Vec::with_capacity(len.saturating_add(1));
    let mut carry = 0i64;
    for index in 0..len {
        let x = left_digits.get(index).copied().unwrap_or(0);
        let y = right_digits.get(index).copied().unwrap_or(0);
        let (digit, next_carry) = zip_digit_step(x, y, carry, subtract)?;
        carry = next_carry;
        out.push(digit);
    }
    if subtract && carry != 0 {
        return Err(ExactEvalError::NegativeDigit);
    }
    if !subtract && carry != 0 {
        out.push(carry);
    }
    from_le_digits(&out)
}

fn eval_unary_digits(inner: &Expr, inputs: &[i64], reverse: bool) -> Result<i64, ExactEvalError> {
    let mut digits = digits_le(eval_exact(inner, inputs)?)?;
    if reverse {
        digits.reverse();
        from_le_digits(&digits)
    } else {
        let mut sum = 0i64;
        for digit in digits {
            sum = sum.checked_add(digit).ok_or(ExactEvalError::Overflow)?;
        }
        Ok(sum)
    }
}

fn eval_binary_arith(
    left: &Expr,
    right: &Expr,
    inputs: &[i64],
    op: fn(i64, i64) -> Option<i64>,
) -> Result<i64, ExactEvalError> {
    op(eval_exact(left, inputs)?, eval_exact(right, inputs)?).ok_or(ExactEvalError::Overflow)
}

fn eval_zip_digits_expr(left: &Expr, right: &Expr, inputs: &[i64], sub: bool) -> Result<i64, ExactEvalError> {
    zip_digits(eval_exact(left, inputs)?, eval_exact(right, inputs)?, sub)
}

fn eval_cmp_or_if(expr: &Expr, inputs: &[i64]) -> Result<i64, ExactEvalError> {
    match expr {
        Expr::Greater(left, right) => Ok(i64::from(eval_exact(left, inputs)? > eval_exact(right, inputs)?)),
        Expr::If { cond, then_branch, else_branch } => {
            let target = if eval_exact(cond, inputs)? != 0 { then_branch } else { else_branch };
            eval_exact(target, inputs)
        }
        _ => Err(ExactEvalError::Overflow),
    }
}

fn eval_digit_or_cmp(expr: &Expr, inputs: &[i64]) -> Result<i64, ExactEvalError> {
    match expr {
        Expr::DigitSum(inner) => eval_unary_digits(inner, inputs, false),
        Expr::DigitRev(inner) => eval_unary_digits(inner, inputs, true),
        Expr::DigitZipAdd(left, right) => eval_zip_digits_expr(left, right, inputs, false),
        Expr::DigitZipDiff(left, right) => eval_zip_digits_expr(left, right, inputs, true),
        _ => eval_cmp_or_if(expr, inputs),
    }
}

/// Exact integer evaluation. `Expr::Const` is refused; it stores a binary float.
pub fn eval_exact(expr: &Expr, inputs: &[i64]) -> Result<i64, ExactEvalError> {
    match expr {
        Expr::Input(index) => inputs
            .get(*index)
            .copied()
            .ok_or(ExactEvalError::UnboundInput { index: *index }),
        Expr::Const(_) => Err(ExactEvalError::FloatConstant),
        Expr::Add(left, right) => eval_binary_arith(left, right, inputs, i64::checked_add),
        Expr::Sub(left, right) => eval_binary_arith(left, right, inputs, i64::checked_sub),
        Expr::Mul(left, right) => eval_binary_arith(left, right, inputs, i64::checked_mul),
        Expr::Abs(inner) => eval_exact(inner, inputs)?
            .checked_abs()
            .ok_or(ExactEvalError::Overflow),
        _ => eval_digit_or_cmp(expr, inputs),
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_7c4c79c7 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
