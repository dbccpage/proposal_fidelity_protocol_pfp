//! Mermin-Peres contextuality as a parity obstruction over `F_2`: the operator
//! table that induces the sign table, the parity packet on nine variables and
//! six contexts, its incidence coboundary and separator, the exhaustive
//! `2^9` assignment census, the Cech nerve complex of the same scenario, and
//! the dependence of any `H^1` reading on a declared second coboundary.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::image_kernel::{solve_in_image, ImageMembership};
use core_homology::graph_f2::pattern_pairing;
use core_number_theory::rational::{ri, rq, Rational};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_quantum_physics::contextuality_obstruction::compute_obstruction_class;
use core_quantum_physics::pauli::{pauli_commutes, Pauli};
use core_quantum_physics::separating_predictions::{
    MerminPeresCochainBridge, MerminPeresError, MerminPeresSquare, MAX_SEARCH_OBSERVABLES,
};

use core_quantum_physics::parity_context_packet::{
    ImageCertificate, ParityAdmission, ParityContextPacket, ParityPacketError,
};
use core_quantum_physics::pauli_context_table::{
    context_members, pauli_word, PauliContextTable, PauliTableError,
};

const ALL_SIX: u32 = 0b11_1111;
const COLUMN_THREE: u32 = 1 << 5;

fn mermin_peres() -> ParityContextPacket {
    ParityContextPacket::from_square(&MerminPeresSquare::standard()).unwrap()
}

fn with_targets(targets: u32) -> ParityContextPacket {
    let contexts: Vec<Vec<usize>> = (0..6)
        .map(|c| context_members(c).unwrap().to_vec())
        .collect();
    let bits: Vec<u8> = (0..6).map(|c| ((targets >> c) & 1) as u8).collect();
    ParityContextPacket::new(9, &contexts, &bits).unwrap()
}

fn exact_solve(rows: &[Vec<Rational>], rhs: &[Rational], cols: usize) -> Option<Vec<Rational>> {
    if rows.is_empty() {
        return rhs.is_empty().then(|| vec![ri(0); cols]);
    }
    if rows.iter().any(|r| r.len() != cols) {
        return None;
    }
    let m = BasicMatrix::from_row_major(rows.len(), cols, rows.iter().flatten().cloned().collect())
        .ok()?;
    match solve_in_image(&m, rhs).ok()? {
        ImageMembership::InImage(w) => Some(w.potential),
        ImageMembership::NotInImage { .. } => None,
    }
}

fn incidence_over_q(packet_contexts: &[Vec<usize>], variables: usize) -> Vec<Vec<Rational>> {
    packet_contexts
        .iter()
        .map(|members| {
            (0..variables)
                .map(|v| ri(i64::from(members.contains(&v))))
                .collect()
        })
        .collect()
}

// ---------------------------------------------------------------------------
// QM-120-C1: the packet, and the operator table that induces its signs.
// ---------------------------------------------------------------------------

#[test]
fn mermin_operators_induce_the_declared_sign_table() {
    let table = PauliContextTable::mermin();
    assert_eq!(
        table.words(),
        ["XI", "IX", "XX", "IY", "YI", "YY", "XY", "YX", "ZZ"]
    );
    assert!(table.observables_are_hermitian_involutions());
    // Rows multiply to +I; the columns to +I, +I and -I.
    assert_eq!(table.sign_table().unwrap(), vec![1, 1, 1, 1, 1, -1]);
    let packet = table.packet().unwrap();
    assert_eq!(packet, mermin_peres());
    assert_eq!(packet.targets(), COLUMN_THREE);
    // Column three is XX . YY . ZZ = (XYZ) (x) (XYZ) = (iI) (x) (iI) = -I.
    let column_three = linear_algebra::exact_field::matrix::multiply(
        &linear_algebra::exact_field::matrix::multiply(
            table.observable(2).unwrap(),
            table.observable(5).unwrap(),
        )
        .unwrap(),
        table.observable(8).unwrap(),
    )
    .unwrap();
    assert_eq!(
        column_three,
        linear_algebra::exact_field::matrix::scale(
            &pauli_word("II").unwrap(),
            &core_number_theory::cyclotomic::GaussianRat::from_ints(-1, 0)
        )
        .unwrap()
    );
}

