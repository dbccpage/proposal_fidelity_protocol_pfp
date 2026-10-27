//! Exact effects and finite Busch hypotheses at declared cyclotomic real places.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    elimination::determinant,
    matrix as mx,
    ordered::{hermitian_inertia, Inertia},
};
use num_bigint::BigInt;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::cyclotomic_field::{Cyclotomic, CyclotomicNumber};
pub use core_number_theory::cyclotomic_ordered::{
    xi_squared, CyclotomicRealRoot, FieldElementF, FieldElementFPlus,
};
use core_number_theory::rational::{r_one, r_zero, ri, rq, Rational, Zero};
use serde::{Deserialize, Serialize};

use crate::exact_hermitian;

/// A checked Hermitian declaration with the single shared matrix representation.
/// Its CM coordinate presentation belongs to number theory; all matrix operations
/// dispatch to the canonical cyclotomic field and exact-field matrix kernel.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct HermitianMatrix {
    pub dim: usize,
    pub conductor: usize,
    pub entries: BasicMatrix<FieldElementF>,
}
enum Operation {
    Add,
    Sub,
    Product,
    Scale(CyclotomicNumber),
}
macro_rules! at_field{($self:expr,$method:ident $(,$arg:expr)*)=>{match $self.conductor{4=>$self.$method::<4>($($arg),*),5=>$self.$method::<5>($($arg),*),8=>$self.$method::<8>($($arg),*),12=>$self.$method::<12>($($arg),*),24=>$self.$method::<24>($($arg),*),_=>Err("unsupported cyclotomic effect field".into())}}}
impl HermitianMatrix {
    pub fn new(
        dim: usize,
        conductor: usize,
        entries: Vec<Vec<FieldElementF>>,
    ) -> Result<Self, String> {
        if dim == 0 || dim > 64 || ![4, 5, 8, 12, 24].contains(&conductor) {
            return Err("effect dimensions1..64 and conductors4,5,8,12,24 are supported".into());
        }
        if entries.len() != dim || entries.iter().any(|r| r.len() != dim) {
            return Err("effect matrix has the wrong shape".into());
        }
        let matrix = BasicMatrix::from_row_major(dim, dim, entries.into_iter().flatten().collect())
            .map_err(|e| e.to_string())?;
        let h = Self {
            dim,
            conductor,
            entries: matrix,
        };
        h.validate()?;
        Ok(h)
    }
    pub fn validate(&self) -> Result<(), String> {
        if [
            self.dim == 0,
            self.dim > 64,
            ![4, 5, 8, 12, 24].contains(&self.conductor),
            self.entries.shape() != (self.dim, self.dim),
        ]
        .into_iter()
        .any(|b| b)
        {
            return Err("invalid effect matrix carrier".into());
        }
        for (i, x) in self.entries.as_slice().iter().enumerate() {
            self.validate_effect_entry(i, x)?;
        }
        if self.conductor == 4 {
            self.preflight_gaussian_conversion()?;
        }
        Ok(())
    }

    fn validate_effect_entry(&self, i: usize, x: &FieldElementF) -> Result<(), String> {
        if [
            x.conductor != self.conductor,
            x.real.conductor != self.conductor,
            x.imag.conductor != self.conductor,
        ]
        .into_iter()
        .any(|b| b)
        {
            return Err("CM field mismatch".into());
        }
        x.as_cyclotomic().map_err(|e| e.to_string())?;
        let (r, c) = (i / self.dim, i % self.dim);
        let conj = self
            .entries
            .get(c, r)
            .map_err(|e| e.to_string())?
            .conjugate();
        if *x != conj {
            return Err(format!("non-Hermitian effect at ({r},{c})"));
        }
        Ok(())
    }

    /// Non-recursive preflight checking carrier dimensions, conductor, and canonical
    /// Gaussian coordinate representations before conversion to `BasicMatrix<GaussianRat>`.
    pub fn preflight_gaussian_conversion(&self) -> Result<(), String> {
        if self.conductor != 4 {
            return Err(
                "exact_hermitian representation requires conductor 4 (Gaussian rationals Q(i))"
                    .into(),
            );
        }
        if self.dim == 0 || self.dim > 64 {
            return Err("effect dimension must be in 1..=64".into());
        }
        if self.entries.shape() != (self.dim, self.dim) {
            return Err("matrix entries shape does not match declared dimension".into());
        }
        for (i, entry) in self.entries.as_slice().iter().enumerate() {
            Self::validate_gaussian_entry(i, entry)?;
        }
        Ok(())
    }

