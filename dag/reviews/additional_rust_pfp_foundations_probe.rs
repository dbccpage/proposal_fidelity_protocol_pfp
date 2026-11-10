#![allow(dead_code)]
#[path = "../../code/rust/core_types/src/category.rs"] mod category;
#[path = "../../code/rust/core_types/src/category_base.rs"] mod category_base;
#[path = "../../code/rust/core_types/src/infinity_groupoid.rs"] mod groupoid;
#[path = "../../code/rust/core_types/src/sign_topology.rs"] mod signs;

fn main() {
    use category::{Mor, MorId, ObjId};
    let id = Mor::new(MorId(1), ObjId(0), ObjId(0));
    let f = Mor::new(MorId(2), ObjId(0), ObjId(0));
    let unit_violation = category::try_finite_presentation(
        &[id], &[f], &[(1, 1, 2)]);
    println!("partial_category_accepts_id_times_id_not_id={}", unit_violation.is_ok());
    let full_table = category_base::PresentedCategory::certify(
        1, &[0], &[0, 0], &[0, 0], &[Some(1), Some(1), Some(1), Some(1)]);
    println!("full_category_refuses_same_unit_violation={}", full_table.is_err());
    let graph = groupoid::FiniteOneGroupoidWitness::try_new(
        3, &[(0,0),(1,1),(2,2),(0,1),(1,0),(1,2),(2,1)],
        &[0,1,2,4,3,6,5], &[0,1,2]);
    println!("groupoid_accepts_graph_missing_0_to_2_composite={}", graph.is_ok());
    std::panic::set_hook(Box::new(|_| {}));
    let vertex = std::panic::catch_unwind(|| signs::BalancedSigning::try_check(&[i8::MIN], &[]));
    let edge = std::panic::catch_unwind(|| signs::BalancedSigning::try_check(&[1], &[(0,0,i8::MIN)]));
    println!("minimum_i8_vertex_panics={}", vertex.is_err());
    println!("minimum_i8_edge_panics={}", edge.is_err());
    assert!(unit_violation.is_ok() && full_table.is_err() && graph.is_ok());
    assert!(vertex.is_err() && edge.is_err());
}