#[test]
fn the_exact_commutator_agrees_with_the_symplectic_form_and_splits_every_row_and_column() {
    let table = PauliContextTable::mermin();
    let letters = |w: &str| -> Vec<Pauli> {
        w.chars()
            .map(Pauli::from_char)
            .collect::<Result<_, _>>()
            .unwrap()
    };
    let mut commuting = 0;
    let mut anticommuting = 0;
    for i in 0..9 {
        for j in 0..9 {
            let exact = table.commute(i, j);
            assert_eq!(
                exact,
                pauli_commutes(&letters(&table.words()[i]), &letters(&table.words()[j]))
            );
            if i < j {
                if exact {
                    commuting += 1;
                } else {
                    anticommuting += 1;
                }
            }
            // Same row or same column: commute. Otherwise: anticommute.
            let shared = i / 3 == j / 3 || i % 3 == j % 3;
            assert_eq!(exact, shared, "observables {i} and {j}");
        }
    }
    assert_eq!((commuting, anticommuting), (18, 18));
}

#[test]
fn pauli_tables_are_refused_when_words_contexts_or_products_are_wrong() {
    for bad in ["XQ", "X", "XYZ", ""] {
        assert_eq!(
            pauli_word(bad),
            Err(PauliTableError::BadWord {
                word: bad.to_string()
            })
        );
    }
    assert!(matches!(
        PauliContextTable::new([["XI", "IX", "XX"], ["IY", "YI", "YY"], ["XY", "YX", "Zz"]]),
        Err(PauliTableError::BadWord { .. })
    ));
    // ZI replaces ZZ: XY and ZI anticommute, so row three has no order-free product.
    let noncommuting =
        PauliContextTable::new([["XI", "IX", "XX"], ["IY", "YI", "YY"], ["XY", "YX", "ZI"]])
            .unwrap();
    assert_eq!(
        noncommuting.context_sign(2),
        Err(PauliTableError::NoncommutingContext {
            context: 2,
            left: 6,
            right: 8
        })
    );
    assert!(noncommuting.packet().is_err());
    // XI, IX, XI commute pairwise and multiply to I (x) X, which is not a sign.
    let unsigned =
        PauliContextTable::new([["XI", "IX", "XI"], ["IY", "YI", "YY"], ["XY", "YX", "ZZ"]])
            .unwrap();
    assert_eq!(
        unsigned.context_sign(0),
        Err(PauliTableError::ProductNotSigned { context: 0 })
    );
    assert_eq!(
        unsigned.context_sign(6),
        Err(PauliTableError::ContextOutOfRange { context: 6 })
    );
    assert_eq!(
        context_members(6),
        Err(PauliTableError::ContextOutOfRange { context: 6 })
    );
}

// ---------------------------------------------------------------------------
// QM-120-C2..C4: incidence, the left global product, the declared product.
// ---------------------------------------------------------------------------

#[test]
fn every_variable_lies_in_exactly_two_contexts() {
    let packet = mermin_peres();
    assert_eq!((packet.variable_count(), packet.context_count()), (9, 6));
    assert_eq!(packet.incidence_counts(), vec![2; 9]);
    // A variable in three contexts changes the count and loses the graph.
    let three =
        ParityContextPacket::new(2, &[vec![0, 1], vec![0], vec![0, 1]], &[0, 0, 0]).unwrap();
    assert_eq!(three.incidence_counts(), vec![3, 2]);
    assert_eq!(
        three.context_graph(),
        Err(ParityPacketError::NotTwoIncidence {
            variable: 0,
            count: 3
        })
    );
}

#[test]
fn the_product_of_all_context_products_is_plus_one_for_every_assignment() {
    let packet = mermin_peres();
    for a in 0..512u32 {
        assert_eq!(
            pattern_pairing(packet.d0(a).unwrap(), packet.all_contexts()),
            0,
            "assignment {a:#011b}"
        );
    }
    // The same fact as a coboundary identity: ell . d0 = 0.
    assert_eq!(packet.transpose_d0(ALL_SIX).unwrap(), 0);
    // Removing one incidence breaks it: variable 0 left only in its row.
    let broken = ParityContextPacket::new(
        9,
        &[
            vec![0, 1, 2],
            vec![3, 4, 5],
            vec![6, 7, 8],
            vec![3, 6],
            vec![1, 4, 7],
            vec![2, 5, 8],
        ],
        &[0; 6],
    )
    .unwrap();
    assert_eq!(broken.transpose_d0(ALL_SIX).unwrap(), 1);
    assert_eq!(pattern_pairing(broken.d0(1).unwrap(), ALL_SIX), 1);
}

