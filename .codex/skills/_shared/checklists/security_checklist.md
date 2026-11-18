# Security Checklist

Shared security checklist for code review and security scanning.

## Quick Security Check

- [ ] No hardcoded secrets or credentials
- [ ] Input validation on user data
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] No command injection vulnerabilities
- [ ] Proper authentication and authorization checks

## OWASP Top 10 (2021)

| # | Category | What to Check |
| --- | ---------- | --------------- |
| A01 | **Broken Access Control** | Authorization checks, RBAC, CORS |
| A02 | **Cryptographic Failures** | Encryption, hashing, key management |
| A03 | **Injection** | SQL, NoSQL, OS command, LDAP |
| A04 | **Insecure Design** | Threat modeling, secure patterns |
| A05 | **Security Misconfiguration** | Default credentials, debug mode, headers |
| A06 | **Vulnerable Components** | Dependency audit, CVE checks |
| A07 | **Auth Failures** | Session management, password handling |
| A08 | **Data Integrity Failures** | Deserialization, CI/CD security |
| A09 | **Logging Failures** | Insufficient logging, log injection |
| A10 | **SSRF** | URL validation, network segmentation |

## Severity Classification

| Severity | Action | Timeline |
| ---------- | -------- | ---------- |
| **CRITICAL** | Immediate fix required | Blocks deploy |
| **HIGH** | Must fix | Before next release |
| **MEDIUM** | Should fix | Near term |
| **LOW** | Track | Future fix |

## Reporting Format

When reporting security findings:

```markdown

## [SEVERITY] Finding Title

**Location**: `file.py:123` ext
**CWE**: CWE-XXX (if applicable)

**Description**: What the vulnerability is

**Impact**: What could happen if exploited

**Remediation**: How to fix it

``` ext

## Trust Boundary / Oracle Security

- [ ] No self-certification path introduced
- [ ] Certificate validation checks signature, expiry, scope, kind, nonce replay, and revocation
- [ ] Mock-only validation is not counted as security evidence
- [ ] Secrets/keys are not reused across supposedly independent trust boundaries
- [ ] Authorization is not described as proof of correctness

## Supply Chain / CI Integrity

- [ ] CI workflows pin trusted actions or versions
- [ ] Deserialization and artifact download paths are validated
- [ ] Release artifacts are reproducible or attested where required
- [ ] Dependency audit is run and results are attached

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
