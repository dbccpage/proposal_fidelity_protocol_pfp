// Bounded reproduction helper: caller supplies the pinned full HTML text.
// No DOM, files, network or runner execution. Entire script is compile-only.
function inspectNormalFormsHtml(text) {
  const lines = text.split(/\r?\n/);
  const script = text.split('<script>')[1].split('</script>')[0];
  let syntax;
  try { new Function(script); syntax = {parsed: true}; }
  catch (error) { syntax = {parsed: false, error_name: error.name, error: error.message}; }
  const cert = new Function(lines.slice(642, 675).join('\n') + ';return runCertLogic;')();
  const fresh = new Function(lines.slice(676, 724).join('\n') + ';return runFreshLogic;')();
  return {
    script_syntax: syntax,
    verified_label_without_proof: cert({certificate_id: 'unbound', verifier_outcome: 'verified'}),
    negative_lag: fresh({packet: {replica_lag_seconds: -1}, observers: [{observer_id: 'o', max_lag_seconds: 0}]}),
    boolean_lag: fresh({packet: {replica_lag_seconds: true}, observers: [{observer_id: 'o', max_lag_seconds: 1}]}),
    refresh_classified_green_by_substring: 'RefreshRequired'.toLowerCase().includes('fresh')
  };
}
