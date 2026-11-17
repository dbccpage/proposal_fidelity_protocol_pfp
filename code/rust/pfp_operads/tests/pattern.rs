//! The detector-pattern dialect: what a rule's pattern may say, what the host refuses, what it
//! does not read, and where the matcher finds a match.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-pattern-tests:v1
//!
//! The tables were written from Python's own parser and matcher: each `MATCHES` row is the
//! match `re.search` gives with `re.IGNORECASE`, and each `REFUSED` row the code
//! `compile_safe_pattern` gives.

use pfp_operads::families::pattern::{
    compile, is_space, Rejected, MAX_BOUND, MAX_LENGTH, MAX_PRODUCT,
};

/// Where a pattern should match: the character offset and the matched text.
type Match = Option<(usize, &'static str)>;

const MATCHES: &[(&str, &str, Match)] = &[
    ("abc", "xxABCxx", Some((2, "ABC"))),
    ("abc", "abcabc", Some((0, "abc"))),
    ("a", "\u{e9}\u{20ac}a", Some((2, "a"))),
    ("\u{e9}", "x\u{c9}", Some((1, "\u{c9}"))),
    ("a.c", "a\nc a-c", Some((4, "a-c"))),
    ("a.c", "a\nc", None),
    ("/1\"", "{\"c\": [1, \"5/1\"]}", Some((12, "/1\""))),
    ("\\[2,", "[1] [2, 3]", Some((4, "[2,"))),
    ("\\{'", "x {'a'", Some((2, "{'"))),
    ("-6, 8", "[1, -6, 8]", Some((4, "-6, 8"))),
    ("[ab]{1,3}", "xabab", Some((1, "aba"))),
    ("[ab]{2}", "cabab", Some((1, "ab"))),
    ("[^a]", "aab", Some((2, "b"))),
    ("[a-c]{2}", "zzcbz", Some((2, "cb"))),
    ("[\\d]{2}", "a12b", Some((1, "12"))),
    ("[]a]{2}", "x]a", Some((1, "]a"))),
    ("[a-]{2}", "x-a", Some((1, "-a"))),
    ("[[]", "a[b", Some((1, "["))),
    ("[a&&b]", "&", Some((0, "&"))),
    ("[a-]{2}", "a-", Some((0, "a-"))),
    ("[\\w.]{3}", "!a.b!", Some((1, "a.b"))),
    ("[\\D]{2}", "12ab", Some((2, "ab"))),
    ("[^\\d]{2}", "12ab34", Some((2, "ab"))),
    ("[\\x41-\\x43]{2}", "xBCx", Some((1, "BC"))),
    ("[\\n]", "a\nb", Some((1, "\n"))),
    ("[\\b]", "a\u{8}b", Some((1, "\u{8}"))),
    ("[A-Z]{3}", "abc", Some((0, "abc"))),
    ("[a-a]", "bab", Some((1, "a"))),
    ("[^]a]", "]ab", Some((2, "b"))),
    ("[a-c-e]", "d-", Some((1, "-"))),
    ("\\x41", "bA", Some((1, "A"))),
    ("\\u00e9", "\u{c9}", Some((0, "\u{c9}"))),
    ("\\U0001F600", "a\u{1f600}", Some((1, "\u{1f600}"))),
    ("\\n", "a\nb", Some((1, "\n"))),
    ("\\t\\r", "a\t\rb", Some((1, "\t\r"))),
    ("\\.", "a.b", Some((1, "."))),
    ("\\$", "$", Some((0, "$"))),
    ("\\d{2}", "a1b23", Some((3, "23"))),
    ("\\D{2}", "12ab", Some((2, "ab"))),
    ("\\w{2}", " a_ ", Some((1, "a_"))),
    ("\\W", "ab !", Some((2, " "))),
    ("\\s{2}", "a  b", Some((1, "  "))),
    ("\\S{2}", "  ab", Some((2, "ab"))),
    ("\\ ", "a b", Some((1, " "))),
    ("\\\u{e9}", "\u{e9}", Some((0, "\u{e9}"))),
    ("\\a", "x\u{7}", Some((1, "\u{7}"))),
    ("\\f\\v", "\u{c}\u{b}", Some((0, "\u{c}\u{b}"))),
    ("(ab)", "xab", Some((1, "ab"))),
    ("(?:ab)", "xab", Some((1, "ab"))),
    ("(?:ab){2}", "ababab", Some((0, "abab"))),
    ("(ab){1,2}", "ababab", Some((0, "abab"))),
    ("((a))", "a", Some((0, "a"))),
    ("(a|b)c", "xbc", Some((1, "bc"))),
    ("ab|ac", "xac", Some((1, "ac"))),
    ("a|b|c", "xc", Some((1, "c"))),
    ("a|ab", "ab", Some((0, "a"))),
    ("ab|abc", "abc", Some((0, "ab"))),
    ("(a|ab)c", "abc", Some((0, "abc"))),
    ("[a-c]|d", "xd", Some((1, "d"))),
    ("[^a]|b", "b", Some((0, "b"))),
    ("(ab|ac){1,2}", "abacx", Some((0, "abac"))),
    ("x(a|b)y|z", "z", Some((0, "z"))),
    ("ab|cd|ef", "zef", Some((1, "ef"))),
    ("(?:a|b)(?:c|d)", "xbd", Some((1, "bd"))),
    ("a|b|\\d", "3", Some((0, "3"))),
    ("a(b|)c", "ac", Some((0, "ac"))),
    ("(|a)b", "ab", Some((0, "ab"))),
    ("ab|ac|ad", "ad", Some((0, "ad"))),
    ("a?b", "ab", Some((0, "ab"))),
    ("a{2}", "aaaa", Some((0, "aa"))),
    ("a{1,3}", "aaaa", Some((0, "aaa"))),
    ("a{,2}b", "aaab", Some((1, "aab"))),
    ("a{1,3}?", "aaaa", Some((0, "a"))),
    ("a{2,3}?b", "aaab", Some((0, "aaab"))),
    ("a??b", "ab", Some((0, "ab"))),
    ("(?:ab){0,2}c", "ababc", Some((0, "ababc"))),
    ("a{0}b", "ab", Some((1, "b"))),
    ("a{3}", "aa", None),
    (
        "x{1,64}",
        "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        Some((
            0,
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        )),
    ),
    ("a{ 1}", "a{ 1}", Some((0, "a{ 1}"))),
    ("a{", "a{", Some((0, "a{"))),
    ("{a}", "{a}", Some((0, "{a}"))),
    ("a{1,2", "a{1,2", Some((0, "a{1,2"))),
    ("x{}", "x{}", Some((0, "x{}"))),
    ("{", "{", Some((0, "{"))),
    ("a}", "a}", Some((0, "a}"))),
    ("a{1,x}", "a{1,x}", Some((0, "a{1,x}"))),
    ("\\d{1,3}/1", "x 12/1", Some((2, "12/1"))),
    ("(\\d|-)\\d", "a-5", Some((1, "-5"))),
    (
        "\"-?\\d{1,3}/\\d{1,3}\"",
        "x\"-5/1\"",
        Some((1, "\"-5/1\"")),
    ),
    ("\u{e9}{2}", "\u{e9}\u{e9}\u{e9}", Some((0, "\u{e9}\u{e9}"))),
    (".{2}", "a\nbc", Some((2, "bc"))),
    ("\\\\", "a\\b", Some((1, "\\"))),
    ("a{,2}b", "b", Some((0, "b"))),
    ("\\U0010FFFF", "a\u{10ffff}", Some((1, "\u{10ffff}"))),
];

