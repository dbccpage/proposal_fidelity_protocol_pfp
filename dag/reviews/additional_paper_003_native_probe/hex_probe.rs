fn hex_to_bytes(hex: &str) -> Result<Vec<u8>, String> {
    if hex.len() % 2 != 0 {
        return Err("Odd length hex string".to_string());
    }
    (0..hex.len())
        .step_by(2)
        .map(|i| {
            u8::from_str_radix(&hex[i..i + 2], 16).map_err(|e| format!("Invalid hex byte: {}", e))
        })
        .collect()
}

fn main() {
    std::panic::set_hook(Box::new(|_| {}));
    assert_eq!(hex_to_bytes("0a"), Ok(vec![10]));
    assert!(hex_to_bytes("zz").is_err());
    assert!(hex_to_bytes("a").is_err());
    let panicked = std::panic::catch_unwind(|| hex_to_bytes("aéa")).is_err();
    assert!(panicked);
    println!("ascii_valid_pass; ascii_invalid_refused; odd_length_refused; utf8_even_length_panics");
}
