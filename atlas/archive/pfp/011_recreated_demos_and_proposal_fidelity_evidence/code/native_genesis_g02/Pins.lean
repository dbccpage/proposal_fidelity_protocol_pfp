import CutTheorems

open HigherStructure ResearchPaper011G02

example : cutCensus 5 0 1 = 8 ∧ cutCensus 6 0 1 = 16 ∧
    cutCensus 7 0 1 = 32 ∧ cutCensus 8 0 1 = 64 := C1
example : ∀ n, 2 ≤ n → cutCensus n 0 1 = 2 ^ (n - 2) := C2
example : ∀ n a b, a < n → b < n → a ≠ b → cutCensus n a b = 2 ^ (n - 2) := C3
example : ∀ n a, cutCensus n a a = 0 := equal_pair
example : ∀ n a b, n ≤ a → cutCensus n a b = 0 := first_outside
example : ∀ n a b, a < n → n ≤ b → cutCensus n a b = 2 ^ (n - 1) := second_outside
example : ∀ a b, cutCensus 0 a b = 0 := zero_carrier
example : cutCensus 1 0 0 = 0 ∧ cutCensus 1 0 1 = 1 ∧ cutCensus 1 1 0 = 0 := one_carrier
example : cutCensus 9 0 1 = 128 := C3_at_nine
example : cutCensus 10 0 1 = 256 := C3_at_ten
example : cutCensus 9 3 1 = 128 := relabel_pair
example : cutCensus 3 0 0 ≠ 2 ^ (3 - 2) := poison_equal_pair
example : cutCensus 0 0 1 ≠ 2 ^ (0 - 2) := poison_no_lower_bound
