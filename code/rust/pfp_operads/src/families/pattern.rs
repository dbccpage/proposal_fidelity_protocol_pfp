//! The detector-pattern dialect: which patterns a rule may use, and how one is matched.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-pattern:v1
//!
//! A detector rule carries a regular expression written in the syntax of Python's `re`, run
//! case-insensitively. This module reads that syntax itself, applies the admission rule of the
//! bounded subset, and matches with the `regex` crate on a pattern it writes from what it read,
//! so the matcher never sees the author's text.
//!
//! The admission rule, as the Python parser applies it to the parsed tree:
//!
//! 1. the pattern has one to [`MAX_LENGTH`] characters and parses;
//! 2. it has no backreference;
//! 3. no repeat stands inside another repeat, and no alternation stands inside a repeat;
//! 4. every repeat is bounded and no upper bound exceeds [`MAX_BOUND`]: `*`, `+` and `{m,}` are
//!    refused;
//! 5. the product, over every repeat `{m,n}` of `n - m + 1` and over every alternation of its
//!    number of branches, is at most [`MAX_PRODUCT`];
//! 6. the pattern cannot match the empty string.
//!
//! The tree is the one Python builds: a common prefix of the branches of an alternation is moved
//! in front of it, and an alternation whose branches are single characters or sets is one set.
//!
//! What is refused ([`Rejected::Refused`]) is a pattern the Python parser refuses or the rule
//! above excludes. What the host does not read ([`Rejected::Unread`]) is syntax Python accepts
//! that this module has no reading for: anchors and word boundaries, groups other than `(...)`
//! and `(?:...)`, possessive repeats, octal and named escapes, and repeat counts beyond the
//! range of the Python engine. A caller stops the run on those instead of guessing. A pattern
//! whose compiled form exceeds 16 MiB is refused.
//!
//! The classes `\w` and `\s` follow the `regex` crate's Unicode tables, which differ from
//! Python's at a few code points (Python's `\s` also takes the four separators U+001C to
//! U+001F). Digits in a count are ASCII, as in Python.

use regex::{Regex, RegexBuilder};

/// The longest pattern, in characters.
pub const MAX_LENGTH: usize = 256;
/// The largest upper bound of a repeat.
pub const MAX_BOUND: u64 = 64;
/// The largest product of repeat widths and branch counts.
pub const MAX_PRODUCT: u64 = 256;
/// The Python engine's repeat count limit: a count at or above it is an overflow there.
const ENGINE_LIMIT: u64 = 4_294_967_295;
/// The size the matcher may compile a pattern to, in bytes.
const SIZE_LIMIT: usize = 16 << 20;

