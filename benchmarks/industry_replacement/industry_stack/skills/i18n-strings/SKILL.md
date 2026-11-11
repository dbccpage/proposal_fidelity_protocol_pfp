---
name: i18n-strings
description: Add and change user-facing strings so they can be translated correctly.
---
# Internationalisation of strings

Use this skill whenever a change adds or edits text that users will see.

## Message catalogue

- All user-facing text lives in `locales/en/*.json`; code references messages by key, never by literal text.
- Keys are dotted, stable and descriptive of purpose, not content: `orders.table.emptyState.title`.
- Never reuse a key for a different meaning, even if the English text is identical.
- Deleting a key requires removing it from every locale in the same change.
- Add a translator comment (`"_comment"`) for any string whose meaning depends on context.

## Formatting

- Use ICU MessageFormat for plurals, gender and selects: `{count, plural, one {# order} other {# orders}}`.
- Never concatenate translated fragments; word order differs between languages.
- Never build sentences from a number and a noun in code; let the plural rules decide.
- Format numbers, currencies, dates and lists with the `Intl` APIs and the active locale.
- Do not put HTML in messages; use rich-text placeholders that the renderer maps to components.

## Layout

- Leave room for text expansion of 30 to 50 percent; German and Finnish strings are often much longer.
- Do not truncate translated text without a tooltip showing the full string.
- Support right-to-left locales: use logical CSS properties (`margin-inline-start`) and mirrored icons where
  direction matters.
- Avoid text in images; if unavoidable, provide localised assets.

## Content

- Write short, plain sentences without idioms, slang or cultural references.
- Use consistent terminology from the glossary in `locales/glossary.md`.
- Do not capitalise for emphasis; use sentence case.
- Error messages say what happened and what the user can do next.

## Process

- English strings are reviewed by the content design team before merge.
- New keys are sent to the translation vendor nightly; untranslated keys fall back to English.
- Pseudo-localisation (`en-XA`) runs in CI to catch hard-coded strings and clipping.
- Screenshots of new UI are attached to the translation request for context.

## Testing

- Unit tests assert on message keys or use the test locale, not English literals.
- Visual regression tests run in English, German, Japanese and Arabic.
- Check that plural forms render correctly for 0, 1, 2, 5 and 21 in at least one Slavic locale.

## Checklist

- [ ] No literal user-facing strings in code
- [ ] Keys descriptive and unique in meaning
- [ ] ICU plurals and selects used
- [ ] Layout tolerates expansion and RTL
- [ ] Translator comments added where needed