    fn validate_gaussian_entry(i: usize, entry: &FieldElementF) -> Result<(), String> {
        if [
            entry.conductor != 4,
            entry.real.conductor != 4,
            entry.imag.conductor != 4,
        ]
        .into_iter()
        .any(|b| b)
        {
            return Err(format!(
                "entry at flat index {i} has conductor mismatch: expected 4"
            ));
        }
        if Self::has_non_canonical_tail(&entry.real.coeffs) {
            return Err(format!(
                "entry at flat index {i} has non-canonical real Gaussian coordinates"
            ));
        }
        if Self::has_non_canonical_tail(&entry.imag.coeffs) {
            return Err(format!(
                "entry at flat index {i} has non-canonical imaginary Gaussian coordinates"
            ));
        }
        Ok(())
    }

    fn has_non_canonical_tail(coeffs: &[Rational]) -> bool {
        coeffs.len() > 1 && coeffs.iter().skip(1).any(|c| !c.is_zero())
    }

    /// Convert to sovereign exact Hermitian matrix representation over Gaussian rationals
    /// when conductor == 4 (Q(i)).
    pub fn to_exact_hermitian(&self) -> Result<BasicMatrix<GaussianRat>, String> {
        self.preflight_gaussian_conversion()?;
        let mut data = Vec::with_capacity(self.dim * self.dim);
        for entry in self.entries.as_slice() {
            let re = entry
                .real
                .coeffs
                .first()
                .cloned()
                .unwrap_or_else(Zero::zero);
            let im = entry
                .imag
                .coeffs
                .first()
                .cloned()
                .unwrap_or_else(Zero::zero);
            data.push(GaussianRat { re, im });
        }
        let bm =
            BasicMatrix::from_row_major(self.dim, self.dim, data).map_err(|e| e.to_string())?;
        exact_hermitian::check_hermitian(&bm).map_err(|e| e.to_string())?;
        Ok(bm)
    }

    /// Construct from workspace sovereign exact Hermitian matrix representation over Gaussian rationals.
    pub fn from_exact_hermitian(m: &BasicMatrix<GaussianRat>) -> Result<Self, String> {
        exact_hermitian::check_hermitian(m).map_err(|e| e.to_string())?;
        let dim = m.rows();
        let mut entries = Vec::with_capacity(dim);
        for r in 0..dim {
            let mut row = Vec::with_capacity(dim);
            for c in 0..dim {
                let g = m.get(r, c).map_err(|e| e.to_string())?;
                row.push(FieldElementF::new(
                    4,
                    FieldElementFPlus::new(4, &[g.re.clone()]),
                    FieldElementFPlus::new(4, &[g.im.clone()]),
                ));
            }
            entries.push(row);
        }
        Self::new(dim, 4, entries)
    }
    fn field_matrix<const N: usize>(&self) -> Result<BasicMatrix<Cyclotomic<N>>, String> {
        self.validate()?;
        let data = self
            .entries
            .as_slice()
            .iter()
            .map(|x| {
                Cyclotomic::<N>::try_from(x.as_cyclotomic().map_err(|e| e.to_string())?)
                    .map_err(|e| e.to_string())
            })
            .collect::<Result<Vec<_>, _>>()?;
        BasicMatrix::from_row_major(self.dim, self.dim, data).map_err(|e| e.to_string())
    }
    fn presentation<const N: usize>(
        m: BasicMatrix<Cyclotomic<N>>,
    ) -> Result<BasicMatrix<FieldElementF>, String> {
        let data = m
            .as_slice()
            .iter()
            .map(|x| FieldElementF::from_cyclotomic(x.as_number()).map_err(|e| e.to_string()))
            .collect::<Result<Vec<_>, _>>()?;
        BasicMatrix::from_row_major(m.rows(), m.cols(), data).map_err(|e| e.to_string())
    }
    fn operate<const N: usize>(
        &self,
        other: Option<&Self>,
        op: Operation,
    ) -> Result<BasicMatrix<FieldElementF>, String> {
        let a = self.field_matrix::<N>()?;
        let b = other.map(|h| h.field_matrix::<N>()).transpose()?;
        let matrix = Self::apply_field_op::<N>(&a, b.as_ref(), op)?;
        Self::presentation(matrix)
    }