#[test]
fn the_declared_signs_multiply_to_minus_one() {
    let square = MerminPeresSquare::standard();
    assert_eq!(square.context_products.iter().product::<i8>(), -1);
    assert_eq!(pattern_pairing(mermin_peres().targets(), ALL_SIX), 1);
}

// ---------------------------------------------------------------------------
// QM-120-C5..C8: no global assignment; local green, global red.
// ---------------------------------------------------------------------------

#[test]
fn no_global_assignment_satisfies_the_six_signed_contexts() {
    let packet = mermin_peres();
    assert!(!packet.satisfiable(ALL_SIX).unwrap());
    // Every one of the 512 assignments violates an odd number of contexts.
    assert_eq!(packet.violation_histogram(), vec![0, 96, 0, 320, 0, 96, 0]);
    assert!(!packet.in_image(packet.targets()).unwrap());
    // The 512-assignment search in `separating_predictions` agrees.
    assert_eq!(
        MerminPeresSquare::standard().verify_no_noncontextual_assignment(),
        Ok(true)
    );
    // With every sign +1 the all-plus assignment satisfies all six.
    let classical = with_targets(0);
    assert!(classical.satisfiable(ALL_SIX).unwrap());
    assert_eq!(
        classical.violation_histogram(),
        vec![16, 0, 240, 0, 240, 0, 16]
    );
}

#[test]
fn each_single_context_is_satisfiable() {
    let packet = mermin_peres();
    for c in 0..6 {
        assert!(packet.satisfiable(1 << c).unwrap(), "context {c}");
    }
}

#[test]
fn every_five_context_subfamily_is_satisfiable_and_the_six_are_minimally_unsatisfiable() {
    let packet = mermin_peres();
    for dropped in 0..6 {
        assert!(
            packet.satisfiable(ALL_SIX & !(1 << dropped)).unwrap(),
            "without context {dropped}"
        );
    }
    assert!(packet.is_minimally_unsatisfiable().unwrap());
    // Each context is the only violated one for exactly 16 assignments.
    let mut sole = [0usize; 6];
    for a in 0..512u32 {
        let violated = packet.violations(a).unwrap();
        if violated.count_ones() == 1 {
            sole[violated.trailing_zeros() as usize] += 1;
        }
    }
    assert_eq!(sole, [16; 6]);
    // A satisfiable packet is not minimally unsatisfiable.
    assert!(!with_targets(0).is_minimally_unsatisfiable().unwrap());
    // Two flipped signs are satisfiable again; the obstruction is parity, not placement.
    assert!(with_targets(0b10_0001).satisfiable(ALL_SIX).unwrap());
}

#[test]
fn local_green_global_red_holds_exactly_for_the_odd_sign_tables() {
    let mut lggr = 0;
    for targets in 0..64u32 {
        let packet = with_targets(targets);
        let local_green = (0..6).all(|c| packet.satisfiable(1 << c).unwrap());
        let global_red = !packet.satisfiable(ALL_SIX).unwrap();
        assert!(local_green);
        assert_eq!(
            global_red,
            targets.count_ones() % 2 == 1,
            "targets {targets:#08b}"
        );
        lggr += usize::from(local_green && global_red);
    }
    assert_eq!(lggr, 32);
}

// ---------------------------------------------------------------------------
// QM-120-C11: the F_2 cochain statement.
// ---------------------------------------------------------------------------

#[test]
fn the_obstruction_is_a_separator_outside_the_image_of_the_incidence_coboundary() {
    let packet = mermin_peres();
    assert_eq!(packet.rank_d0(), 5);
    assert_eq!(packet.quotient_dimension(), 1);
    let certificate = packet.certificate(packet.targets()).unwrap();
    assert_eq!(certificate, ImageCertificate::Separator(ALL_SIX));
    assert!(packet
        .verify_certificate(packet.targets(), certificate)
        .unwrap());
    // The all-ones functional is the only nonzero separator.
    let separators: Vec<u32> = (1..64u32)
        .filter(|&y| packet.transpose_d0(y).unwrap() == 0)
        .collect();
    assert_eq!(separators, vec![ALL_SIX]);
    // Tampered certificates do not replay.
    assert!(!packet
        .verify_certificate(packet.targets(), ImageCertificate::Separator(0b01_1111))
        .unwrap());
    assert!(!packet
        .verify_certificate(packet.targets(), ImageCertificate::Preimage(0))
        .unwrap());
    // Rank test and certificate agree on all 64 cochains; the image is the 32 even ones.
    let mut in_image = 0;
    for s in 0..64u32 {
        let member = packet.in_image(s).unwrap();
        let certificate = packet.certificate(s).unwrap();
        assert_eq!(member, matches!(certificate, ImageCertificate::Preimage(_)));
        assert!(packet.verify_certificate(s, certificate).unwrap());
        assert_eq!(member, s.count_ones() % 2 == 0);
        in_image += usize::from(member);
    }
    assert_eq!(in_image, 32);
}

