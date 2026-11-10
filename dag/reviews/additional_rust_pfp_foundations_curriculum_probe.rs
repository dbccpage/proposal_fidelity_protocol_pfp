#[path = "../../code/rust/pfp_runtime/src/curriculum.rs"]
mod curriculum;
use curriculum::{CurriculumGenerator as G, Edge};
fn edges(pairs:&[(usize,usize)])->Vec<Edge>{pairs.iter().map(|&(u,v)|Edge{u,v,weight:1}).collect()}
fn triangles(es:&[Edge])->usize{let mut count=0;let has=|a,b|es.iter().any(|e|(e.u==a&&e.v==b)||(e.u==b&&e.v==a));for a in 0..6{for b in a+1..6{for c in b+1..6{if has(a,b)&&has(b,c)&&has(a,c){count+=1}}}}count}
fn main(){
    let bipartite=edges(&[(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5)]);
    let prism=edges(&[(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5)]);
    let a=G::compute_canonical_digest(6,&bipartite);let b=G::compute_canonical_digest(6,&prism);
    assert_eq!(triangles(&bipartite),0);assert_eq!(triangles(&prism),2);assert_eq!(a,b);
    let seed0=G::generate_cochain_instance(4,0,"checker").unwrap();let seed1=G::generate_cochain_instance(4,1,"checker").unwrap();assert_eq!(seed0,seed1);
    println!("{{\"nonisomorphic_connected_graphs_share_digest\":true,\"triangles\":[0,2],\"digest\":\"{a}\",\"seed_zero_equals_seed_one\":true}}");
}