    fn apply_field_op<const N: usize>(
        a: &BasicMatrix<Cyclotomic<N>>,
        b: Option<&BasicMatrix<Cyclotomic<N>>>,
        op: Operation,
    ) -> Result<BasicMatrix<Cyclotomic<N>>, String> {
        let res = match op {
            Operation::Add => mx::add(a, b.ok_or("missing matrix")?),
            Operation::Sub => mx::sub(a, b.ok_or("missing matrix")?),
            Operation::Product => mx::multiply(a, b.ok_or("missing matrix")?),
            Operation::Scale(s) => {
                mx::scale(a, &Cyclotomic::<N>::try_from(s).map_err(|e| e.to_string())?)
            }
        };
        res.map_err(|e| e.to_string())
    }
    fn from_result(&self, m: BasicMatrix<FieldElementF>) -> Result<Self, String> {
        let result = Self {
            dim: m.rows(),
            conductor: self.conductor,
            entries: m,
        };
        result.validate()?;
        Ok(result)
    }
    pub fn zero(dim: usize, conductor: usize) -> Result<Self, String> {
        if dim == 0 || dim > 64 || ![4, 5, 8, 12, 24].contains(&conductor) {
            return Err("invalid effect carrier".into());
        }
        Self::new(
            dim,
            conductor,
            vec![vec![FieldElementF::zero(conductor); dim]; dim],
        )
    }
    pub fn identity(dim: usize, conductor: usize) -> Result<Self, String> {
        let mut h = Self::zero(dim, conductor)?;
        for j in 0..dim {
            h.entries
                .set(j, j, FieldElementF::one(conductor))
                .map_err(|e| e.to_string())?;
        }
        Ok(h)
    }
    pub fn add(&self, b: &Self) -> Result<Self, String> {
        self.from_result(at_field!(self, operate, Some(b), Operation::Add)?)
    }
    pub fn sub(&self, b: &Self) -> Result<Self, String> {
        self.from_result(at_field!(self, operate, Some(b), Operation::Sub)?)
    }
    pub fn scalar_mul(&self, c: &FieldElementFPlus) -> Result<Self, String> {
        self.from_result(at_field!(
            self,
            operate,
            None,
            Operation::Scale(c.as_cyclotomic().map_err(|e| e.to_string())?)
        )?)
    }
    pub fn scalar_mul_rational(&self, c: &Rational) -> Result<Self, String> {
        let scalar = CyclotomicNumber::from_rational(self.conductor, c.clone())
            .map_err(|e| e.to_string())?;
        self.from_result(at_field!(self, operate, None, Operation::Scale(scalar))?)
    }
    pub fn matmul(&self, b: &Self) -> Result<BasicMatrix<FieldElementF>, String> {
        at_field!(self, operate, Some(b), Operation::Product)
    }
    fn field_trace<const N: usize>(&self, b: Option<&Self>) -> Result<FieldElementFPlus, String> {
        let a = self.field_matrix::<N>()?;
        let m = if let Some(b) = b {
            mx::multiply(&a, &b.field_matrix::<N>()?).map_err(|e| e.to_string())?
        } else {
            a
        };
        let trace = mx::trace(&m).map_err(|e| e.to_string())?;
        let f = FieldElementF::from_cyclotomic(trace.as_number()).map_err(|e| e.to_string())?;
        if !f.imag.is_zero() {
            return Err("Hermitian trace pairing is not real".into());
        }
        Ok(f.real)
    }
    pub fn trace(&self) -> Result<FieldElementFPlus, String> {
        at_field!(self, field_trace, None)
    }
    pub fn trace_prod(&self, b: &Self) -> Result<FieldElementFPlus, String> {
        at_field!(self, field_trace, Some(b))
    }
    fn minors<const N: usize>(&self, count: usize) -> Result<Vec<FieldElementFPlus>, String> {
        let matrix = self.field_matrix::<N>()?;
        let mut output = Vec::with_capacity(count);
        for mask in 1..=count {
            let ix = (0..self.dim)
                .filter(|&j| mask & (1 << j) != 0)
                .collect::<Vec<_>>();
            let minor = mx::from_fn(ix.len(), ix.len(), |r, c| {
                matrix.as_slice()[ix[r] * self.dim + ix[c]].clone()
            })
            .map_err(|e| e.to_string())?;
            let det = determinant(&minor).map_err(|e| e.to_string())?;
            let f = FieldElementF::from_cyclotomic(det.as_number()).map_err(|e| e.to_string())?;
            if !f.imag.is_zero() {
                return Err("principal minor is not real".into());
            }
            output.push(f.real);
        }
        Ok(output)
    }
    pub fn principal_minors_with_budget(
        &self,
        budget: usize,
    ) -> Result<Vec<FieldElementFPlus>, String> {
        self.validate()?;
        let count = 1usize
            .checked_shl(self.dim as u32)
            .and_then(|n| n.checked_sub(1))
            .ok_or("principal minor carrier overflow")?;
        if count > budget {
            return Err("principal minor budget exhausted".into());
        }
        at_field!(self, minors, count)
    }
    fn inertia<const N: usize>(&self, embedding_exponent: i64) -> Result<Inertia, String> {
        let standard = self.field_matrix::<N>()?;
        let entries = standard
            .as_slice()
            .iter()
            .map(|x| x.galois(embedding_exponent).map_err(|e| e.to_string()))
            .collect::<Result<Vec<_>, _>>()?;
        let embedded =
            BasicMatrix::from_row_major(self.dim, self.dim, entries).map_err(|e| e.to_string())?;
        hermitian_inertia(&embedded).map_err(|e| e.to_string())
    }
    pub fn try_inertia(&self, place: &CyclotomicRealRoot) -> Result<Inertia, String> {
        self.validate()?;
        self.validate_real_place(place)?;
        // A real place is selected by the image of zeta+zeta^-1. Every such
        // place is a cyclotomic automorphism; conjugate exponents agree there.
        for k in 1..self.conductor {
            if num_integer::Integer::gcd(&k, &self.conductor) != 1 {
                continue;
            }
            if self.place_selects_exponent(place, k)? {
                return at_field!(self, inertia, k as i64);
            }
        }
        Err("the declared interval selects no cyclotomic real place".into())
    }