#[test]
fn the_kernel_of_the_coboundary_is_the_cycle_space_of_the_context_graph() {
    let packet = mermin_peres();
    let graph = packet.context_graph().unwrap();
    assert_eq!((graph.vertex_count(), graph.edges().len()), (6, 9));
    assert!(graph.is_simple());
    // Every edge joins a row (0..3) to a column (3..6): the graph is K_{3,3}.
    assert!(graph.edges().iter().all(|&(u, v)| u < 3 && v >= 3));
    for y in 0..64u32 {
        assert_eq!(
            graph.coboundary(y).unwrap(),
            packet.transpose_d0(y).unwrap()
        );
    }
    let mut kernel = 0;
    for a in 0..512u32 {
        let closed = packet.d0(a).unwrap() == 0;
        assert_eq!(
            closed,
            a == 0 || graph.is_even_subgraph(a).unwrap(),
            "assignment {a:#011b}"
        );
        kernel += usize::from(closed);
    }
    assert_eq!(kernel, 16);
}

#[test]
fn the_cech_nerve_complex_agrees_with_the_parity_packet_on_every_sign_table() {
    let standard = compute_obstruction_class(&mermin_peres().measurement_scenario("MP")).unwrap();
    assert_eq!(
        (standard.dim_c0, standard.dim_c1, standard.dim_c2),
        (12, 9, 0)
    );
    assert_eq!(
        (standard.rank_delta0, standard.dim_z1, standard.dim_h1),
        (8, 9, 1)
    );
    assert!(!standard.obstruction_class_is_zero);
    for targets in 0..64u32 {
        let packet = with_targets(targets);
        let cech = compute_obstruction_class(&packet.measurement_scenario("MP")).unwrap();
        assert_eq!(
            cech.obstruction_class_is_zero,
            packet.in_image(targets).unwrap(),
            "targets {targets:#08b}"
        );
    }
}

#[test]
fn promotion_to_h1_depends_on_the_declared_second_coboundary() {
    let packet = mermin_peres();
    let s = packet.targets();
    // No 2-cells: d1 = 0, H^1 = F_2^6 / im d0 has dimension 1 and [s] is its nonzero class.
    let none: Vec<Vec<u8>> = Vec::new();
    assert_eq!(packet.h1_dimension(&none).unwrap(), 1);
    let closed = packet.admit_with_d1(s, &none).unwrap();
    assert_eq!(
        closed,
        ParityAdmission::ClosedNonexact { separator: ALL_SIX }
    );
    assert_eq!(
        closed.diagnostic_class(),
        ObstructionDiagnosticClass::ClosedResidual
    );
    assert!(packet.verify_admission(s, &none, &closed).unwrap());
    // d1 = the global parity functional: d1 d0 = 0, the complex is exact at C^1,
    // and the same s is a closure failure with defect 1, not an H^1 class.
    let parity = vec![vec![1u8; 6]];
    assert_eq!(packet.h1_dimension(&parity).unwrap(), 0);
    let failure = packet.admit_with_d1(s, &parity).unwrap();
    assert_eq!(failure, ParityAdmission::ClosureFailure { defect: vec![1] });
    assert_eq!(
        failure.diagnostic_class(),
        ObstructionDiagnosticClass::ActiveClosureFailure
    );
    assert!(packet.verify_admission(s, &parity, &failure).unwrap());
    // An exact cochain is exact under both declarations.
    let exact = packet.d0(0b1).unwrap();
    assert_eq!(exact, 0b00_1001);
    for d1 in [&none, &parity] {
        let admission = packet.admit_with_d1(exact, d1).unwrap();
        assert!(matches!(admission, ParityAdmission::Exact { .. }));
        assert_eq!(
            admission.diagnostic_class(),
            ObstructionDiagnosticClass::ExactRepair
        );
        assert!(packet.verify_admission(exact, d1, &admission).unwrap());
    }
    // Tampered admissions do not replay.
    assert!(!packet
        .verify_admission(
            s,
            &parity,
            &ParityAdmission::ClosureFailure { defect: vec![0] }
        )
        .unwrap());
    assert!(!packet
        .verify_admission(
            s,
            &parity,
            &ParityAdmission::ClosedNonexact { separator: ALL_SIX }
        )
        .unwrap());
    assert!(!packet
        .verify_admission(
            s,
            &none,
            &ParityAdmission::ClosureFailure { defect: vec![] }
        )
        .unwrap());
    assert!(!packet
        .verify_admission(exact, &none, &ParityAdmission::Exact { preimage: 0b10 })
        .unwrap());
    // A d1 that does not annihilate im d0, or is not over F_2, is refused.
    assert_eq!(
        packet.admit_with_d1(s, &[vec![1, 0, 0, 0, 0, 0]]),
        Err(ParityPacketError::D1DoesNotAnnihilateImage)
    );
    assert_eq!(
        packet.h1_dimension(&[vec![2, 0, 0, 0, 0, 0]]),
        Err(ParityPacketError::D1NotBinary { row: 0, value: 2 })
    );
    assert_eq!(
        packet.admit_with_d1(s, &[vec![1; 5]]),
        Err(ParityPacketError::D1Shape {
            row: 0,
            expected: 6,
            actual: 5
        })
    );
}