const REFUSED: &[(&str, &str)] = &[
    ("", "PATTERN_EMPTY"),
    ("   ", "PATTERN_EMPTY"),
    ("\u{1c}", "PATTERN_EMPTY"),
    ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "PATTERN_TOO_LONG"),
    ("a*", "PATTERN_UNBOUNDED_REPEAT"),
    ("a+", "PATTERN_UNBOUNDED_REPEAT"),
    ("a{1,}", "PATTERN_UNBOUNDED_REPEAT"),
    ("a{,}", "PATTERN_UNBOUNDED_REPEAT"),
    ("a{2,}", "PATTERN_UNBOUNDED_REPEAT"),
    ("(?:ab)*", "PATTERN_UNBOUNDED_REPEAT"),
    ("a*?", "PATTERN_UNBOUNDED_REPEAT"),
    ("a{1,65}", "PATTERN_REPEAT_BOUND"),
    ("a{65}", "PATTERN_REPEAT_BOUND"),
    ("a{0,100}", "PATTERN_REPEAT_BOUND"),
    ("(a{1,2}){1,2}", "PATTERN_NESTED_QUANTIFIER"),
    ("(?:a?){2}", "PATTERN_NESTED_QUANTIFIER"),
    ("((ab){1,2}c){1,2}", "PATTERN_NESTED_QUANTIFIER"),
    ("(ab|cd){1,2}", "PATTERN_QUANTIFIED_ALTERNATION"),
    ("(?:a|bc)?d", "PATTERN_QUANTIFIED_ALTERNATION"),
    ("(?:a|b|cd){2}", "PATTERN_QUANTIFIED_ALTERNATION"),
    ("a?", "PATTERN_ZERO_WIDTH"),
    ("a{0}", "PATTERN_ZERO_WIDTH"),
    ("(?:a)?", "PATTERN_ZERO_WIDTH"),
    ("(a|)", "PATTERN_ZERO_WIDTH"),
    ("(|a)", "PATTERN_ZERO_WIDTH"),
    ("()", "PATTERN_ZERO_WIDTH"),
    ("\\1", "PATTERN_BACKREFERENCE"),
    ("(a)\\1", "PATTERN_BACKREFERENCE"),
    ("\\9", "PATTERN_BACKREFERENCE"),
    ("\\8", "PATTERN_BACKREFERENCE"),
    ("\\18", "PATTERN_BACKREFERENCE"),
    ("\\11", "PATTERN_BACKREFERENCE"),
    ("\\q", "PATTERN_SYNTAX"),
    ("\\e", "PATTERN_SYNTAX"),
    ("\\xZ1", "PATTERN_SYNTAX"),
    ("\\x4", "PATTERN_SYNTAX"),
    ("\\u12", "PATTERN_SYNTAX"),
    ("\\U0011FFFF", "PATTERN_SYNTAX"),
    ("\\", "PATTERN_SYNTAX"),
    ("a\\", "PATTERN_SYNTAX"),
    ("[", "PATTERN_SYNTAX"),
    ("[a", "PATTERN_SYNTAX"),
    ("[a-", "PATTERN_SYNTAX"),
    ("[]", "PATTERN_SYNTAX"),
    ("[^]", "PATTERN_SYNTAX"),
    ("[b-a]", "PATTERN_SYNTAX"),
    ("[\\d-z]", "PATTERN_SYNTAX"),
    ("[a-\\d]", "PATTERN_SYNTAX"),
    ("[\\8]", "PATTERN_SYNTAX"),
    ("[\\q]", "PATTERN_SYNTAX"),
    ("[\\", "PATTERN_SYNTAX"),
    ("(", "PATTERN_SYNTAX"),
    ("(a", "PATTERN_SYNTAX"),
    (")", "PATTERN_SYNTAX"),
    ("a)", "PATTERN_SYNTAX"),
    ("(?:a", "PATTERN_SYNTAX"),
    ("*a", "PATTERN_SYNTAX"),
    ("+a", "PATTERN_SYNTAX"),
    ("?a", "PATTERN_SYNTAX"),
    ("a**", "PATTERN_SYNTAX"),
    ("a+*", "PATTERN_SYNTAX"),
    ("a{2}{3}", "PATTERN_SYNTAX"),
    ("a{2}*", "PATTERN_SYNTAX"),
    ("(*a)", "PATTERN_SYNTAX"),
    ("a|*b", "PATTERN_SYNTAX"),
    ("{1}*", "PATTERN_SYNTAX"),
    ("a{3,1}", "PATTERN_SYNTAX"),
    ("{1}", "PATTERN_SYNTAX"),
    ("a{,}b", "PATTERN_UNBOUNDED_REPEAT"),
    ("(?:ab|cd){1}", "PATTERN_QUANTIFIED_ALTERNATION"),
    ("[a--b]", "PATTERN_SYNTAX"),
    ("a|b?c|d?", "PATTERN_ZERO_WIDTH"),
    ("a{1,16}b{1,16}c?", "PATTERN_CHOICE_PRODUCT"),
    ("a{1,16}b{1,17}", "PATTERN_CHOICE_PRODUCT"),
    ("(aa|bb|cc|dd|ee|ff|gg|hh|ii|jj|kk|ll|mm|nn|oo|pp|qq)(aa|bb|cc|dd|ee|ff|gg|hh|ii|jj|kk|ll|mm|nn|oo|pp|qq)", "PATTERN_CHOICE_PRODUCT"),
    ("(ab|cd)(ef|gh)(ij|kl)(mn|op)(qr|st)(uv|wx)(yz|01)(23|45)(67|89)", "PATTERN_CHOICE_PRODUCT"),
    ("a{4294967294}", "PATTERN_REPEAT_BOUND"),
    ("(?:(a)b|(a)c){1,2}", "PATTERN_QUANTIFIED_ALTERNATION"),
    ("(?:(a)b|cd){1,2}", "PATTERN_QUANTIFIED_ALTERNATION"),
    ("(?:[^ab]|c){1,2}", "PATTERN_QUANTIFIED_ALTERNATION"),
    ("a{0,15}b|a{0,15}c", "PATTERN_CHOICE_PRODUCT"),
    ("a?a?a?a?a?a?a?a?a?b", "PATTERN_CHOICE_PRODUCT"),
    ("\\877", "PATTERN_BACKREFERENCE"),
    ("\\188", "PATTERN_BACKREFERENCE"),
    ("\\178", "PATTERN_BACKREFERENCE"),
    ("[\\9]", "PATTERN_SYNTAX"),
    ("\\x+1", "PATTERN_SYNTAX"),
    ("a{1,2}?+", "PATTERN_SYNTAX"),
    ("((a{1,2})){1,2}", "PATTERN_NESTED_QUANTIFIER"),
    ("(){1,2}", "PATTERN_ZERO_WIDTH"),
];

