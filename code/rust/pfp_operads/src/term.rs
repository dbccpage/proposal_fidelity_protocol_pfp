//! Typed operations, trees of them, substitution and exact evaluation.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:term:v1

use std::slice::Iter;

use serde::{Deserialize, Serialize};

use crate::{canon_values, Refusal};

/// The canon types whose values may colour an operation's ports.
pub const COLOUR_TYPES: [&str; 3] = ["operad_colour", "prompt_colour", "task_value_colour"];

/// One colour: a value of one of the canon's colour types.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
pub struct Colour {
    colour_type: &'static str,
    name: &'static str,
}

impl Colour {
    /// Refuses a colour type or a colour name the canon does not list.
    pub fn new(colour_type: &str, name: &str) -> Result<Self, Refusal> {
        let colour_type = COLOUR_TYPES
            .iter()
            .find(|known| **known == colour_type)
            .ok_or_else(|| {
                Refusal::new(
                    "UNKNOWN_COLOUR_TYPE",
                    format!("{colour_type} is not a colour type"),
                )
            })?;
        let name = canon_values(colour_type)?
            .iter()
            .find(|known| **known == name)
            .ok_or_else(|| {
                Refusal::new(
                    "UNKNOWN_COLOUR",
                    format!("{name} is not a value of {colour_type}"),
                )
            })?;
        Ok(Self { colour_type, name })
    }

    pub fn name(&self) -> &'static str {
        self.name
    }
}

/// An exact value: an integer or a list of values.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Value {
    Int(i64),
    List(Vec<Value>),
}

/// The closed set of executable bodies. `Opaque` is a signature with no body.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Body {
    Identity,
    Sum,
    Product,
    Difference,
    Pack,
    SumList,
    Opaque,
}

fn integers(args: &[Value]) -> Result<Vec<i64>, Refusal> {
    args.iter()
        .map(|arg| match arg {
            Value::Int(n) => Ok(*n),
            Value::List(_) => Err(Refusal::new(
                "VALUE_SHAPE",
                "expected an integer, got a list",
            )),
        })
        .collect()
}

fn overflow() -> Refusal {
    Refusal::new("OVERFLOW", "the exact result does not fit in 64 bits")
}

fn fold(numbers: &[i64], start: i64, step: fn(i64, i64) -> Option<i64>) -> Result<Value, Refusal> {
    numbers
        .iter()
        .try_fold(start, |total, n| step(total, *n))
        .map(Value::Int)
        .ok_or_else(overflow)
}

impl Body {
    /// The number of inputs the body needs, when it is fixed.
    pub fn fixed_arity(self) -> Option<usize> {
        match self {
            Body::Identity | Body::SumList => Some(1),
            Body::Difference => Some(2),
            Body::Sum | Body::Product | Body::Pack | Body::Opaque => None,
        }
    }

    /// Apply the body to already evaluated arguments.
    pub fn apply(self, args: &[Value]) -> Result<Value, Refusal> {
        match (self, args) {
            (Body::Identity, [only]) => Ok(only.clone()),
            (Body::Sum, _) => fold(&integers(args)?, 0, i64::checked_add),
            (Body::Product, _) => fold(&integers(args)?, 1, i64::checked_mul),
            (Body::Difference, [Value::Int(left), Value::Int(right)]) => left
                .checked_sub(*right)
                .map(Value::Int)
                .ok_or_else(overflow),
            (Body::Difference, [_, _]) => Err(Refusal::new("VALUE_SHAPE", "expected two integers")),
            (Body::Pack, _) => Ok(Value::List(args.to_vec())),
            (Body::SumList, [Value::List(items)]) => fold(&integers(items)?, 0, i64::checked_add),
            (Body::SumList, [Value::Int(_)]) => Err(Refusal::new(
                "VALUE_SHAPE",
                "expected a list, got an integer",
            )),
            (Body::Opaque, _) => Err(Refusal::new("NO_BODY", "the operation has no body to run")),
            _ => Err(Refusal::new(
                "ARITY",
                "wrong number of arguments for the body",
            )),
        }
    }
}

/// Whether the order of an operation's inputs matters. The names are the canon's `operad_variant`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Variant {
    Planar,
    Symmetric,
}

/// One operation: ordered source colours, a target colour, a body, a variant and an exact cost.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize)]
pub struct Operation {
    name: String,
    sources: Vec<Colour>,
    target: Colour,
    body: Body,
    variant: Variant,
    cost: u64,
}

impl Operation {
    pub fn new(
        name: &str,
        sources: Vec<Colour>,
        target: Colour,
        body: Body,
        variant: Variant,
        cost: u64,
    ) -> Result<Self, Refusal> {
        if name.trim().is_empty() {
            return Err(Refusal::new("BAD_NAME", "an operation needs a name"));
        }
        if body
            .fixed_arity()
            .is_some_and(|arity| arity != sources.len())
        {
            return Err(Refusal::new(
                "ARITY",
                format!("{name}: the body does not take {} inputs", sources.len()),
            ));
        }
        if body == Body::Identity && sources.first() != Some(&target) {
            return Err(Refusal::new(
                "COLOUR_MISMATCH",
                format!("{name}: an identity keeps its colour"),
            ));
        }
        Ok(Self {
            name: name.to_owned(),
            sources,
            target,
            body,
            variant,
            cost,
        })
    }

