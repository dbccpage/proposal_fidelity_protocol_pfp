---
name: react-components
description: Build accessible, typed React function components for the web dashboard.
---
# React components

Use this skill when creating or modifying components under `web/src/components`.

## Structure

- One component per file, named after the component (`OrderTable.tsx` exports `OrderTable`).
- Function components only. No class components, no default exports.
- Props are a named TypeScript `interface` declared directly above the component, suffixed `Props`.
- Keep components presentational where possible; fetch data in hooks under `web/src/hooks`.
- Co-locate a `*.test.tsx` file using React Testing Library; test behaviour, not implementation details.
- Co-locate a `*.stories.tsx` file with at least the default, loading, empty and error states.

## State and effects

- Derive values during render instead of mirroring props into state.
- Use `useMemo` only for measurably expensive computations; do not wrap every value.
- Every `useEffect` must list complete dependencies; prefer event handlers over effects for user actions.
- Never fetch inside `useEffect` without an abort controller; use the shared `useQuery` wrapper instead.
- Lift state only as high as the nearest common parent that needs it.
- Avoid context for frequently changing values; it re-renders every consumer.

## Styling

- Use the design-token CSS variables (`--space-2`, `--color-surface`); never hard-code colours or pixel spacing.
- Use CSS modules (`Component.module.css`); no inline style objects except for dynamic values.
- Support dark mode through tokens only; do not branch on theme in component code.
- Respect `prefers-reduced-motion` for any transition longer than 150 ms.

## Accessibility

- Every interactive element is a real `button`, `a` or form control; no clickable `div`s.
- Icon-only buttons need an `aria-label`.
- Tables need `<caption>` or `aria-labelledby`, and header cells need `scope`.
- Focus must be visible and must move predictably when dialogs open and close.
- Colour is never the only carrier of meaning; pair status colours with text or icons.
- Run the axe check in Storybook before requesting review.

## Data display

- Format money with the shared `formatMoney(cents, currency)` helper; never divide by 100 in a component.
- Format dates with `formatDate` in the viewer's locale; store and pass ISO-8601 strings.
- Long lists over 200 rows use the virtualised `DataGrid`.
- Empty states explain what is missing and offer the next action.
- Loading states use skeletons of the final layout, not spinners, for content areas.

## Forms

- Use the shared `Form` and `Field` components; they wire labels, descriptions and errors.
- Validate on blur and on submit; never block typing.
- Show server errors next to the field they belong to when the API returns a field path.
- Disable submit only while a request is in flight, and show progress.

## Performance

- Split routes with `React.lazy`; keep the initial bundle under the budget in `web/budget.json`.
- Images use `loading="lazy"` and explicit width and height.
- Avoid anonymous functions in props of memoised children only when profiling shows a problem.

## Review checklist

- [ ] Typed props interface, named export
- [ ] Tests and stories for all states
- [ ] Tokens only, no hard-coded styles
- [ ] Keyboard and screen-reader pass
- [ ] Money and dates formatted with shared helpers
- [ ] No new dependency without an approved ADR