const ADMITTED: &[&str] = &[
    "a{1,16}b{1,16}",
    "(ab|cd)(ef|gh)(ij|kl)(mn|op)(qr|st)(uv|wx)(yz|01)(23|45)",
    "(ab|cd|ef)(gh|ij|kl)",
    "ab|cd|ef|gh|ij|kl|mn|op|qr",
    "(aa|bb|cc|dd|ee|ff|gg|hh|ii|jj|kk|ll|mm|nn|oo|pp)(aa|bb|cc|dd|ee|ff|gg|hh|ii|jj|kk|ll|mm|nn|oo|pp)",
    "(?:[a-c]|d){1,2}",
    "a?a?a?a?a?a?a?a?b",
    "(?:[^aa]b|[^a]c){1,2}",
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
];

const UNREAD: &[&str] = &[
    "^a",
    "a$",
    "\\bx",
    "x\\B",
    "\\Aa",
    "a\\Z",
    "(?=a)b",
    "(?!a)b",
    "(?<=a)b",
    "(?P<n>a)",
    "(?i)a",
    "(?#c)a",
    "(?",
    "a*+",
    "a++",
    "a?+",
    "a{1,2}+",
    "\\0",
    "\\01",
    "\\101",
    "\\777",
    "[\\0]",
    "[\\1]",
    "[\\7]",
    "[\\101]",
    "\\N{DIGIT ONE}",
    "[\\N{DIGIT ONE}]",
    "\\ud800",
    "[\\ud800]",
    "a{4294967295}",
    "a{1,4294967295}",
    "a{99999999999999999999}",
];

