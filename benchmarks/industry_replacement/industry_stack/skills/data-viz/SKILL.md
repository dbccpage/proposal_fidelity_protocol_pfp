---
name: data-viz
description: Produce clear, honest charts for reports and dashboards with the plotting stack.
---
# Data visualisation

Use this skill when a task asks for a chart, a dashboard panel or a figure for a report.

## Choosing the chart

- Change over time: line chart; use bars only for a small number of discrete periods.
- Comparison across categories: horizontal bar chart sorted by value.
- Part of a whole: stacked bar or a single bar with segments; avoid pie charts beyond three slices.
- Distribution: histogram or box plot; show the sample size.
- Relationship between two measures: scatter plot with a trend line only when a model justifies it.
- A single number: a stat tile with the comparison period, not a gauge.

## Axes and scales

- Bar charts start at zero. Line charts may start elsewhere, but label the axis.
- Never use dual y-axes; use two aligned panels instead.
- Use log scales only for data spanning several orders of magnitude, and say so in the axis title.
- Label units in axis titles (`Revenue (USD)`, `Latency (ms)`), not in every tick.
- Use thousands separators and at most three significant digits on ticks.

## Colour

- Use the categorical palette from `viz/palette.json` in order; do not pick colours ad hoc.
- Use a sequential palette for ordered data and a diverging palette only around a meaningful midpoint.
- Check contrast for both light and dark themes.
- Highlight one series by colour and render the rest in neutral grey when telling a single story.

## Text

- The title states the finding ("Refunds fell 12% after the fix"), the subtitle states the measure and period.
- Annotate notable events directly on the chart instead of in a legend.
- Put legends next to the data or label lines directly at their ends.
- Cite the data source and extraction date in a footnote.

## Honesty

- Show uncertainty: confidence bands, error bars or the sample size.
- Do not smooth or resample without saying so.
- Do not truncate axes to exaggerate differences.
- Show missing data as gaps, not zeros.
- Keep the same scale when comparing small multiples.

## Dashboards

- Put the most important number top left.
- Group panels by question, not by data source.
- Every panel has a description explaining how to read it and what action it supports.
- Default time ranges match the decision cadence (daily operations: 7 days; planning: 12 months).
- Limit a dashboard to about nine panels; link to detail dashboards for more.

## Implementation

- Build charts from tidy data frames with one row per observation.
- Keep plotting code in functions that take data and return a figure; no global state.
- Export static figures as SVG for documents and PNG at 2x for slides.
- Store the code that produced a figure next to the figure.

## Checklist

- [ ] Chart type matches the question
- [ ] Axes, units and source labelled
- [ ] Palette and contrast checked
- [ ] Uncertainty and missing data shown
- [ ] Title states the finding
