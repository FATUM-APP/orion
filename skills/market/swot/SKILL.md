---
name: swot
description: Use when the user wants a SWOT analysis, a market diagnosis, or a positioning check for a service or a provider
---

# Context

A SWOT separates what the provider controls from what the market imposes:

- **Strengths / Weaknesses (internal)**: rating behaviour, review text, price,
  description quality, punctuality, coverage, schedule, repeat rate. The
  provider can change these.
- **Opportunities / Threats (external)**: category averages, competitor
  density, demand signals, seasonality, what clients in this category expect.
  The provider cannot change these, only react to them.

The output is a **diagnosis with evidence**, not a list of adjectives, and it
ends with a short list of actions. Read `references/REFERENCE.MD` for two
worked examples.

# Step by step

1. **Identify the subject.** A `service_id`, or a `provider_id` with its
   services. Confirm category (`job_type`), city/coverage and price.
2. **Internal evidence.** Ratings (average, count, distribution), completed
   orders, the free-text `details` of reviews (repeated praise and complaints),
   price against the category, description length and clarity, calendar
   availability and booking lead time.
3. **External evidence.** Category averages (rating, price, order volume),
   number of providers offering the same category in the same city, demand
   signals (orders per service, repeat rate), price distribution.
4. **Classify.** Internal factors go to S/W, external ones to O/T. If the
   provider cannot change it, it is not a strength or a weakness.
5. **Benchmark.** For rating and price, show provider vs. category average vs.
   market average. Flag gaps larger than ~10-15% as material.
6. **Derive actions.** At most three, each tied to one weakness or threat and to
   the tool that would implement it (for example `update_catalog_item` for
   title, description, price, negotiability or estimated time).

# Rules

- 3 to 5 items per quadrant, never more. More is a list, not an analysis.
- No duplicates across quadrants. If an item is both, choose where it acts.
- Every item carries its evidence: a number, a count, or a quote from a review.
- Never invent competitors, prices or demand. If data is missing, say which
  query would fill it and leave the item out.
- Do not mix recommendations into the quadrants; actions go in their own list.
- If the service has fewer than ~10 ratings, label the analysis **preliminary**
  and lower the confidence.

# Output

```markdown
## SWOT — <service title> (<service_id>, <provider_name>)

| Strengths | Weaknesses |
|---|---|
| <item> — <evidence> | <item> — <evidence> |

| Opportunities | Threats |
|---|---|
| <item> — <evidence> | <item> — <evidence> |

## Benchmark
- Rating: 4.6 (category avg 4.2, market avg 4.1) — +10%
- Price: 95k (category avg 110k, market avg 105k) — 14% below
- Orders: 34 in 90 days (category avg 21)

## Actions
1. <action> — fixes <weakness/threat> — via `update_catalog_item(...)`
2. ...
```

Keep the whole analysis under ~600 words. If you save it, 
save the SWOT using `remember_selected_services` with `key="/swot.md"`
and `replace=True`. The service must be selected first. This does not
overwrite the niche at the default memory key.
