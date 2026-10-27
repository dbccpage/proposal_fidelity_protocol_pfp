from operads.skill_operad.domain.planar import ColoredOp, identity
from operads.skill_operad.domain.evidence import EMPTY, Residual


def test_identity_is_structural_not_a_name():
    op = ColoredOp("f", ("Code",), "Code", lambda x: (x + 1, EMPTY))
    fake = ColoredOp("id_Code", ("Code",), "Code", lambda x: (x * 2, EMPTY))
    assert op.compose(fake)(3)[0] == 7
    assert op.compose(identity("Code"))(3)[0] == 4


def test_residual_count_and_tuple_value_survive_composition():
    f = ColoredOp("f", ("Code", "Code"), "Code", lambda a,b: ((a,b), EMPTY), Residual(obligations=("outer",)))
    g = ColoredOp("g", ("Code",), "Code", lambda x: (x, EMPTY), Residual(obligations=("inner",)))
    value, residual = f.compose(g, identity("Code"))((1,2), (3,4))
    assert value == ((1,2),(3,4))
    assert residual.obligations.count("outer") == 1
    assert residual.obligations.count("inner") == 1


def test_nested_slot_reindexing_and_disjoint_interchange_on_values():
    def pair(name):
        return ColoredOp(name,("Code","Code"),"Code",lambda a,b:((name,a,b),EMPTY))
    def substitute(outer,slot,inner):
        return outer.compose(*(inner if index==slot else identity("Code") for index in range(outer.arity)))
    a,b,c=pair("A"),pair("B"),pair("C")
    for i in range(2):
        for j in range(2):
            left=substitute(substitute(a,i,b),i+j,c)
            right=substitute(a,i,substitute(b,j,c))
            assert left.source_colors==right.source_colors
            assert left(1,2,3,4)==right(1,2,3,4)
    left=substitute(substitute(a,0,b),2,c)
    right=substitute(substitute(a,1,c),0,b)
    assert left(1,2,3,4)==right(1,2,3,4)
    wrong=substitute(substitute(a,1,b),0,c)
    right=substitute(a,1,substitute(b,0,c))
    assert wrong(1,2,3,4)!=right(1,2,3,4)
