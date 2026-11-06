"""Send hard-problem packets to Claude Fable 5.1 through the Anthropic API, under hard dollar and token caps.

    python -I -X utf8 dag/pfp/fable_api/run_fable.py --confirm-spend --usd-cap 10 --token-cap 1000000 \
        dag/pfp/fable_api/packets/gleason_gaussian_rational.md dag/pfp/fable_api/packets/mub6_no_quartet_concrete.md

Without --confirm-spend it prints the plan (packet sizes, per-problem caps) and calls only the free token-count endpoint.
Each packet is a Markdown file whose front matter names `node_id` and `context_files`; the context files are appended
verbatim. The caps are split evenly across packets and enforced before every call (worst case = counted input at the input
price + max_tokens at the output price). If a reply stops at max_tokens and budget remains, Fable is asked to continue.
Outputs go to dag/results/<node_id>/runs/<UTC>_fable_api/: request, every turn's text and thinking summary, usage, cost,
and any `-- FILE: lean4/...` blocks extracted to lean/ (for the host to compile; nothing here compiles or trusts them).
"""
import argparse, datetime, json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODEL = 'claude-fable-5-1'
FALLBACK = 'claude-opus-5-5'
PRICE_IN, PRICE_OUT = 10.0 / 1e6, 50.0 / 1e6      # USD per token (dag/pfp/llm_ladder/config.py)
MAX_TOKENS_PER_CALL = 128000   # the API maximum for claude-fable-5-1 (a larger value is rejected with 400)
MAX_TURNS = 4
WRITE_UP = ('Your previous call used its whole output budget on reasoning and wrote no answer. Your reasoning so far is '
            'summarised below. Do not restart the analysis: reason only as much as needed to settle the remaining gaps, '
            'then WRITE THE DELIVERABLE (argument, complete Lean files, WHAT IS PROVED). If something is unfinished, '
            'deliver the largest honest piece and say exactly what is missing.\n\n## Your reasoning so far\n\n')
SYSTEM = ('You are a research mathematician and Lean 4 expert collaborating on a finite, exact formalisation of quantum '
          'mechanics. Be exact and conservative: never claim more than the Lean proves. Follow the deliverable format.')
CONTINUE = 'Continue exactly where you stopped. Do not repeat earlier text.'


def load_env():
    env = {}
    for path in (ROOT / '.env', ROOT.parents[2] / '.env'):
        if path.is_file():
            for line in path.read_text(encoding='utf-8').splitlines():
                if '=' in line and not line.lstrip().startswith('#'):
                    k, v = line.split('=', 1)
                    env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def read_packet(path: Path):
    text = path.read_text(encoding='utf-8')
    m = re.match(r'---\n(.*?)\n---\n(.*)', text, re.S)
    if not m:
        sys.exit('%s: missing front matter' % path)
    meta, body = m.groups()
    node = re.search(r'^node_id:\s*(\S+)', meta, re.M).group(1)
    files = re.findall(r'^\s*-\s*(\S+)', meta, re.M)
    parts = [body.strip(), '\n## Included repository files\n']
    for rel in files:
        parts.append('\n### %s\n```lean\n%s\n```\n' % (rel, (ROOT / rel).read_text(encoding='utf-8')))
    return node, '\n'.join(parts)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def dump(content):
    return [b.model_dump(exclude_none=True) if hasattr(b, 'model_dump') else b for b in content]


def prior_reasoning(node):
    """Thinking summaries of earlier answerless _fable_api runs of this node, oldest first."""
    runs = sorted((ROOT / 'dag' / 'results' / node / 'runs').glob('*_fable_api'))
    parts = []
    for run in runs:
        for f in sorted(run.glob('turn_*_thinking_summary.md')):
            text = f.read_text(encoding='utf-8').strip()
            if text:
                parts.append('### %s/%s\n\n%s' % (run.name, f.name, text))
    return '\n\n'.join(parts)


EFFORT = 'high'


def call(client, messages, max_tokens, use_fallback):
    extra_body = {'output_config': {'effort': EFFORT}}
    headers = {}
    if use_fallback:
        extra_body['fallbacks'] = [{'model': FALLBACK}]
        headers['anthropic-beta'] = 'server-side-fallback-2026-06-01'
    with client.messages.stream(model=MODEL, max_tokens=max_tokens, system=SYSTEM, messages=messages,
                                thinking={'type': 'adaptive', 'display': 'summarized'},
                                extra_body=extra_body, extra_headers=headers) as stream:
        return stream.get_final_message()


