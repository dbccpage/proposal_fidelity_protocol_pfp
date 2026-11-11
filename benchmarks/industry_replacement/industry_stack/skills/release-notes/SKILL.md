---
name: release-notes
description: Draft customer-facing release notes and internal changelog entries from merged pull requests.
---
# Release notes

Use this skill when asked to summarise a release, write a changelog entry or prepare an announcement.

## Sources

- Start from the list of merged pull requests between the previous release tag and the release branch head.
- Read each PR title, description and linked issue; do not infer behaviour from the diff alone.
- Exclude PRs labelled `internal`, `chore`, `ci` or `deps` from customer-facing notes, but keep them in the
  internal changelog.
- Security fixes are described only after the advisory is published; until then, write "security improvements".

## Structure

1. A two-sentence summary of the most important change for customers.
2. **New** — features customers can use now, each with one sentence on the benefit and a link to docs.
3. **Improved** — behaviour or performance changes, with numbers when they were measured.
4. **Fixed** — bugs customers could have noticed, written as the symptom that is gone.
5. **Deprecated and removed** — with dates and migration guidance.
6. **Known issues** — with workarounds.

## Voice

- Write in second person and present tense: "You can now export reports as CSV."
- Lead with the benefit, then the mechanism.
- No internal code names, ticket numbers, team names or people's names.
- Avoid superlatives and unmeasured performance claims.
- Keep each bullet under 30 words; link out for details.
- Use sentence case for headings.

## Versioning

- Follow semantic versioning: breaking API changes bump the major version, features bump minor, fixes bump patch.
- A deprecation is announced at least one minor release before removal.
- Every breaking change has a migration section with before and after examples.
- Pre-release builds use `-rc.N` suffixes and are not announced publicly.

## Internal changelog

- Group entries by component (`api`, `web`, `billing`, `infra`).
- Include PR numbers and authors' team handles.
- Note database migrations, feature flags and configuration changes explicitly, with rollback steps.
- Note any change to on-call runbooks.

## Localisation

- Customer-facing notes are translated after English sign-off; freeze the English text 48 hours before release.
- Keep product names and UI labels exactly as they appear in the product so translators can match them.
- Avoid idioms and wordplay.

## Review

- Product marketing reviews customer-facing notes; engineering leads review the internal changelog.
- Support reviews the known-issues section and adds help-centre links.
- Legal reviews anything mentioning data handling, retention or compliance.

## Checklist

- [ ] Every customer-facing bullet traceable to a PR
- [ ] No internal names or ticket numbers
- [ ] Breaking changes and deprecations dated
- [ ] Known issues have workarounds
- [ ] Links resolve