/// The rule a pattern is refused under.
fn refusal(pattern: &str) -> &'static str {
    match compile(pattern) {
        Err(Rejected::Refused(code)) => code,
        other => panic!("{pattern:?} should be refused, got {other:?}"),
    }
}

/// What a pattern finds in a text: the character offset and the matched text.
fn found(pattern: &str, text: &str) -> Option<(usize, String)> {
    let compiled = compile(pattern).unwrap_or_else(|why| panic!("{pattern:?}: {why:?}"));
    compiled.find(text).map(|hit| (hit.start, hit.text))
}

#[test]
fn every_admitted_pattern_matches_where_python_does() {
    for (pattern, text, expected) in MATCHES {
        let expected = expected.map(|(start, matched)| (start, matched.to_owned()));
        assert_eq!(found(pattern, text), expected, "{pattern:?} on {text:?}");
    }
}

#[test]
fn every_refused_pattern_is_refused_under_the_rule_that_applies() {
    for (pattern, code) in REFUSED {
        assert_eq!(refusal(pattern), *code, "{pattern:?}");
    }
}

#[test]
fn patterns_at_the_limits_are_admitted() {
    for pattern in ADMITTED {
        assert!(compile(pattern).is_ok(), "{pattern:?}");
    }
}

#[test]
fn syntax_the_host_does_not_read_is_named_and_not_guessed() {
    for pattern in UNREAD {
        assert!(
            matches!(compile(pattern), Err(Rejected::Unread(what)) if !what.is_empty()),
            "{pattern:?}"
        );
    }
}

