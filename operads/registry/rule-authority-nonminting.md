# Authority and promotion rules

- `AGT-AUTH-0001` -- Configuration is not authority.
- `AGT-AUTH-0002` -- Every model-backed receipt has authority status `None`.
- `AGT-AUTH-0003` -- A model receipt may propose but cannot select its accepted
  terminal disposition.
- `AGT-AUTH-0004` -- Parsing, generation, test success, receipt verification,
  terminal disposition, and global green do not promote evidence or issue
  authority.
- `AGT-AUTH-0005` -- Only an authenticated human or governance boundary may
  promote evidence or issue authority.
- `AGT-AUTH-0006` -- The host may verify and route; it cannot mint authority from
  agent receipts.
