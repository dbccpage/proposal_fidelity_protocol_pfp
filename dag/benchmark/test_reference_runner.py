import hashlib
import json
from pathlib import Path
import tempfile
import pytest
from reference_runner import HERE, OfflineTape, Reply, run

@pytest.fixture
def folder():
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        yield Path(directory) / 'run'

def test_seed_exact_each_call_and_no_key_or_tools(folder):
    provider = OfflineTape(['candidate', 'revised'])
    receipt = run('self_critique', provider, folder, 'case')
    expected = (HERE / 'seed_prompt.txt').read_bytes()
    assert len(provider.requests) == 2
    for request in provider.requests:
        assert request['messages'][1]['content'].encode('utf-8') == expected
        assert request['tools'] == [] and request['retries'] == 0
        assert 'answer_key' not in request
    assert receipt['answer_text'] == 'revised'
    assert receipt['accuracy_score'] is None and receipt['input_tokens'] is None
    assert hashlib.sha256((folder / 'run.json').read_bytes()).hexdigest() == (folder / 'run.sha256').read_text().strip()

def test_unknown_bill_retains_hold_and_prevents_second_call(folder):
    class Unknown(OfflineTape):
        def upper_quote(self, request): return 60_000
        def complete(self, request):
            self.requests.append(request)
            return Reply('candidate', None, None, None)
    p = Unknown([])
    receipt = run('self_critique', p, folder, 'case')
    assert len(p.requests) == 1
    assert receipt['budget']['held_microusd'] == 60_000
    assert receipt['budget']['blocked'] and receipt['status'] == 'incomplete_accounting'

def test_total_cost_gate_blocks_second_dispatch(folder):
    class Costly(OfflineTape):
        def upper_quote(self, request): return 60_000
        def complete(self, request):
            self.requests.append(request)
            return Reply('candidate', 60_000, 100, 10)
    p = Costly([])
    receipt = run('self_critique', p, folder, 'case')
    assert len(p.requests) == 1
    assert receipt['status'] == 'admission_failure'
    assert receipt['budget']['spent_microusd'] == 60_000

def test_timeout_never_retries_and_freezes_failure(folder):
    class Timeout(OfflineTape):
        def upper_quote(self, request): return 10_000
        def complete(self, request):
            self.requests.append(request)
            raise TimeoutError('ambiguous remote completion')
    p = Timeout([])
    receipt = run('self_critique', p, folder, 'case')
    assert len(p.requests) == 1 and receipt['budget']['blocked']
    assert receipt['budget']['held_microusd'] == 10_000
    assert receipt['answer_text'] is None and (folder / 'run.json').exists()

def test_live_and_unsupported_research_plan_refused_before_dispatch(folder):
    p = OfflineTape(['unused']); p.offline = False
    with pytest.raises(ValueError, match='Live provider'):
        run('direct', p, folder, 'case')
    assert p.requests == [] and not folder.exists()
    with pytest.raises(ValueError, match='Unsupported plan'):
        run('R01-I01', OfflineTape([]), folder, 'case')

def test_existing_run_directory_cannot_be_overwritten(folder):
    run('direct', OfflineTape(['first']), folder, 'case')
    with pytest.raises(FileExistsError):
        run('direct', OfflineTape(['replacement']), folder, 'case')
