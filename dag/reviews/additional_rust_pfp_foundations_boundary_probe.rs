pub fn verify_boundary_closed(faces: &[Vec<(usize, usize, i64)>]) -> bool {
    for terms in faces {
        let mut total: std::collections::BTreeMap<usize, i64> = std::collections::BTreeMap::new();
        for &(t, h, s) in terms {
            *total.entry(h).or_insert(0) += s;
            *total.entry(t).or_insert(0) -= s;
        }
        if total.values().any(|&c| c != 0) {
            return false;
        }
    }
    true
}

fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let face=vec![vec![(0,1,i64::MIN),(0,1,i64::MIN)]];
 let actual:i128=2*i128::from(i64::MIN);assert_ne!(actual,0);
 let result=std::panic::catch_unwind(||verify_boundary_closed(&face));
 match result {Err(_)=>println!("checked_boundary_panicked=true"),Ok(v)=>{assert!(v);println!("false_boundary_closed=true");}}
}