    /// The unit of a colour: one input, the same output, no cost.
    pub fn identity(colour: &Colour) -> Self {
        Self {
            name: format!("id_{}", colour.name),
            sources: vec![colour.clone()],
            target: colour.clone(),
            body: Body::Identity,
            variant: Variant::Planar,
            cost: 0,
        }
    }

    pub fn name(&self) -> &str {
        &self.name
    }
    pub fn sources(&self) -> &[Colour] {
        &self.sources
    }
    pub fn target(&self) -> &Colour {
        &self.target
    }
    pub fn body(&self) -> Body {
        self.body
    }
    pub fn variant(&self) -> Variant {
        self.variant
    }
}

/// A tree of operations. Its open leaves, left to right, are its inputs.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Term {
    Leaf(Colour),
    Node(Operation, Vec<Term>),
}

impl Term {
    /// One operation with every input open.
    pub fn corolla(operation: &Operation) -> Self {
        let leaves = operation.sources.iter().cloned().map(Term::Leaf).collect();
        Term::Node(operation.clone(), leaves)
    }

    pub fn target(&self) -> &Colour {
        match self {
            Term::Leaf(colour) => colour,
            Term::Node(operation, _) => &operation.target,
        }
    }

    /// The colours of the open inputs, left to right.
    pub fn leaves(&self) -> Vec<&Colour> {
        match self {
            Term::Leaf(colour) => vec![colour],
            Term::Node(_, children) => children.iter().flat_map(Term::leaves).collect(),
        }
    }

    /// Partial composition: plug `inner` into open input `slot` (counted from 0).
    pub fn substitute(&self, slot: usize, inner: &Term) -> Result<Term, Refusal> {
        let mut remaining = Some(slot);
        let grafted = self.graft(&mut remaining, inner)?;
        match remaining {
            None => Ok(grafted),
            Some(_) => Err(Refusal::new(
                "SLOT_OUT_OF_RANGE",
                format!("there is no open input {slot}"),
            )),
        }
    }

    fn graft(&self, remaining: &mut Option<usize>, inner: &Term) -> Result<Term, Refusal> {
        match (self, *remaining) {
            (Term::Leaf(colour), Some(0)) => {
                *remaining = None;
                if inner.target() == colour {
                    Ok(inner.clone())
                } else {
                    Err(Refusal::new(
                        "COLOUR_MISMATCH",
                        format!("input wants {}, got {}", colour.name, inner.target().name),
                    ))
                }
            }
            (Term::Leaf(_), Some(left)) => {
                *remaining = Some(left - 1);
                Ok(self.clone())
            }
            (Term::Leaf(_), None) => Ok(self.clone()),
            (Term::Node(operation, children), _) => {
                let children: Result<Vec<Term>, Refusal> = children
                    .iter()
                    .map(|child| child.graft(remaining, inner))
                    .collect();
                Ok(Term::Node(operation.clone(), children?))
            }
        }
    }

    /// The exact cost of running the whole tree once.
    pub fn cost(&self) -> Result<u64, Refusal> {
        match self {
            Term::Leaf(_) => Ok(0),
            Term::Node(operation, children) => children
                .iter()
                .try_fold(operation.cost, |total, child| {
                    total.checked_add(child.cost().ok()?)
                })
                .ok_or_else(|| Refusal::new("OVERFLOW", "the total cost does not fit in 64 bits")),
        }
    }

    /// Run the tree on one value per open input, left to right.
    pub fn eval(&self, inputs: &[Value]) -> Result<Value, Refusal> {
        let mut rest = inputs.iter();
        let value = self.run(&mut rest)?;
        match rest.next() {
            None => Ok(value),
            Some(_) => Err(Refusal::new("ARITY", "more inputs than open leaves")),
        }
    }

    fn run(&self, inputs: &mut Iter<'_, Value>) -> Result<Value, Refusal> {
        match self {
            Term::Leaf(_) => inputs
                .next()
                .cloned()
                .ok_or_else(|| Refusal::new("ARITY", "fewer inputs than open leaves")),
            Term::Node(operation, children) => {
                let args: Result<Vec<Value>, Refusal> =
                    children.iter().map(|child| child.run(inputs)).collect();
                operation.body.apply(&args?)
            }
        }
    }

    /// The same tree with every identity node removed.
    pub fn normalise(&self) -> Term {
        match self {
            Term::Leaf(_) => self.clone(),
            Term::Node(operation, children) => match (operation.body, children.as_slice()) {
                (Body::Identity, [only]) => only.normalise(),
                _ => Term::Node(
                    operation.clone(),
                    children.iter().map(Term::normalise).collect(),
                ),
            },
        }
    }
}