def run_packet(client, path, usd_cap, token_cap, confirm):
    node, user = read_packet(path)
    seed = prior_reasoning(node)
    if seed:
        user += ('\n\n## Progress from your earlier attempt on this problem (your own reasoning summary; it wrote no '
                 'answer)\n\nBuild on it rather than starting over.\n\n' + seed)
    messages = [{'role': 'user', 'content': user}]
    counted = client.messages.count_tokens(model=MODEL, system=SYSTEM, messages=messages).input_tokens
    print('%s: packet %d input tokens; caps USD %.2f, tokens %d' % (node, counted, usd_cap, token_cap), flush=True)
    if not confirm:
        return None
    run = ROOT / 'dag' / 'results' / node / 'runs' / (utc() + '_fable_api')
    run.mkdir(parents=True)
    (run / 'request.md').write_text(user, encoding='utf-8')
    spent = tokens = 0.0
    turns, texts, use_fallback, thinking_log = [], [], True, []
    for turn in range(MAX_TURNS):
        counted = client.messages.count_tokens(model=MODEL, system=SYSTEM, messages=messages).input_tokens
        affordable = int((usd_cap - spent - counted * PRICE_IN) / PRICE_OUT)
        max_tokens = min(MAX_TOKENS_PER_CALL, affordable, int(token_cap - tokens - counted))
        if max_tokens < 4000:
            turns.append({'turn': turn, 'stopped': 'cap', 'remaining_usd': round(usd_cap - spent, 4)})
            break
        t0 = time.time()
        try:
            msg = call(client, messages, max_tokens, use_fallback)
        except Exception as error:  # a 400 on the fallback beta: retry once without it
            if use_fallback and 'fallback' in str(error).lower():
                use_fallback = False
                msg = call(client, messages, max_tokens, use_fallback)
            else:
                raise
        u = msg.usage
        cost = (u.input_tokens + (getattr(u, 'cache_creation_input_tokens', 0) or 0)) * PRICE_IN \
            + (getattr(u, 'cache_read_input_tokens', 0) or 0) * PRICE_IN * 0.1 + u.output_tokens * PRICE_OUT
        spent += cost
        tokens += u.input_tokens + u.output_tokens
        text = ''.join(b.text for b in msg.content if b.type == 'text')
        thinking = '\n'.join(getattr(b, 'thinking', '') or '' for b in msg.content if b.type == 'thinking')
        texts.append(text)
        (run / ('turn_%d.md' % turn)).write_text(text, encoding='utf-8')
        (run / ('turn_%d_thinking_summary.md' % turn)).write_text(thinking, encoding='utf-8')
        turns.append({'turn': turn, 'model': msg.model, 'stop_reason': msg.stop_reason, 'max_tokens': max_tokens,
                      'input_tokens': u.input_tokens, 'output_tokens': u.output_tokens, 'cost_usd': round(cost, 5),
                      'seconds': round(time.time() - t0, 1), 'fallback_enabled': use_fallback})
        print('  turn %d: %s, out %d tok, $%.4f (total $%.4f)' % (turn, msg.stop_reason, u.output_tokens, cost, spent), flush=True)
        if msg.stop_reason != 'max_tokens':
            break
        if text.strip():
            # the written answer was cut off: continue it
            messages += [{'role': 'assistant', 'content': dump(msg.content)}, {'role': 'user', 'content': CONTINUE}]
        else:
            # thinking only: a continuation of a thinking-only turn is refused, so start a fresh write-up request
            summaries = '\n\n'.join(t for t in thinking_log + [thinking] if t.strip())
            messages = [{'role': 'user', 'content': user + '\n\n' + WRITE_UP + summaries}]
        thinking_log.append(thinking)
    answer = '\n'.join(texts)
    (run / 'answer.md').write_text(answer, encoding='utf-8')
    lean_dir = run / 'lean'
    files = re.findall(r'```lean\s*\n--\s*FILE:\s*(lean4/[\w/]+\.lean)\s*\n(.*?)```', answer, re.S)
    for name, body in files:
        target = lean_dir / Path(name).name
        target.parent.mkdir(exist_ok=True)
        target.write_text(body, encoding='utf-8')
    receipt = {'schema_id': 'omega.pfp.fable-api-run.v1', 'authority_effect': 'None', 'node_id': node, 'model': MODEL,
               'packet': str(path.relative_to(ROOT)).replace('\\', '/'), 'usd_cap': usd_cap, 'token_cap': token_cap,
               'spend_usd': round(spent, 5), 'tokens': int(tokens), 'turns': turns,
               'lean_files_extracted': [n for n, _ in files], 'host_verdict': 'not_yet_compiled'}
    (run / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print('  -> %s (%d Lean file(s)), spend $%.4f' % (run.relative_to(ROOT), len(files), spent), flush=True)
    return spent, tokens


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('packets', nargs='+')
    ap.add_argument('--usd-cap', type=float, default=10.0)
    ap.add_argument('--token-cap', type=int, default=1_000_000)
    ap.add_argument('--confirm-spend', action='store_true')
    args = ap.parse_args()
    import anthropic
    key = load_env().get('ANTHROPIC_API_KEY')
    if not key:
        sys.exit('ANTHROPIC_API_KEY not found in .env')
    client = anthropic.Anthropic(api_key=key, timeout=3600)
    n = len(args.packets)
    total_usd = total_tok = 0.0
    for i, p in enumerate(args.packets):
        usd = (args.usd_cap - total_usd) / (n - i)       # unspent budget rolls forward
        tok = (args.token_cap - total_tok) / (n - i)
        result = run_packet(client, ROOT / p, usd, tok, args.confirm_spend)
        if result:
            total_usd += result[0]
            total_tok += result[1]
    print('total spend $%.4f, tokens %d' % (total_usd, total_tok) if args.confirm_spend else
          'DRY RUN: only the free token-count endpoint was called. Add --confirm-spend to run.')


if __name__ == '__main__':
    main()