#[test]
fn the_length_counts_characters_not_bytes() {
    assert!(compile(&"\u{e9}".repeat(MAX_LENGTH)).is_ok());
    assert_eq!(
        refusal(&"\u{e9}".repeat(MAX_LENGTH + 1)),
        "PATTERN_TOO_LONG"
    );
}

#[test]
fn the_limits_are_the_documented_ones() {
    assert_eq!((MAX_LENGTH, MAX_BOUND, MAX_PRODUCT), (256, 64, 256));
}

#[test]
fn a_pattern_that_compiles_beyond_the_size_limit_is_refused() {
    assert_eq!(refusal(&r"\w{64}".repeat(42)), "PATTERN_COMPILE_LIMIT");
    assert!(compile(&r"[^a]{64}".repeat(28)).is_ok());
}

#[test]
fn white_space_is_what_python_calls_white_space() {
    for point in [
        '\u{9}', '\u{a}', '\u{b}', '\u{c}', '\u{d}', '\u{1c}', '\u{1d}', '\u{1e}', '\u{1f}', ' ',
        '\u{85}', '\u{a0}', '\u{2003}', '\u{3000}',
    ] {
        assert!(is_space(point), "{point:?}");
    }
    for point in ['a', '0', '_', '\u{0}', '\u{1b}', '\u{200b}'] {
        assert!(!is_space(point), "{point:?}");
    }
}

#[test]
fn a_pattern_of_white_space_only_is_empty() {
    assert_eq!(refusal("\u{a0}\t\u{1f}"), "PATTERN_EMPTY");
    assert!(compile(" a ").is_ok());
}

#[test]
fn the_offset_counts_characters_not_bytes() {
    assert_eq!(found("a", "é€a"), Some((2, "a".to_owned())));
    assert_eq!(found("€", "é€a"), Some((1, "€".to_owned())));
}

#[test]
fn the_leftmost_match_wins_and_greedy_and_lazy_repeats_differ() {
    assert_eq!(found("a{1,3}", "baaaa"), Some((1, "aaa".to_owned())));
    assert_eq!(found("a{1,3}?", "baaaa"), Some((1, "a".to_owned())));
    assert_eq!(found("b|a", "ab"), Some((0, "a".to_owned())));
    assert_eq!(found("ab|b", "ab"), Some((0, "ab".to_owned())));
}

#[test]
fn a_match_must_cover_a_character() {
    assert_eq!(found("a", ""), None);
    assert_eq!(found("[a-c]", "d"), None);
}

#[test]
fn a_compiled_pattern_can_be_copied_and_reused() {
    let compiled = compile("ab?|c").unwrap_or_else(|why| panic!("{why:?}"));
    let copy = compiled.clone();
    assert_eq!(copy.find("zzz"), None);
    assert_eq!(compiled.find("xab"), copy.find("xab"));
}
