#[path = "../../code/rust/pfp_runtime/src/f2.rs"]
mod f2;
use f2::{F2Matrix, GaugeBoard, GaugeVerdict};
fn bits(value: usize, n: usize) -> Vec<bool> { (0..n).map(|i| value & (1<<i) != 0).collect() }
fn main() {
    std::panic::set_hook(Box::new(|_|{}));
    let rows=1usize << (usize::BITS-1);
    let outcome=std::panic::catch_unwind(|| F2Matrix::new(rows, 2, vec![]));
    let observed=match outcome { Err(_)=>"panic", Ok(Ok(m))=>{assert_eq!(m.rows(),rows);"accepted_zero_storage"}, Ok(Err(_))=>"typed_refusal" };
    assert_ne!(observed,"typed_refusal");
    let wire=format!("{{\"rows\":{rows},\"cols\":2,\"data\":[]}}");
    let wire_outcome=std::panic::catch_unwind(||serde_json::from_str::<F2Matrix>(&wire));
    let wire_observed=match wire_outcome { Err(_)=>"panic",Ok(Ok(_))=>"accepted_zero_storage",Ok(Err(_))=>"typed_refusal" };
    assert_eq!(observed,wire_observed);
    let mut cases=0;
    for rows in 0..=3 { for cols in 0..=3 { for encoded in 0..(1usize<<(rows*cols)) {
        let m=F2Matrix::new(rows,cols,bits(encoded,rows*cols)).unwrap();
        let image:std::collections::BTreeSet<_>=(0..(1usize<<cols)).map(|x|m.apply(&bits(x,cols)).unwrap()).collect();
        assert_eq!(image.len(),1usize<<m.rank());
        let basis=m.kernel_basis(); assert_eq!(basis.len()+m.rank(),cols);
        for v in &basis { assert!(m.apply(v).unwrap().iter().all(|x|!*x)); }
        let span:std::collections::BTreeSet<_>=(0..(1usize<<basis.len())).map(|mask|{
            let mut v=vec![false;cols]; for (i,b) in basis.iter().enumerate(){if mask&(1<<i)!=0 {for j in 0..cols {v[j]^=b[j];}}} v
        }).collect();
        assert_eq!(span.len(),1usize<<basis.len());
        for encoded_rhs in 0..(1usize<<rows) {
            let rhs=bits(encoded_rhs,rows); let solved=m.solve(&rhs).unwrap();
            assert_eq!(solved.is_some(),image.contains(&rhs));
            if let Some(v)=solved {assert_eq!(m.apply(&v).unwrap(),rhs);}
            cases+=1;
        }
    }}}
    let mut boards=0;
    for e0 in 0..16 {for e1 in 0..16 {let board=GaugeBoard::new(F2Matrix::new(2,2,bits(e0,4)).unwrap(),F2Matrix::new(2,2,bits(e1,4)).unwrap());
        for a0 in 0..4 {let a=bits(a0,2);let verdict=board.classify(&a).unwrap();
            match verdict {
                GaugeVerdict::BoardInvalid{product}=>assert!(!product.is_zero()),
                GaugeVerdict::LocalCurvature{syndrome}=>{assert!(board.chain_law().unwrap().is_none());assert_eq!(syndrome,board.d1.apply(&a).unwrap());assert!(syndrome.iter().any(|x|*x));},
                GaugeVerdict::GaugeExact{lambda}=>assert_eq!(board.d0.apply(&lambda).unwrap(),a),
                GaugeVerdict::GlobalH1Obstruction{separator}=>{assert!(board.d1.apply(&a).unwrap().iter().all(|x|!*x));assert!(board.d0.transpose().apply(&separator).unwrap().iter().all(|x|!*x));assert!(f2::pairing(&a,&separator).unwrap());}
            } boards+=1;
        }
    }}
    println!("{{\"overflow_constructor\":\"{observed}\",\"overflow_deserialization\":\"{wire_observed}\",\"small_linear_systems\":{cases},\"small_gauge_cases\":{boards}}}");
}
