# FATUM database schema reference

This document describes the 10 read-only views and 2 tables available to the
FATUM agent through its database tools. Use these schemas to write SQL queries
without guessing table or column names.

The documented objects are distributed across three databases:

- `catalogservice_db`: services, orders, providers, and client behaviour.
- `rate`: service, provider, and client ratings.
- `postgres`: users, demographics, and addresses.

You may choose the query order according to the task. Many investigations
require sequential queries: first identify an entity, then use its identifier
to query related information.

## Schemas

**Important**: each query tool (`query_catalog`, `query_rate`, `query_users`)
connects to exactly ONE database. You cannot JOIN views across databases in a
single query. To combine data from different databases, run separate queries
and correlate the results by their shared identifiers (e.g. `service_id`,
`provider_id`, `user_id`).

### v_client_contracted_services (db: catalogservice_db)

This view indicates the services that have been requested by the app users. To determine the interaction of the user
with the service consider the columns client_id, avg_final_price, times_requested.

      Column       |            Type             | Collation | Nullable | Default 
-------------------+-----------------------------+-----------+----------+-------
--
 client_id         | character varying(36)       |           |          | 
 service_id        | character varying(36)       |           |          | 
 provider_id       | character varying(36)       |           |          | 
 title             | character varying(40)       |           |          | 
 description       | text                        |           |          | 
 job_type          | character varying(10)       |           |          | 
 category          | character varying(30)       |           |          | 
 times_requested   | bigint                      |           |          | 
 avg_final_price   | numeric                     |           |          | 
 completed         | bigint                      |           |          | 
 cancelled         | bigint                      |           |          | 
 rejected          | bigint                      |           |          | 
 failed            | bigint                      |           |          | 
 disputed          | bigint                      |           |          | 
 negative_outcomes | jsonb                       |           |          | 
 last_requested_at | timestamp without time zone |           |          | 

### v_client_service_behavior (db: catalogservice_db)


This view describes how users behave with the offered services, it shows metrics such ashow many times a service has been viewed and how much time users spent reviewing it

        Column        |            Type             | Collation | Nullable | Default 
----------------------+-----------------------------+-----------+----------+---------
 user_id              | character varying           |           |          | 
 service_id           | character varying           |           |          | 
 category             | character varying(30)       |           |          | 
 is_favorite          | boolean                     |           |          | 
 client_visits        | bigint                      |           |          | 
 client_dwell_seconds | bigint                      |           |          | 
 service_total_views  | bigint                      |           |          | 
 interaction_pct      | numeric                     |           |          | 
 last_viewed_at       | timestamp without time zone |           |          | 

### v_available_services (db: catalogservice_db)

It shows the services that are currently active

      Column       |          Type          | Collation | Nullable | Default 
-------------------+------------------------+-----------+----------+---------
 service_id        | character varying(36)  |           |          | 
 provider_id       | character varying(36)  |           |          | 
 provider_name     | character varying(255) |           |          | 
 provider_username | character varying(15)  |           |          | 
 title             | character varying(40)  |           |          | 
 description       | text                   |           |          | 
 category          | character varying(30)  |           |          | 
 job_type          | character varying(10)  |           |          | 
 price_type        | character varying(12)  |           |          | 
 base_price        | numeric(10,2)          |           |          | 
 is_negotiable     | boolean                |           |          | 
 default_time      | integer                |           |          | 
 total_views       | bigint                 |           |          | 
 favorite_count    | integer                |           |          | 


### v_provider_clientele (db: catalogservice_db)

It gives you an idea of the type of orders that have been resolved by a provider

    Column     |            Type             | Collation | Nullable | Default 
---------------+-----------------------------+-----------+----------+---------
 provider_id   | character varying(36)       |           |          | 
 client_id     | character varying(36)       |           |          | 
 orders        | bigint                      |           |          | 
 completed     | bigint                      |           |          | 
 avg_price     | numeric                     |           |          | 
 median_price  | double precision            |           |          | 
 top_city      | character varying           |           |          | 
 last_order_at | timestamp without time zone |           |          | 



### v_order_outcomes (db: catalogservice_db)

       Column      |            Type             | Collation | Nullable | Default 
------------------+-----------------------------+-----------+----------+---------
 order_id         | character varying(36)       |           |          | 
 client_id        | character varying(36)       |           |          | 
 provider_id      | character varying(36)       |           |          | 
 service_id       | character varying(36)       |           |          | 
 status           | character varying(15)       |           |          | 
 reason           | character varying(500)      |           |          | 
 booking          | timestamp without time zone |           |          | 
 negotiated_price | numeric(10,2)               |           |          | 
 created_at       | timestamp without time zone |           |          | 
 updated_at       | timestamp without time zone |           |          | 


### v_service_rating_summary (db: rate)

It gives you the average of a service rating

     Column     |           Type           | Collation | Nullable | Default 