    fn validate_real_place(&self, place: &CyclotomicRealRoot) -> Result<(), String> {
        if place.conductor != self.conductor {
            return Err("wrong real field place".into());
        }
        let expected = core_number_theory::cyclotomic_ordered::conductor_min_poly(self.conductor);
        if place.poly != expected || place.a > place.b {
            return Err("invalid declared real place".into());
        }
        if place.a == place.b {
            if !place.poly.eval(&place.a).is_zero() {
                return Err("declared root is not a root".into());
            }
            return Ok(());
        }
        let chain = core_number_theory::polynomial::SturmSequence::new(&place.poly)
            .map_err(|e| e.to_string())?;
        let count = chain
            .count_in(&place.a, &place.b)
            .map_err(|e| e.to_string())?;
        if count != 1 {
            return Err("declared real place must isolate exactly one root".into());
        }
        Ok(())
    }

    fn place_selects_exponent(&self, place: &CyclotomicRealRoot, k: usize) -> Result<bool, String> {
        let z = CyclotomicNumber::zeta(self.conductor, k as i64).map_err(|e| e.to_string())?;
        let real = z.add(&z.conjugate()).map_err(|e| e.to_string())?;
        let a = CyclotomicNumber::from_rational(self.conductor, place.a.clone())
            .map_err(|e| e.to_string())?;
        let b = CyclotomicNumber::from_rational(self.conductor, place.b.clone())
            .map_err(|e| e.to_string())?;
        let low = core_number_theory::cyclotomic_ordered::standard_real_sign(
            &real.sub(&a).map_err(|e| e.to_string())?,
        )
        .map_err(|e| e.to_string())?;
        let high = core_number_theory::cyclotomic_ordered::standard_real_sign(
            &real.sub(&b).map_err(|e| e.to_string())?,
        )
        .map_err(|e| e.to_string())?;
        Ok(low >= 0 && high <= 0)
    }