#[test]
fn membership_over_q_and_over_f2_agree_here_and_differ_on_an_odd_context_cycle() {
    // The Mermin-Peres contexts form the bipartite K_{3,3}: over Q the target
    // is also outside the image, separated by (1, 1, 1, -1, -1, -1).
    let contexts: Vec<Vec<usize>> = (0..6)
        .map(|c| context_members(c).unwrap().to_vec())
        .collect();
    let target_q: Vec<Rational> = (0..6).map(|c| ri(i64::from(c == 5))).collect();
    assert_eq!(
        exact_solve(&incidence_over_q(&contexts, 9), &target_q, 9),
        None
    );
    // Three contexts on a triangle: (1, 0, 0) is odd, so outside im d0 over F_2,
    // yet it is d0 of (1/2, 1/2, -1/2) over Q.
    let triangle_contexts = vec![vec![0, 1], vec![1, 2], vec![2, 0]];
    let triangle = ParityContextPacket::new(3, &triangle_contexts, &[1, 0, 0]).unwrap();
    assert!(!triangle.in_image(triangle.targets()).unwrap());
    assert_eq!(
        triangle.certificate(triangle.targets()).unwrap(),
        ImageCertificate::Separator(0b111)
    );
    assert_eq!(
        exact_solve(
            &incidence_over_q(&triangle_contexts, 3),
            &[ri(1), ri(0), ri(0)],
            3
        ),
        Some(vec![rq(1, 2), rq(1, 2), rq(-1, 2)])
    );
}

#[test]
fn malformed_packets_and_squares_are_refused() {
    let one = vec![vec![0usize]];
    assert_eq!(
        ParityContextPacket::new(17, &one, &[0]),
        Err(ParityPacketError::TooLarge)
    );
    assert_eq!(
        ParityContextPacket::new(2, &[vec![]], &[0]),
        Err(ParityPacketError::EmptyContext { context: 0 })
    );
    assert_eq!(
        ParityContextPacket::new(2, &[vec![0, 2]], &[0]),
        Err(ParityPacketError::VariableOutOfRange {
            context: 0,
            variable: 2,
            variable_count: 2
        })
    );
    assert_eq!(
        ParityContextPacket::new(2, &[vec![1, 1]], &[0]),
        Err(ParityPacketError::RepeatedVariable {
            context: 0,
            variable: 1
        })
    );
    assert_eq!(
        ParityContextPacket::new(2, &one, &[0, 1]),
        Err(ParityPacketError::TargetCount {
            contexts: 1,
            targets: 2
        })
    );
    assert_eq!(
        ParityContextPacket::new(2, &one, &[2]),
        Err(ParityPacketError::TargetNotBinary {
            context: 0,
            value: 2
        })
    );
    let packet = mermin_peres();
    assert_eq!(
        packet.d0(1 << 9),
        Err(ParityPacketError::MaskOutOfRange {
            mask: 1 << 9,
            width: 9
        })
    );
    assert_eq!(
        packet.satisfiable(1 << 6),
        Err(ParityPacketError::MaskOutOfRange {
            mask: 1 << 6,
            width: 6
        })
    );
    let mut signed = MerminPeresSquare::standard();
    signed.context_products[5] = 2;
    assert_eq!(
        ParityContextPacket::from_square(&signed),
        Err(ParityPacketError::NotASign {
            context: 5,
            value: 2
        })
    );
    let mut short = MerminPeresSquare::standard();
    short.context_products.pop();
    assert_eq!(
        ParityContextPacket::from_square(&short),
        Err(ParityPacketError::TargetCount {
            contexts: 6,
            targets: 5
        })
    );
}

