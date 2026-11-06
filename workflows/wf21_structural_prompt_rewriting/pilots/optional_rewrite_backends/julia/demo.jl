# Optional local ACSet/DPO reference experiment. No LLM or provider calls.
using Catlab, AlgebraicRewriting, Test

@present SchExactCochain(FreeSchema) begin
  V::Ob
  E::Ob
  src::Hom(E, V)
  tgt::Hom(E, V)
  Scalar::AttrType
  potential::Attr(V, Scalar)
  weight::Attr(E, Scalar)
end
@acset_type ExactCochainGraph(SchExactCochain, index=[:src, :tgt])
const ExactGraph = ExactCochainGraph{Rational{BigInt}}
# Attribute-aware DPO needs the variable-ACSet category explicitly. The
# fixed-type inferred category represents attribute components as `nothing`.
const ExactCategory = ACSetCategory(VarACSetCat(ExactGraph()))

function graph(potentials, sources=Int[], targets=Int[], weights=Rational{BigInt}[])
  g = ExactGraph()
  add_parts!(g, :V, length(potentials); potential=potentials)
  add_parts!(g, :E, length(sources); src=sources, tgt=targets, weight=weights)
  g
end

# Independent edgewise judge; a sum of weights is not a cochain certificate.
function exact_gradient(g)
  all(g[e, :weight] == g[g[e, :tgt], :potential] -
      g[g[e, :src], :potential] for e in parts(g, :E))
end

# Potentials are unique labels in this four-vertex fixture, so an oriented
# endpoint multiset checks its topology without relying on internal indices.
function oriented_edges(g)
  sort([(g[g[e, :src], :potential], g[g[e, :tgt], :potential]) for e in parts(g, :E)])
end

function registered_rewrite(registry, rule_id, match)
  haskey(registry, rule_id) || error("UNREGISTERED_RULE")
  rule = registry[rule_id]
  is_natural(match; cat=ExactCategory) || error("NON_NATURAL_MATCH")
  for kind in (:V, :E)
    images = collect(match[kind])
    length(unique(images)) == length(images) || error("NON_INJECTIVE_MATCH")
  end
  rewrite_match(rule, match; cat=ExactCategory, check=true)
end

q(n) = BigInt(n) // BigInt(1)
left = graph(q.([0, 1]), [1], [2], q.([0]))
interface = graph(q.([0, 1]))
right = graph(q.([0, 1]), [1], [2], q.([1]))
repair = Rule{:DPO}(
  ACSetTransformation(interface, left; V=[1, 2], E=Int[], cat=ExactCategory),
  ACSetTransformation(interface, right; V=[1, 2], E=Int[], cat=ExactCategory);
  monic=true, cat=ExactCategory,
)
registry = Dict("replace-bad-gradient-v001" => repair)
state = graph(q.([0, 1, 3, 7]), [1, 2, 3], [2, 3, 4], q.([0, 2, 4]))
match = ACSetTransformation(left, state; V=[1, 2], E=[1], cat=ExactCategory)
@test !exact_gradient(state)
rewritten = registered_rewrite(registry, "replace-bad-gradient-v001", match)
@test exact_gradient(rewritten)
@test sort(collect(rewritten[:potential])) == q.([0, 1, 3, 7])
@test oriented_edges(rewritten) == oriented_edges(state)
@test nparts(rewritten, :V) == 4 && nparts(rewritten, :E) == 3
@test !exact_gradient(state) # Original mutable ACSet was not rewritten in place.
@test_throws ErrorException registered_rewrite(registry, "invented-rule", match)

# Delete vertex 3 through edge 2 while retaining the unmatched incident edge 3.
# The exact explicit match is natural, but the DPO dangling condition forbids it.
delete_left = graph(q.([1, 3]), [1], [2], q.([2]))
delete_interface = graph(q.([1]))
delete_rule = Rule{:DPO}(
  ACSetTransformation(delete_interface, delete_left; V=[1], E=Int[], cat=ExactCategory),
  ACSetTransformation(delete_interface, delete_interface; V=[1], E=Int[], cat=ExactCategory);
  monic=true, cat=ExactCategory,
)
registry["delete-endpoint-v001"] = delete_rule
bad_match = ACSetTransformation(delete_left, state; V=[2, 3], E=[2], cat=ExactCategory)
@test is_natural(bad_match; cat=ExactCategory)
@test_throws ErrorException registered_rewrite(registry, "delete-endpoint-v001", bad_match)
@test nparts(state, :V) == 4 && nparts(state, :E) == 3

# Equal counts, potentials and an exact gradient do not certify the topology.
rebound = graph(q.([0, 1, 3, 7]), [1, 1, 3], [2, 3, 4], q.([1, 3, 4]))
@test exact_gradient(rebound)
@test sort(collect(rebound[:potential])) == sort(collect(rewritten[:potential]))
@test oriented_edges(rebound) != oriented_edges(state)

println("FIXTURE_VERIFIED: registered explicit DPO rewrite, exact edgewise gradient, dangling refusal")
println("No provider calls; no general confluence or LLM improvement claim.")