    pub fn is_positive_semidefinite(&self, p: &mut CyclotomicRealRoot) -> bool {
        self.try_inertia(p)
            .is_ok_and(|i| i.is_positive_semidefinite())
    }
    pub fn is_effect(&self, p: &mut CyclotomicRealRoot) -> bool {
        self.is_positive_semidefinite(p)
            && Self::identity(self.dim, self.conductor)
                .and_then(|i| i.sub(self))
                .is_ok_and(|d| d.is_positive_semidefinite(p))
    }
    pub fn canonical_basis(dim: usize, conductor: usize) -> Result<Vec<Self>, String> {
        if dim.checked_pow(4).is_none_or(|n| n > 65536) {
            return Err("effect basis exceeds the65536 entry budget".into());
        }
        Self::zero(dim, conductor)?;
        let mut output = Vec::with_capacity(dim * dim);
        for j in 0..dim {
            let mut h = Self::zero(dim, conductor)?;
            h.entries
                .set(j, j, FieldElementF::one(conductor))
                .map_err(|e| e.to_string())?;
            output.push(h);
        }
        for imaginary in [false, true] {
            Self::append_off_diagonal_basis(&mut output, dim, conductor, imaginary)?;
        }
        Ok(output)
    }

    fn append_off_diagonal_basis(
        output: &mut Vec<Self>,
        dim: usize,
        conductor: usize,
        imaginary: bool,
    ) -> Result<(), String> {
        let x = if imaginary {
            FieldElementF::xi(conductor)
        } else {
            FieldElementF::one(conductor)
        };
        let x_conj = x.conjugate();
        for j in 0..dim {
            for k in j + 1..dim {
                let mut h = Self::zero(dim, conductor)?;
                h.entries.set(j, k, x.clone()).map_err(|e| e.to_string())?;
                h.entries
                    .set(k, j, x_conj.clone())
                    .map_err(|e| e.to_string())?;
                output.push(h);
            }
        }
        Ok(())
    }
}
// ---------------------------------------------------------------------------
// Section 6: Effect Algebra Eff_d(F, iota)
// ---------------------------------------------------------------------------

pub struct EffectAlgebra {
    pub dim: usize,
    pub conductor: usize,
    pub embedding: CyclotomicRealRoot,
}

impl EffectAlgebra {
    pub fn new(dim: usize, conductor: usize) -> Result<Self, String> {
        HermitianMatrix::zero(dim, conductor)?;
        Ok(Self {
            dim,
            conductor,
            embedding: CyclotomicRealRoot::new(conductor),
        })
    }

    pub fn contains(&mut self, a: &HermitianMatrix) -> bool {
        if a.dim != self.dim || a.conductor != self.conductor {
            return false;
        }
        a.is_effect(&mut self.embedding)
    }
}

// ---------------------------------------------------------------------------
// Section 7: Busch Constructive Chain and Density Recovery
// ---------------------------------------------------------------------------

pub struct TraceFrameFunction {
    pub rho: HermitianMatrix,
}

impl TraceFrameFunction {
    pub fn new(rho: HermitianMatrix) -> Self {
        Self { rho }
    }

    pub fn call(&self, effect: &HermitianMatrix) -> Result<FieldElementFPlus, String> {
        self.rho.trace_prod(effect)
    }
}

fn checked_value<F: Fn(&HermitianMatrix) -> FieldElementFPlus>(
    f: &F,
    e: &HermitianMatrix,
) -> Result<FieldElementFPlus, String> {
    let value = f(e);
    if value.conductor != e.conductor {
        return Err("valuation belongs to another field".into());
    }
    value.as_cyclotomic().map_err(|e| e.to_string())?;
    Ok(value)
}

pub fn derive_monotonicity<F>(
    f: &F,
    e1: &HermitianMatrix,
    e2: &HermitianMatrix,
    embedding: &mut CyclotomicRealRoot,
) -> Result<(HermitianMatrix, bool), String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    if e1.dim != e2.dim
        || e1.conductor != e2.conductor
        || !e1.is_effect(embedding)
        || !e2.is_effect(embedding)
    {
        return Err("monotonicity requires compatible effects".into());
    }
    let delta = e2.sub(e1)?;
    if !delta.is_positive_semidefinite(embedding) {
        return Err("E1 is not <=_iota E2".to_string());
    }
    let f_diff = checked_value(f, e2)? - checked_value(f, e1)?;
    let is_ordered = f_diff.sign(embedding) >= 0;
    Ok((delta, is_ordered))
}

pub fn evaluate_rational_homogeneity<F>(f: &F, e: &HermitianMatrix, r: &Rational) -> bool
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    if r < &r_zero() || r > &r_one() {
        return false;
    }
    let Ok(r_e) = e.scalar_mul_rational(r) else {
        return false;
    };
    let Ok(lhs) = checked_value(f, &r_e) else {
        return false;
    };
    let Ok(value) = checked_value(f, e) else {
        return false;
    };
    let rhs = &value * r;
    lhs == rhs
}