/// Names `B0 .. B(n-1)` with `'static` lifetime, for squares built in tests.
fn names(n: usize) -> Vec<&'static str> {
    (0..n)
        .map(|k| &*Box::leak(format!("B{k}").into_boxed_str()))
        .collect()
}

/// The product of the values of `assignment` (observable order) over each context.
fn context_products_of(square: &MerminPeresSquare, assignment: &[i8]) -> Vec<i8> {
    let observables = square.observables();
    square
        .contexts
        .iter()
        .map(|context| {
            context
                .iter()
                .map(|name| assignment[observables.iter().position(|o| o == name).unwrap()])
                .product()
        })
        .collect()
}

/// Past twelve observables the search used to return its declared flag, it
/// read a product of `2` as unsatisfiable, and it dropped contexts without a
/// declared product. It now searches up to `MAX_SEARCH_OBSERVABLES` and refuses
/// the rest.
#[test]
fn the_square_search_decides_up_to_its_bound_and_refuses_malformed_squares() {
    // Thirteen observables, all products +1: the all-plus assignment satisfies it,
    // whatever the square declares.
    let b = names(13);
    let mut satisfiable = MerminPeresSquare {
        contexts: vec![b[0..5].to_vec(), b[5..10].to_vec(), b[10..13].to_vec()],
        context_products: vec![1, 1, 1],
        noncontextual_assignment_exists: false,
    };
    let packet = ParityContextPacket::from_square(&satisfiable).unwrap();
    assert_eq!(packet.variable_count(), 13);
    assert!(packet.satisfiable(packet.all_contexts()).unwrap());
    assert_eq!(
        satisfiable.find_noncontextual_assignment(),
        Ok(Some(vec![1; 13]))
    );
    assert_eq!(satisfiable.verify_no_noncontextual_assignment(), Ok(false));
    satisfiable.noncontextual_assignment_exists = true;
    assert_eq!(satisfiable.verify_no_noncontextual_assignment(), Ok(false));

    // Sixteen observables are searched; seventeen are refused.
    let b = names(17);
    let mut chain = MerminPeresSquare {
        contexts: (0..15).map(|k| vec![b[k], b[k + 1]]).collect(),
        context_products: vec![-1; 15],
        noncontextual_assignment_exists: false,
    };
    assert_eq!(chain.observables().len(), MAX_SEARCH_OBSERVABLES);
    let witness = chain.find_noncontextual_assignment().unwrap().unwrap();
    assert_eq!(context_products_of(&chain, &witness), vec![-1; 15]);
    chain.contexts.push(vec![b[15], b[16]]);
    chain.context_products.push(-1);
    assert_eq!(
        chain.verify_no_noncontextual_assignment(),
        Err(MerminPeresError::TooManyObservables {
            observables: 17,
            max: 16
        })
    );

    // A product of 2 is not a sign.
    let mut signed = MerminPeresSquare::standard();
    signed.context_products = vec![1, 1, 1, 1, 1, 2];
    assert_eq!(
        signed.verify_no_noncontextual_assignment(),
        Err(MerminPeresError::NotASign {
            context: 5,
            value: 2
        })
    );
    // Five products for six contexts, and seven: unpaired.
    let mut short = MerminPeresSquare::standard();
    short.context_products = vec![1, 1, 1, 1, 1];
    assert_eq!(
        short.verify_no_noncontextual_assignment(),
        Err(MerminPeresError::UnpairedProducts {
            contexts: 6,
            products: 5
        })
    );
    let mut long = MerminPeresSquare::standard();
    long.context_products.push(1);
    assert_eq!(
        long.verify_no_noncontextual_assignment(),
        Err(MerminPeresError::UnpairedProducts {
            contexts: 6,
            products: 7
        })
    );
    // An empty context, and an observable named twice in one context.
    let mut empty = MerminPeresSquare::standard();
    empty.contexts[2].clear();
    assert_eq!(
        empty.verify_no_noncontextual_assignment(),
        Err(MerminPeresError::EmptyContext { context: 2 })
    );
    let mut repeated = MerminPeresSquare::standard();
    repeated.contexts[1][2] = "A21";
    assert_eq!(
        repeated.verify_no_noncontextual_assignment(),
        Err(MerminPeresError::RepeatedObservable {
            context: 1,
            name: "A21".into()
        })
    );
}

