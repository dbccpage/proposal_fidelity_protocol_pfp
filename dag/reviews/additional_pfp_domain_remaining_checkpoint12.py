import sys
sys.dont_write_bytecode=True
import additional_pfp_domain_remaining_audit as a
rows=[
('key.py',82,'Key normalizes surrounding whitespace and restricts128 characters; equality/hash distinguish exact runtime types despite polymorphic wording. WireKey here is a nominal string wrapper distinct from the enum in wire_key.py; ContextKey only marks a category.'),
('key_type.py',38,'Finite label enums and a KeyType alias. Wire names encode field spelling, not packet schema completeness or verification.'),
('media_type.py',64,'Admission only requires a stripped lowercased string containing slash, not the MIME grammar. Lowercasing entire parameters can alter case-sensitive parameter values. Named constructors provide conventional fixed values; no content sniffing/decoding or authority is performed.'),
('patch.py',66,'PatchText enforces a UTF8 byte budget and retains exact text for counts/digests; it never parses unified diff or checks applicability, path ownership or semantics. Empty/arbitrary text is admitted. Runtime hash is nominal equality support, separate from computed SHA256.'),
('path_manifest.py',51,'Normalizes sorted duplicate-free syntactically safe path lists and forbids exact owned/protected intersection. Directory ancestor overlap and filesystem aliases are not checked; whether entries denote exact files or recursive roots is caller policy. Factory stringifies arbitrary supplied entries. This is a path-list value, not verified filesystem authorization.'),
('research_digest.py',26,'Sorted compact ensure_ascii=False JSON digest helper with default json.dumps semantics. Unlike strict canonical owners it permits floats/NaN and string-coercible nonstring keys; no recursive type/resource admission. Stable bytes for the accepted input profile must be supplied by callers; SHA256 binds serialization, not research truth.'),
('revision.py',50,'A trimmed nonempty nominal label; no length/character/commit-existence or immutable revision check. Branch names and commit IDs are deliberately admitted in the same type, so the type cannot by itself pin source custody.'),
('schema.py',57,'Trimmed syntax token ending .v and digits, with nominal equality/hash. No registry membership, URI resolution or payload validation; regex validation is not schema conformance.'),
('task_objective.py',52,'Nonempty trimmed objective with16384-codepoint pre-trim length bound, despite16KB comment. Verified/safety wording means only these syntactic checks; no policy, executable meaning or authority judgment.'),
('turn.py',74,'Role inherits explicit Role constraints; modality enum supplies named examples but TurnKind inherits open syntactic Kind and does not restrict to that enum. Factory normalizes enum/string representations. No turn execution or model trust is conferred.'),
('turn_type.py',66,'TurnType defines VALID_TYPES but never checks membership: any nonempty stripped/lowercased string is accepted. Exact nominal equality is preserved. Consumers needing the six-category enum must validate separately.'),
('wire_key.py',54,'Complete54-line spelling catalog reviewed. This WireKey is a str Enum, unlike shared_kernel.key.WireKey; the catalog contains neither parsing nor mandatory/forbidden-field enforcement.')]
for p,n,s in rows:a.record('pfp/domain/shared_kernel/'+p,1,n,s)
a.report()