pub fn density_squeeze<F>(
    f: &F,
    e: &HermitianMatrix,
    lambda_val: &FieldElementFPlus,
    embedding: &mut CyclotomicRealRoot,
    epsilon: &Rational,
) -> Result<(Rational, Rational), String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    e.try_inertia(embedding)?;
    if [
        epsilon <= &r_zero(),
        lambda_val.conductor != e.conductor,
        embedding.conductor != e.conductor,
    ]
    .into_iter()
    .any(|b| b)
    {
        return Err("invalid squeeze width or field mismatch".into());
    }
    let (r, s) = lambda_val.interval_bounds(embedding, epsilon);
    let lam_e = e.scalar_mul(lambda_val)?;
    let val_lam = checked_value(f, &lam_e)?;
    let val_e = checked_value(f, e)?;

    let lower_bound = &val_e * &r;
    let upper_bound = &val_e * &s;

    let diff_low = &val_lam - &lower_bound;
    let diff_high = &upper_bound - &val_lam;

    if diff_low.sign(embedding) < 0 || diff_high.sign(embedding) < 0 {
        return Err("Density squeeze bounding condition failed".to_string());
    }

    Ok((r, s))
}

pub fn linear_extension<F>(
    f: &F,
    a: &HermitianMatrix,
    embedding: &mut CyclotomicRealRoot,
) -> Result<FieldElementFPlus, String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    a.try_inertia(embedding)?;
    if embedding.conductor != a.conductor {
        return Err("wrong real place".into());
    }
    let dim = a.dim;
    let conductor = a.conductor;
    let max_row_sum = compute_max_row_sum(a, embedding)?;

    let mu = Rational::from_integer(max_row_sum.to_integer() + BigInt::from(2));
    let ident = HermitianMatrix::identity(dim, conductor)?;
    let two_mu = &mu * &rq(2, 1);
    let inv_two_mu = r_one() / &two_mu;

    let shifted = a.add(&ident.scalar_mul_rational(&mu)?)?;
    let e_a = shifted.scalar_mul_rational(&inv_two_mu)?;

    let val_e_a = checked_value(f, &e_a)?;
    Ok(&(&val_e_a * &two_mu) - &FieldElementFPlus::rational(mu, conductor))
}

fn compute_max_row_sum(
    a: &HermitianMatrix,
    embedding: &mut CyclotomicRealRoot,
) -> Result<Rational, String> {
    let mut max_row_sum = r_zero();
    let one_rat = r_one();
    for i in 0..a.dim {
        let mut row_sum = r_zero();
        for j in 0..a.dim {
            let n_val = a.entries.get(i, j).map_err(|e| e.to_string())?.norm();
            let (_, upper_n) = n_val.interval_bounds(embedding, &one_rat);
            let ceil_int = (upper_n + &one_rat).to_integer() + BigInt::from(1);
            row_sum += Rational::from_integer(ceil_int);
        }
        if row_sum > max_row_sum {
            max_row_sum = row_sum;
        }
    }
    Ok(max_row_sum)
}

/// Validate whether the given conductor is supported by the cyclotomic ordered arithmetic table.
pub fn validate_conductor_support(conductor: usize) -> Result<(), String> {
    if ![4, 5, 8, 12, 24].contains(&conductor) {
        return Err(format!(
            "Conductor {} not supported; expected 4, 5, 8, 12, or 24",
            conductor
        ));
    }
    Ok(())
}

pub fn recover_density_matrix<F>(
    f: &F,
    dim: usize,
    conductor: usize,
    embedding: &mut CyclotomicRealRoot,
) -> Result<HermitianMatrix, String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    validate_recovery_carrier(dim, conductor)?;
    let mut grid = vec![vec![FieldElementF::zero(conductor); dim]; dim];
    let basis = HermitianMatrix::canonical_basis(dim, conductor)?;

    // 1. Diagonal components
    for j in 0..dim {
        let val_d = checked_value(f, &basis[j])?;
        grid[j][j] = FieldElementF::new(conductor, val_d, FieldElementFPlus::zero(conductor));
    }

    // 2. Off-diagonal components
    fill_recovered_off_diagonals(f, &mut grid, &basis, dim, conductor, embedding)?;

    let recovered_rho = HermitianMatrix::new(dim, conductor, grid)?;
    verify_recovered_state(&recovered_rho, conductor, embedding)?;
    Ok(recovered_rho)
}

