# SWOT references

Two worked examples of the same method. Notice that every line carries a
number or a quote, and that actions come only at the end.

## Reference one — at-home deep cleaning, Bogotá

**Subject:** service `s_1841`, provider `p_118` ("Limpieza Total"), category
HOME_CLEANING, Bogotá, price 95k, 60 minutes.

**Data used:** 34 orders in 90 days, 12 ratings (avg 4.6), 3 negative reviews,
category averages from `query_rate`, price distribution from `query_catalog`.

| Strengths | Weaknesses |
|---|---|
| Rating 4.6 vs category 4.2 (+10%): consistent quality above the category | Only 12 ratings in 90 days: thin sample, volatile average |
| Reviews repeat "puntual" (5 of 12) and "trae sus insumos" (4 of 12) | Description is 1 line and lists no supplies; clients only learn it after booking |
| Price 95k vs category 110k: 14% below, strong for a family budget | Calendar shows only Saturday mornings; no weekday slots |

| Opportunities | Threats |
|---|---|
| 63% of orders in the category are at-home and growing: the service is in the right format | 9 other providers offer the same category in the same city at a similar price |
| Weekday demand exists: 28% of category orders are Mon-Fri | Two competitors with 4.8+ and 100+ ratings appear first in search |

**Actions**
1. Rewrite the description to state "we bring our own supplies" and the
   included tasks — fixes the information weakness — `update_catalog_item(description=...)`.
2. Open two weekday morning slots — addresses the calendar weakness and the
   weekday opportunity.
3. Ask satisfied clients for a rating after each visit — fixes the thin
   sample that weakens the main strength.

## Reference two — personal training for older adults, Medellín

**Subject:** service `s_2207`, provider `p_301` ("Movimiento Seguro"),
category PERSONAL_TRAINING, Medellín, price 70k/session, 45 minutes.

**Data used:** 18 orders, 9 ratings (avg 3.9), 4 reviews mention "canceló",
category avg 4.5, market avg 4.1, price distribution from `query_catalog`.

| Strengths | Weaknesses |
|---|---|
| Specialised in older adults: 7 of 9 reviews mention patience and care | 4 of 9 reviews mention last-minute cancellations: the clearest driver of low ratings |
| Price 70k vs category 90k: accessible for a recurring service | Description does not mention the 45-minute length or the home visit |

| Opportunities | Threats |
|---|---|
| Category demand from 55+ clients grew in the last 90 days | Two gyms in the same area launched group classes at 45k |
| Few providers in the category explicitly target older adults | Rating 3.9 sits below the category average 4.5 |

**Actions**
1. Fix the cancellation policy (24h notice) and say it in the description —
   fixes the main weakness — `update_catalog_item(description=...)`.
2. Add the session length and home-visit coverage to the title/description —
   removes a purchase blocker — `update_catalog_item(title=..., description=...)`.
3. Do not compete on price with the gyms; compete on specialisation (older
   adults) — reacts to the threat without eroding margin.