----------------+--------------------------+-----------+----------+---------
 service_id     | character varying(36)    |           |          | 
 ratings        | bigint                   |           |          | 
 avg_score      | numeric                  |           |          | 
 last_rating_at | timestamp with time zone |           |          | 

### v_provider_rating_summary (db: rate)

 It gives you the average of a provider rating

      Column     |           Type           | Collation | Nullable | Default 
----------------+--------------------------+-----------+----------+---------
 provider_id    | character varying(36)    |           |          | 
 ratings        | bigint                   |           |          | 
 avg_score      | numeric                  |           |          | 
 last_rating_at | timestamp with time zone |           |          | 


### v_client_rating_summary (db: rate)

  It gives you the avaverage of a client rating

      Column     |           Type           | Collation | Nullable | Default 
----------------+--------------------------+-----------+----------+---------
 user_id        | character varying(36)    |           |          | 
 ratings        | bigint                   |           |          | 
 avg_score      | numeric                  |           |          | 
 low_scores     | bigint                   |           |          | 
 top_scores     | bigint                   |           |          | 
 last_rating_at | timestamp with time zone |           |          | 


### v_rating_detail (db: rate)

It gives the details of a rating to know what people like or dislike about the target

   Column    |           Type           | Collation | Nullable | Default 
-------------+--------------------------+-----------+----------+---------
 id          | character varying(36)    |           |          | 
 order_id    | character varying(36)    |           |          | 
 target_type | character varying(20)    |           |          | 
 target_id   | character varying(36)    |           |          | 
 rater_id    | character varying(36)    |           |          | 
 score       | integer                  |           |          | 
 details     | jsonb                    |           |          | 
 created_at  | timestamp with time zone |           |          | 


### v_user_demographics (db: postgres)

Shows the demographics of a user. Note: this view does not have a `username` column. To look up a user by
username, query the `users` table first (`WHERE username = '<value>'`) to
obtain the `user_id`, then use that id here and in other views.

   Column   |         Type          | Collation | Nullable | Default 
------------+-----------------------+-----------+----------+---------
 user_id    | character varying(36) |           |          | 
 role       | character varying(20) |           |          | 
 gender     | character varying(6)  |           |          | 
 birth_date | date                  |           |          | 
 age        | integer               |           |          | 
 age_bucket | text                  |           |          | 
 city       | character varying(50) |           |          | 
 is_active  | boolean               |           |          | 


### Tables

#### addresses (db: postgres)

Stores the user's addresses. When `position` is 0, the address is the principal one. The principal address
of a prfesional indicates where the service is being offered.

   Column    |          Type          | Collation | Nullable | Default 
-------------+------------------------+-----------+----------+---------
 id          | character varying(36)  |           | not null | 
 residence   | character varying(255) |           | not null | 
 alias       | character varying(255) |           | not null | 
 city        | character varying(50)  |           | not null | 
 state       | character varying(50)  |           | not null | 
 country     | character varying(50)  |           | not null | 
 position    | integer                |           | not null | 0
 user_aws_id | character varying(255) |           | not null | 


#### users (db: postgres)

Complete information **about a** user

       Column        |          Type          | Collation | Nullable |             Default             
---------------------+------------------------+-----------+----------+---------------------------------
 aws_id              | character varying(255) |           | not null | 
 email               | character varying(100) |           | not null | 
 complete_name       | character varying(142) |           | not null | 
 birth_date          | date                   |           | not null | 
 username            | character varying(15)  |           | not null | 
 phone_number        | character varying(20)  |           | not null | 
 role                | character varying(20)  |           | not null | 'CLIENT'::character varying
 is_active           | boolean                |           | not null | true
 document            | character varying(30)  |           | not null | 
 gender              | character varying(6)   |           | not null | 
 document_type       | character varying(20)  |           | not null | 
 city                | character varying(50)  |           |          | 
 country             | character varying(50)  |           | not null | 'COLOMBIA'::character varying
 verification_status | character varying(20)  |           | not null | 'UNVERIFIED'::character varying
 id                  | character varying(36)  |           | not null | 

## Identifier relationships

- `users.id` is the FATUM user identifier used as `user_id`, `client_id`, and
  `provider_id` in the catalog and rating views.
- `users.aws_id` is the AWS identity of a user.
- `addresses.user_aws_id` references `users.aws_id`, not `users.id`.
- To find a provider's principal service location:
  1. obtain the provider's `provider_id`;
  2. query `users` to obtain that user's `aws_id`;
  3. query `addresses` using `user_aws_id = users.aws_id`;
  4. keep the address where `position = 0`.
- A service is connected to its provider through `provider_id`.
- A client is connected to an order or behavior record through `client_id` or
  `user_id`, depending on the view.


## Location query rule

To determine where a provider offers a service, use the provider's principal
address, identified by `position = 0`.

Because `addresses` stores `user_aws_id` while the catalog views store
`provider_id`, resolve the relationship through `users.aws_id` before querying
`addresses`.

When matching cities, use case-insensitive matching and account for accents.
For example:

```sql
WHERE lower(city) LIKE '%bogot%'
```