/// Why a pattern is not compiled.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Rejected {
    /// The pattern is invalid or outside the admitted subset. The code names the rule.
    Refused(&'static str),
    /// The pattern uses syntax the host does not read. The text names it.
    Unread(&'static str),
}

/// Python's `str.isspace`: the Unicode white space and the four separators U+001C to U+001F.
pub fn is_space(point: char) -> bool {
    point.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&point)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Category {
    Digit,
    NotDigit,
    Space,
    NotSpace,
    Word,
    NotWord,
}

impl Category {
    fn read(letter: char) -> Option<Category> {
        Some(match letter {
            'd' => Category::Digit,
            'D' => Category::NotDigit,
            's' => Category::Space,
            'S' => Category::NotSpace,
            'w' => Category::Word,
            'W' => Category::NotWord,
            _ => return None,
        })
    }

    fn written(self) -> &'static str {
        match self {
            Category::Digit => "\\d",
            Category::NotDigit => "\\D",
            Category::Space => "\\s",
            Category::NotSpace => "\\S",
            Category::Word => "\\w",
            Category::NotWord => "\\W",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Item {
    Point(char),
    Range(char, char),
    Class(Category),
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum Node {
    Point(char),
    Any,
    NotPoint(char),
    Set { negated: bool, items: Vec<Item> },
    Group(Vec<Node>),
    Repeat(Repeat),
    Branch(Vec<Vec<Node>>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct Repeat {
    low: u64,
    /// `None` is unbounded.
    high: Option<u64>,
    lazy: bool,
    body: Vec<Node>,
}

/// Whether two nodes are the same node for moving a common prefix out of an alternation. Python
/// compares tuples, and a group or a repeat holds a sub-pattern object that only equals itself.
fn same(left: &Node, right: &Node) -> bool {
    match (left, right) {
        (Node::Group(_) | Node::Repeat(_) | Node::Branch(_), _) => false,
        _ => left == right,
    }
}

/// Python's `_parse_sub` on the branches it has read: the shared prefix first, then the set or
/// the alternation of what is left.
fn assemble(mut branches: Vec<Vec<Node>>) -> Vec<Node> {
    if branches.len() == 1 {
        return branches.swap_remove(0);
    }
    let mut out = Vec::new();
    while branches[0].first().is_some_and(|head| {
        branches
            .iter()
            .all(|one| one.first().is_some_and(|n| same(head, n)))
    }) {
        out.push(branches[0][0].clone());
        for one in &mut branches {
            one.remove(0);
        }
    }
    let mut items: Vec<Item> = Vec::new();
    let single = branches.iter().all(|one| match one.as_slice() {
        [Node::Point(point)] => {
            items.push(Item::Point(*point));
            true
        }
        [Node::Set {
            negated: false,
            items: inner,
        }] => {
            items.extend(inner.iter().copied());
            true
        }
        _ => false,
    });
    if single {
        out.push(Node::Set {
            negated: false,
            items: unique(items),
        });
    } else {
        out.push(Node::Branch(branches));
    }
    out
}

fn unique(items: Vec<Item>) -> Vec<Item> {
    let mut kept: Vec<Item> = Vec::new();
    for item in items {
        if !kept.contains(&item) {
            kept.push(item);
        }
    }
    kept
}

enum Atom {
    Point(char),
    Class(Category),
}

struct Parser {
    chars: Vec<char>,
    at: usize,
}

type Read<T> = Result<T, Rejected>;

fn refused<T>(code: &'static str) -> Read<T> {
    Err(Rejected::Refused(code))
}

fn unread<T>(what: &'static str) -> Read<T> {
    Err(Rejected::Unread(what))
}

impl Parser {
    fn peek(&self) -> Option<char> {
        self.chars.get(self.at).copied()
    }

    fn take(&mut self) -> Option<char> {
        let next = self.peek();
        if next.is_some() {
            self.at += 1;
        }
        next
    }

    fn eat(&mut self, expected: char) -> bool {
        let found = self.peek() == Some(expected);
        if found {
            self.at += 1;
        }
        found
    }

    /// Alternatives up to the end of the pattern, or up to the `)` of a group when `nested`.
    fn alternatives(&mut self, nested: bool) -> Read<Vec<Node>> {
        let mut branches = vec![self.sequence(nested)?];
        while self.eat('|') {
            branches.push(self.sequence(nested)?);
        }
        Ok(assemble(branches))
    }

    fn sequence(&mut self, nested: bool) -> Read<Vec<Node>> {
        let mut nodes: Vec<Node> = Vec::new();
        while let Some(this) = self.peek() {
            if this == '|' {
                break;
            }
            if this == ')' {
                if nested {
                    break;
                }
                return refused("PATTERN_SYNTAX");
            }
            self.at += 1;
            match this {
                '[' => nodes.push(self.set()?),
                '.' => nodes.push(Node::Any),
                '(' => nodes.push(self.group()?),
                '^' | '$' => return unread("an anchor"),
                '\\' => nodes.push(self.escape()?),
                '*' => repeat(self, &mut nodes, 0, None)?,
                '+' => repeat(self, &mut nodes, 1, None)?,
                '?' => repeat(self, &mut nodes, 0, Some(1))?,
                '{' => self.braces(&mut nodes)?,
                other => nodes.push(Node::Point(other)),
            }
        }
        Ok(nodes)
    }

    fn group(&mut self) -> Read<Node> {
        if self.eat('?') && !self.eat(':') {
            return unread("a group other than (...) and (?:...)");
        }
        let inner = self.alternatives(true)?;
        if !self.eat(')') {
            return refused("PATTERN_SYNTAX");
        }
        Ok(Node::Group(inner))
    }

    fn digits(&mut self) -> String {
        let mut text = String::new();
        while let Some(digit) = self.peek().filter(char::is_ascii_digit) {
            text.push(digit);
            self.at += 1;
        }
        text
    }

    /// `{`: a counted repeat when it reads as one, else the character itself.
    fn braces(&mut self, nodes: &mut Vec<Node>) -> Read<()> {
        if self.peek() == Some('}') {
            nodes.push(Node::Point('{'));
            return Ok(());
        }
        let start = self.at;
        let low = self.digits();
        let high = if self.eat(',') {
            self.digits()
        } else {
            low.clone()
        };
        if !self.eat('}') {
            self.at = start;
            nodes.push(Node::Point('{'));
            return Ok(());
        }
        let count = |text: &str| -> Read<Option<u64>> {
            if text.is_empty() {
                return Ok(None);
            }
            match text.parse::<u64>() {
                Ok(number) if number < ENGINE_LIMIT => Ok(Some(number)),
                _ => unread("a repeat count beyond the engine's range"),
            }
        };
        let (low, high) = (count(&low)?.unwrap_or(0), count(&high)?);
        if high.is_some_and(|high| high < low) {
            return refused("PATTERN_SYNTAX");
        }
        repeat(self, nodes, low, high)
    }

    fn escape(&mut self) -> Read<Node> {
        let Some(letter) = self.take() else {
            return refused("PATTERN_SYNTAX");
        };
        if let Some(class) = Category::read(letter) {
            return Ok(Node::Set {
                negated: false,
                items: vec![Item::Class(class)],
            });
        }
        match letter {
            'A' | 'Z' | 'b' | 'B' => unread("an anchor or a word boundary"),
            '0' => unread("an octal escape"),
            '1'..='9' => {
                let octal = |point: Option<char>| point.is_some_and(|p| ('0'..='7').contains(&p));
                let more = |at: usize| self.chars.get(self.at + at).copied();
                if ('1'..='7').contains(&letter) && octal(more(0)) && octal(more(1)) {
                    unread("an octal escape")
                } else {
                    refused("PATTERN_BACKREFERENCE")
                }
            }
            other => self.point(other, false).map(|atom| match atom {
                Atom::Point(point) => Node::Point(point),
                Atom::Class(class) => Node::Set {
                    negated: false,
                    items: vec![Item::Class(class)],
                },
            }),
        }
    }

    /// The character an escape other than a class or an anchor stands for.
    fn point(&mut self, letter: char, in_set: bool) -> Read<Atom> {
        let point = match letter {
            'a' => '\u{7}',
            'f' => '\u{c}',
            'n' => '\n',
            'r' => '\r',
            't' => '\t',
            'v' => '\u{b}',
            '\\' => '\\',
            'b' if in_set => '\u{8}',
            'x' => self.hex(2)?,
            'u' => self.hex(4)?,
            'U' => self.hex(8)?,
            'N' => return unread("a named escape"),
            '0'..='7' if in_set => return unread("an octal escape"),
            '8' | '9' if in_set => return refused("PATTERN_SYNTAX"),
            other if other.is_ascii_alphabetic() => return refused("PATTERN_SYNTAX"),
            other => other,
        };
        Ok(Atom::Point(point))
    }

    fn hex(&mut self, width: usize) -> Read<char> {
        let digits: String = self.chars[self.at..].iter().take(width).collect();
        if digits.len() != width || !digits.chars().all(|d| d.is_ascii_hexdigit()) {
            return refused("PATTERN_SYNTAX");
        }
        self.at += width;
        match u32::from_str_radix(&digits, 16) {
            Ok(value) if value > 0x10_ffff => refused("PATTERN_SYNTAX"),
            Ok(value) => char::from_u32(value).map_or_else(|| unread("a surrogate escape"), Ok),
            Err(_) => refused("PATTERN_SYNTAX"),
        }
    }

    fn set_atom(&mut self, this: char) -> Read<Atom> {
        if this != '\\' {
            return Ok(Atom::Point(this));
        }
        let Some(letter) = self.take() else {
            return refused("PATTERN_SYNTAX");
        };
        match Category::read(letter) {
            Some(class) => Ok(Atom::Class(class)),
            None => self.point(letter, true),
        }
    }

    /// `[`: a set, as Python reads it. A `]` first in the set is a character, and a `-` that
    /// begins or ends the set is one too.
    fn set(&mut self) -> Read<Node> {
        let negated = self.eat('^');
        let mut items: Vec<Item> = Vec::new();
        let mut first = true;
        loop {
            let Some(this) = self.take() else {
                return refused("PATTERN_SYNTAX");
            };
            if this == ']' && !first {
                break;
            }
            first = false;
            let low = self.set_atom(this)?;
            if !self.eat('-') {
                items.push(item(low));
                continue;
            }
            let Some(that) = self.take() else {
                return refused("PATTERN_SYNTAX");
            };
            if that == ']' {
                items.push(item(low));
                items.push(Item::Point('-'));
                break;
            }
            match (low, self.set_atom(that)?) {
                (Atom::Point(low), Atom::Point(high)) if low <= high => {
                    items.push(Item::Range(low, high));
                }
                _ => return refused("PATTERN_SYNTAX"),
            }
        }
        let items = unique(items);
        Ok(match items.as_slice() {
            [Item::Point(point)] if negated => Node::NotPoint(*point),
            [Item::Point(point)] => Node::Point(*point),
            _ => Node::Set { negated, items },
        })
    }
}

fn item(atom: Atom) -> Item {
    match atom {
        Atom::Point(point) => Item::Point(point),
        Atom::Class(class) => Item::Class(class),
    }
}

/// Apply a repeat to the last node read, then read its lazy mark.
fn repeat(parser: &mut Parser, nodes: &mut Vec<Node>, low: u64, high: Option<u64>) -> Read<()> {
    let body = match nodes.pop() {
        None | Some(Node::Repeat(_)) => return refused("PATTERN_SYNTAX"),
        Some(Node::Group(inner)) => inner,
        Some(other) => vec![other],
    };
    let lazy = parser.eat('?');
    if !lazy && parser.peek() == Some('+') {
        return unread("a possessive repeat");
    }
    nodes.push(Node::Repeat(Repeat {
        low,
        high,
        lazy,
        body,
    }));
    Ok(())
}

fn multiply(product: &mut u64, factor: u64) -> Read<()> {
    *product *= factor;
    if *product > MAX_PRODUCT {
        return refused("PATTERN_CHOICE_PRODUCT");
    }
    Ok(())
}

/// Rules 2 to 5 over the tree. `inside` says a repeat holds this node.
fn admit(nodes: &[Node], inside: bool, product: &mut u64) -> Read<()> {
    for node in nodes {
        match node {
            Node::Repeat(one) => {
                if inside {
                    return refused("PATTERN_NESTED_QUANTIFIER");
                }
                admit(&one.body, true, product)?;
                let Some(high) = one.high else {
                    return refused("PATTERN_UNBOUNDED_REPEAT");
                };
                if high > MAX_BOUND {
                    return refused("PATTERN_REPEAT_BOUND");
                }
                multiply(product, high - one.low + 1)?;
            }
            Node::Branch(branches) => {
                if inside {
                    return refused("PATTERN_QUANTIFIED_ALTERNATION");
                }
                multiply(product, branches.len() as u64)?;
                for branch in branches {
                    admit(branch, inside, product)?;
                }
            }
            Node::Group(inner) => admit(inner, inside, product)?,
            Node::Point(_) | Node::Any | Node::NotPoint(_) | Node::Set { .. } => {}
        }
    }
    Ok(())
}

/// The fewest characters the nodes can match.
fn narrowest(nodes: &[Node]) -> u64 {
    nodes
        .iter()
        .map(|node| match node {
            Node::Point(_) | Node::Any | Node::NotPoint(_) | Node::Set { .. } => 1,
            Node::Group(inner) => narrowest(inner),
            Node::Repeat(one) => one.low.saturating_mul(narrowest(&one.body)),
            Node::Branch(branches) => branches.iter().map(|b| narrowest(b)).min().unwrap_or(0),
        })
        .fold(0, u64::saturating_add)
}

fn written_point(point: char) -> String {
    format!("\\x{{{:X}}}", u32::from(point))
}

fn written_item(one: &Item, out: &mut String) {
    match one {
        Item::Point(point) => out.push_str(&written_point(*point)),
        Item::Range(low, high) => {
            out.push_str(&written_point(*low));
            out.push('-');
            out.push_str(&written_point(*high));
        }
        Item::Class(class) => out.push_str(class.written()),
    }
}

fn write_nodes(nodes: &[Node], out: &mut String) {
    for node in nodes {
        match node {
            Node::Point(point) => out.push_str(&written_point(*point)),
            Node::Any => out.push('.'),
            Node::NotPoint(point) => {
                out.push_str("[^");
                out.push_str(&written_point(*point));
                out.push(']');
            }
            Node::Set { negated, items } => {
                out.push('[');
                if *negated {
                    out.push('^');
                }
                items.iter().for_each(|one| written_item(one, out));
                out.push(']');
            }
            Node::Group(inner) => {
                out.push_str("(?:");
                write_nodes(inner, out);
                out.push(')');
            }
            Node::Repeat(one) => {
                out.push_str("(?:");
                write_nodes(&one.body, out);
                out.push(')');
                out.push_str(&match one.high {
                    Some(high) => format!("{{{},{}}}", one.low, high),
                    None => format!("{{{},}}", one.low),
                });
                if one.lazy {
                    out.push('?');
                }
            }
            Node::Branch(branches) => {
                out.push_str("(?:");
                for (place, branch) in branches.iter().enumerate() {
                    if place > 0 {
                        out.push('|');
                    }
                    write_nodes(branch, out);
                }
                out.push(')');
            }
        }
    }
}

/// An admitted pattern, ready to match.
#[derive(Debug, Clone)]
pub struct Pattern {
    matcher: Regex,
}

/// Where a pattern matched: the character offset and the text.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Hit {
    pub start: usize,
    pub text: String,
}

impl Pattern {
    /// The leftmost match in `text`, the preferred one among those that start there.
    pub fn find(&self, text: &str) -> Option<Hit> {
        let found = self.matcher.find(text)?;
        Some(Hit {
            start: text[..found.start()].chars().count(),
            text: found.as_str().to_owned(),
        })
    }
}

/// Read, admit and compile a detector pattern.
pub fn compile(pattern: &str) -> Result<Pattern, Rejected> {
    if pattern.chars().all(is_space) {
        return refused("PATTERN_EMPTY");
    }
    if pattern.chars().count() > MAX_LENGTH {
        return refused("PATTERN_TOO_LONG");
    }
    let mut parser = Parser {
        chars: pattern.chars().collect(),
        at: 0,
    };
    let tree = parser.alternatives(false)?;
    admit(&tree, false, &mut 1)?;
    if narrowest(&tree) < 1 {
        return refused("PATTERN_ZERO_WIDTH");
    }
    let mut written = String::new();
    write_nodes(&tree, &mut written);
    RegexBuilder::new(&written)
        .case_insensitive(true)
        .size_limit(SIZE_LIMIT)
        .build()
        .map(|matcher| Pattern { matcher })
        .or_else(|_| refused("PATTERN_COMPILE_LIMIT"))
}
