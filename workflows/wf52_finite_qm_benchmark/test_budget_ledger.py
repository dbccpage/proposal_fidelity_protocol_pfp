from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import pytest
from budget_ledger import BudgetError,RunLedger,quote_microusd

HERE=Path(__file__).parent
H='a'*64

@pytest.fixture
def location():
    with tempfile.TemporaryDirectory(dir=HERE) as directory:yield Path(directory)/'ledger.db'

def test_aggregate_cap_is_across_calls(location):
    ledger=RunLedger(location);ledger.start('run',H)
    ledger.reserve('run','a',H,60_000)
    with pytest.raises(BudgetError):ledger.reserve('run','b',H,40_001)
    ledger.reserve('run','b',H,40_000)
    assert ledger.summary('run')['available_microusd']==0
    ledger.close()

def test_crash_reopen_retains_hold_and_identity(location):
    a=RunLedger(location);a.start('run',H);a.reserve('run','a',H,70_000);a.close()
    b=RunLedger(location)
    assert b.summary('run')['held_microusd']==70_000
    with pytest.raises(BudgetError):b.reserve('run','a',H,1)
    with pytest.raises(BudgetError):b.start('run',H)
    b.close()

def test_unknown_cost_blocks_without_releasing(location):
    a=RunLedger(location);a.start('run',H);a.reserve('run','a',H,20_000);a.mark_uncertain('a')
    assert a.summary('run')['held_microusd']==20_000
    with pytest.raises(BudgetError):a.reserve('run','b',H,1)
    a.close()

def test_overrun_persists_actual_before_error(location):
    a=RunLedger(location);a.start('run',H);a.reserve('run','a',H,10_000)
    with pytest.raises(BudgetError):a.settle('a',12_000,H)
    s=a.summary('run');assert s['spent_microusd']==12_000 and s['blocked']
    with pytest.raises(BudgetError):a.settle('a',1,H)
    a.close()

def test_settlement_frees_only_unused_reservation(location):
    a=RunLedger(location);a.start('run',H);a.reserve('run','a',H,90_000);a.settle('a',30_000,H)
    assert a.summary('run')['available_microusd']==70_000
    a.reserve('run','b',H,70_000);a.close()

def test_concurrent_reservation_cannot_oversubscribe(location):
    a=RunLedger(location);a.start('run',H);a.close()
    def attempt(name):
        b=RunLedger(location)
        try:b.reserve('run',name,H,60_000);return True
        except BudgetError:return False
        finally:b.close()
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(attempt,['a','b']))
    assert sorted(results)==[False,True]

def test_exact_quote_rounds_up_and_validates():
    assert quote_microusd(1,1,'0.0001','0.0002')==1
    assert quote_microusd(1000,2000,'1','2','0.001')==6000
    for price in ['NaN','Infinity','-1']:
        with pytest.raises(BudgetError):quote_microusd(1,1,price,'1')
    with pytest.raises(BudgetError):quote_microusd(True,1,'1','1')

def test_cannot_raise_per_run_limit(location):
    a=RunLedger(location)
    with pytest.raises(BudgetError):a.start('run',H,100_001)
    with pytest.raises(BudgetError):a.start('run',H,True)
    a.close()
