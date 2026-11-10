#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_contracts/src/improvement_canonical_json.rs"] mod canonical;
    fn b64_decode(s: &str) -> Result<Vec<u8>, String> {
        fn val(c: u8) -> Result<u8, String> {
            match c {
                b'A'..=b'Z' => Ok(c - b'A'),
                b'a'..=b'z' => Ok(c - b'a' + 26),
                b'0'..=b'9' => Ok(c - b'0' + 52),
                b'+' => Ok(62),
                b'/' => Ok(63),
                _ => Err(format!("invalid base64 byte {c}")),
            }
        }
        let bytes = s.as_bytes();
        if !bytes.len().is_multiple_of(4) {
            return Err("invalid base64 length".to_owned());
        }
        let mut out = Vec::with_capacity(bytes.len() / 4 * 3);
        for chunk in bytes.chunks(4) {
            let pad = chunk.iter().filter(|&&c| c == b'=').count();
            let n = ((val(chunk[0])? as u32) << 18)
                | ((val(chunk[1])? as u32) << 12)
                | ((if chunk[2] == b'=' {
                    0
                } else {
                    val(chunk[2])? as u32
                }) << 6)
                | (if chunk[3] == b'=' {
                    0
                } else {
                    val(chunk[3])? as u32
                });
            out.push(((n >> 16) & 0xFF) as u8);
            if pad < 2 {
                out.push(((n >> 8) & 0xFF) as u8);
            }
            if pad < 1 {
                out.push((n & 0xFF) as u8);
            }
        }
        Ok(out)
    }

fn main(){
 for n in [f64::NAN,f64::INFINITY,f64::NEG_INFINITY] { let result=canonical::dumps_canonical_v1(&n).unwrap(); assert_eq!(result,b"null"); }
 assert!(canonical::dumps_canonical_v1(&1.5f64).is_err());
 assert_eq!(canonical::hash_canonical_v1(&f64::NAN).unwrap(),canonical::hash_canonical_v1(&Option::<u8>::None).unwrap());
 println!("three_nonfinite_floats_accepted_as_null=true; finite_float_refused=true");
 for s in ["AA=A","AB==","AA==AAAA"] {let result=b64_decode(s).unwrap();println!("invalid_or_noncanonical_base64_accepted={s}:{result:?}");}
}