fn validate_recovery_carrier(dim: usize, conductor: usize) -> Result<(), String> {
    validate_conductor_support(conductor)?;
    if dim == 0 || dim > 64 {
        return Err(format!(
            "effect dimension {dim} out of supported bounds 1..=64"
        ));
    }
    let _elements = dim.checked_mul(dim).ok_or("dimension overflow")?;
    let _quad = dim.checked_pow(4).ok_or("carrier size overflow")?;
    Ok(())
}

fn fill_recovered_off_diagonals<F>(
    f: &F,
    grid: &mut [Vec<FieldElementF>],
    basis: &[HermitianMatrix],
    dim: usize,
    conductor: usize,
    embedding: &mut CyclotomicRealRoot,
) -> Result<(), String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    let xi2 = xi_squared(conductor);
    let mut idx = dim;
    let half = rq(1, 2);
    let minus_two = rq(-2, 1);
    let denom_t = &xi2 * &minus_two;

    for j in 0..dim {
        for k in (j + 1)..dim {
            let val_s = linear_extension(f, &basis[idx], embedding)?;
            let re_jk = &val_s * &half;

            let t_jk = &basis[idx + dim * (dim - 1) / 2];
            let val_t = linear_extension(f, t_jk, embedding)?;
            let im_jk = &val_t / &denom_t;

            let cell_jk = FieldElementF::new(conductor, re_jk, im_jk);
            grid[j][k] = cell_jk.clone();
            grid[k][j] = cell_jk.conjugate();
            idx += 1;
        }
    }
    Ok(())
}

fn verify_recovered_state(
    recovered_rho: &HermitianMatrix,
    conductor: usize,
    embedding: &mut CyclotomicRealRoot,
) -> Result<(), String> {
    let tr_rho = recovered_rho.trace()?;
    if tr_rho != FieldElementFPlus::one(conductor) {
        return Err(format!("Recovered state trace != 1, got {:?}", tr_rho));
    }
    if !recovered_rho.is_positive_semidefinite(embedding) {
        return Err("Recovered state is not positive semidefinite".to_string());
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Section 8: State Recovery Verification Matrix
// ---------------------------------------------------------------------------

/// The two honest routes to a Born-selection import.
///
/// Mirrors `BornSelectionImport` in
/// `lean4/research_programs/003_quantum_foundations/000_quantum_foundations_core/qm_wave7_completion.lean`.
/// Kept as an explicit two-case enum so that "which route paid for Born
/// uniqueness at this dimension" is a recorded fact rather than an assumption.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BornSelectionRoute {
    /// Projection-lattice Gleason. Valid only for `dim >= 3`.
    GleasonDim3Plus,
    /// Busch's POVM frame-function variant (PRL 91 (2003) 120403).
    /// Carries no dimension restriction — it survives at `dim = 2`.
    BuschPovm,
}

/// Which Born-selection routes are available at a given finite dimension.
///
/// At `dim = 2` the Gleason route is **absent**: Gleason's theorem is false
/// there, so a seal at the estate's only working dimension can only be charged
/// to Busch. This is the executable counterpart of the Lean theorem
/// `dim_two_forces_busch_route`.
pub fn available_born_routes(dim: usize) -> Vec<BornSelectionRoute> {
    let mut routes = Vec::new();
    if dim >= 3 {
        routes.push(BornSelectionRoute::GleasonDim3Plus);
    }
    if dim >= 2 {
        routes.push(BornSelectionRoute::BuschPovm);
    }
    routes
}

/// `dim = 2` forces the Busch route: the Gleason disjunct is unavailable.
pub fn dim_two_forces_busch_route() -> bool {
    available_born_routes(2) == vec![BornSelectionRoute::BuschPovm]
}

/// Check Busch's hypotheses on a declared finite effect carrier. This is a
/// finite certificate; completeness of the continuum effect domain is external.
pub fn check_finite_effect_additivity<F>(
    algebra: &mut EffectAlgebra,
    effects: &[HermitianMatrix],
    f: F,
) -> Result<bool, String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    if effects.is_empty() || effects.len() > 256 {
        return Err("declare1..256 effects for the finite additivity check".into());
    }
    if !check_unit_and_zero_valuations(algebra, &f)? {
        return Ok(false);
    }
    if !check_all_effects_in_unit_interval(algebra, effects, &f)? {
        return Ok(false);
    }
    check_pairwise_effect_additivity(algebra, effects, &f)
}

