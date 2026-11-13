// Verbatim production owner lines 291..353; see source_binding.json.
impl RationalMatrix {
    fn multiply_square_matrix(&self, rhs: &[Vec<Exact>]) -> Vec<Vec<Exact>> {
        let n = self.rows;
        let mut prod = vec![vec![Exact::zero(); n]; n];
        for i in 0..n {
            for j in 0..n {
                let mut sum = Exact::zero();
                for t in 0..n {
                    sum += self.get(i, t) * &rhs[t][j];
                }
                prod[i][j] = sum;
            }
        }
        prod
    }

    fn add_scaled_identity(prod: &[Vec<Exact>], scalar: &Exact) -> Vec<Vec<Exact>> {
        let n = prod.len();
        let mut mk = vec![vec![Exact::zero(); n]; n];
        for i in 0..n {
            for j in 0..n {
                mk[i][j] = if i == j {
                    &prod[i][j] + scalar
                } else {
                    prod[i][j].clone()
                };
            }
        }
        mk
    }

    fn matrix_trace(mat: &[Vec<Exact>]) -> Exact {
        let mut tr = Exact::zero();
        for (i, row) in mat.iter().enumerate() {
            tr += &row[i];
        }
        tr
    }

    /// Exact characteristic polynomial coefficients via Faddeev-LeVerrier over BigRational.
    pub fn char_poly(&self) -> Result<Vec<Exact>, RationalError> {
        if !self.is_square() {
            return Err(RationalError::NotSquare {
                rows: self.rows,
                cols: self.cols,
            });
        }
        let n = self.rows;
        let mut coeffs = vec![Exact::zero(); n + 1];
        coeffs[n] = Exact::one();
        let mut mk = vec![vec![Exact::zero(); n]; n];
        let mut ck = Exact::one();

        for k in 1..=n {
            // M_k = A * M_{k-1} + c_{n-k+1} * I
            let prod = self.multiply_square_matrix(&mk);
            mk = Self::add_scaled_identity(&prod, &ck);
            let am = self.multiply_square_matrix(&mk);
            let tr = Self::matrix_trace(&am);
            ck = -(&tr / Exact::from(num_bigint::BigInt::from(k)));
            coeffs[n - k] = ck.clone();
        }
        Ok(coeffs)
    }
}