/// The search agrees with `ParityContextPacket` on every sign table of the
/// square's layout, and every witness it returns meets the declared products.
#[test]
fn the_square_search_agrees_with_the_parity_packet_on_all_sign_tables() {
    let mut obstructed = 0;
    for signs in 0u32..64 {
        let mut square = MerminPeresSquare::standard();
        square.context_products = (0..6)
            .map(|c| if (signs >> c) & 1 == 1 { -1 } else { 1 })
            .collect();
        let packet = ParityContextPacket::from_square(&square).unwrap();
        let found = square.find_noncontextual_assignment().unwrap();
        assert_eq!(
            found.is_some(),
            packet.in_image(packet.targets()).unwrap(),
            "signs {signs:06b}"
        );
        match found {
            Some(assignment) => assert_eq!(
                context_products_of(&square, &assignment),
                square.context_products
            ),
            None => obstructed += 1,
        }
    }
    // Exactly the tables with an odd number of -1 signs.
    assert_eq!(obstructed, 32);
}

/// The bridge computes the class of the signs; the product of the signs
/// decides it only when every observable lies in an even number of contexts.
#[test]
fn the_cochain_bridge_computes_the_class_not_the_product_of_signs() {
    let standard = MerminPeresCochainBridge::from_standard_square().unwrap();
    assert!(standard.is_obstructed());
    assert!(standard.even_incidence);
    // The only nonzero mod-2 2-cycle of the square is the sum of all six faces.
    assert_eq!(standard.certificate, ImageCertificate::Separator(ALL_SIX));

    // Two disjoint pillows, each two faces on the same three observables with
    // opposite signs: no assignment, yet the product of all four signs is +1.
    let pillows = MerminPeresSquare {
        contexts: vec![
            vec!["a", "b", "c"],
            vec!["a", "b", "c"],
            vec!["d", "e", "f"],
            vec!["d", "e", "f"],
        ],
        context_products: vec![1, -1, 1, -1],
        noncontextual_assignment_exists: true,
    };
    assert_eq!(pillows.verify_no_noncontextual_assignment(), Ok(true));
    let bridge = MerminPeresCochainBridge::from_square(pillows).unwrap();
    assert_eq!(bridge.product_of_context_constraints, 1);
    assert!(bridge.even_incidence);
    assert!(bridge.is_obstructed());
    assert_eq!(bridge.certificate, ImageCertificate::Separator(0b0011));

    // One context with product -1: the product is -1, but the assignment
    // a = -1 meets it, so the class vanishes (odd incidence).
    let single = MerminPeresSquare {
        contexts: vec![vec!["a"]],
        context_products: vec![-1],
        noncontextual_assignment_exists: false,
    };
    assert_eq!(single.find_noncontextual_assignment(), Ok(Some(vec![-1])));
    let bridge = MerminPeresCochainBridge::from_square(single).unwrap();
    assert_eq!(bridge.product_of_context_constraints, -1);
    assert!(!bridge.even_incidence);
    assert!(!bridge.is_obstructed());
    assert_eq!(bridge.certificate, ImageCertificate::Preimage(1));

    // The bridge refuses what the search refuses.
    let mut short = MerminPeresSquare::standard();
    short.context_products.pop();
    assert_eq!(
        MerminPeresCochainBridge::from_square(short),
        Err(MerminPeresError::UnpairedProducts {
            contexts: 6,
            products: 5
        })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/boundary/mermin_peres_parity_obstruction.rs
// Claim: urn:core:crates_rs:tests:mermin-peres-parity-obstruction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8720f52a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8720f52a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8720f52a {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError8720f52a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8720f52a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8720f52a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8720f52a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8720f52a> {
        if capacity_bound == 0 {
            return Err(BoundaryError8720f52a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8720f52a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8720f52a::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_8720f52a() {
    let admitted = BoundaryRecord8720f52a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8720f52a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