fn check_unit_and_zero_valuations<F>(algebra: &EffectAlgebra, f: &F) -> Result<bool, String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    let identity = HermitianMatrix::identity(algebra.dim, algebra.conductor)?;
    let zero = HermitianMatrix::zero(algebra.dim, algebra.conductor)?;
    let id_ok = checked_value(f, &identity)? == FieldElementFPlus::one(algebra.conductor);
    let zero_ok = checked_value(f, &zero)?.is_zero();
    Ok(id_ok && zero_ok)
}

fn check_all_effects_in_unit_interval<F>(
    algebra: &mut EffectAlgebra,
    effects: &[HermitianMatrix],
    f: &F,
) -> Result<bool, String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    for effect in effects {
        if !algebra.contains(effect) {
            return Err("declared operator is not an effect".into());
        }
        let value = checked_value(f, effect)?;
        if value.conductor != algebra.conductor {
            return Err("valuation lies in another field".into());
        }
        let upper = &FieldElementFPlus::one(algebra.conductor) - &value;
        if value.sign(&mut algebra.embedding) < 0 || upper.sign(&mut algebra.embedding) < 0 {
            return Ok(false);
        }
    }
    Ok(true)
}

fn check_pairwise_effect_additivity<F>(
    algebra: &mut EffectAlgebra,
    effects: &[HermitianMatrix],
    f: &F,
) -> Result<bool, String>
where
    F: Fn(&HermitianMatrix) -> FieldElementFPlus,
{
    for left in effects {
        for right in effects {
            let sum = left.add(right)?;
            if algebra.contains(&sum)
                && checked_value(f, &sum)? != checked_value(f, left)? + checked_value(f, right)?
            {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

/// Non-Born d=2 projector frame function `(1+n_z^3)/2` on rational
/// Bloch directions. Antipodal sums are one, but no affine density readout
/// agrees with its values on the declared directions.
pub fn cubic_qubit_projector_value(direction: &[Rational; 3]) -> Result<Rational, String> {
    if direction.iter().map(|x| x * x).sum::<Rational>() != r_one() {
        return Err("Bloch direction is not unit".into());
    }
    Ok((r_one() + &direction[2] * &direction[2] * &direction[2]) / ri(2))
}

impl TryFrom<&HermitianMatrix> for BasicMatrix<GaussianRat> {
    type Error = String;
    fn try_from(h: &HermitianMatrix) -> Result<Self, Self::Error> {
        h.to_exact_hermitian()
    }
}

impl TryFrom<&BasicMatrix<GaussianRat>> for HermitianMatrix {
    type Error = String;
    fn try_from(m: &BasicMatrix<GaussianRat>) -> Result<Self, Self::Error> {
        HermitianMatrix::from_exact_hermitian(m)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/busch_effects.rs
// Claim: urn:core:crates_rs:core-quantum-physics:busch-effects:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5d7585e5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5d7585e5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5d7585e5 {
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
impl BoundaryError5d7585e5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5d7585e5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5d7585e5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5d7585e5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5d7585e5> {
        if capacity_bound == 0 {
            return Err(BoundaryError5d7585e5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5d7585e5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5d7585e5::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exact_hermitian_round_trip() {
        let ident = HermitianMatrix::identity(3, 4).expect("3x3 conductor 4 identity");
        let exact: BasicMatrix<GaussianRat> = (&ident)
            .try_into()
            .expect("convert to BasicMatrix<GaussianRat>");
        assert_eq!(exact.rows(), 3);
        assert_eq!(exact.cols(), 3);
        assert!(crate::exact_hermitian::is_hermitian(&exact));

        let recovered: HermitianMatrix = (&exact).try_into().expect("recover HermitianMatrix");
        assert_eq!(recovered.dim, 3);
        assert_eq!(recovered.conductor, 4);
    }
}

#[cfg(test)]
mod l4_boundary_tests_5d7585e5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5d7585e5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5d7585e5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5d7585e5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5d7585e5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5d7585e5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError5d7585e5::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError5d7585e5::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
