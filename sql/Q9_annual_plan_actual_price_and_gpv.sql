-- Q9: Annual plan actual subscription price + ongoing GPV revenue per active site
-- Purpose: Replace the $166 business assumption and $7.93 GPV estimate with real data.
--
-- Key insight (per user): net_collections is almost entirely subscription revenue;
-- GPV take (~2.9% of payments volume) is only ~3% of total revenue.
--
-- For annual plan sites:
--   - LM1: one large CHARGE transaction (the actual annual subscription price)
--   - LM2-LM11: $0 net_collections, only GPV take
--   - LM12: one RENEWAL transaction (the renewal price, may differ from original CHARGE)
--
-- This query gives us:
--   A) Avg CHARGE amount for annual plans at signup → true LM1 upfront price
--   B) Avg RENEWAL amount for annual plans at month 12 → true renewal price
--   C) Avg monthly GPV take for annual sites in months 2-11 → true ongoing revenue
--
-- Source: sandbox.ariellez.financial_transactions_vibe_sites, prod.wt_metasites.vibe,
--         prod.premium.subscriptions_premium_plan_scd, prod.payments.gpv_transactions
-- Author: Cursor agent | Date: 2026-06-29

WITH params AS (
    SELECT
        DATE '2025-07-01'  AS window_start,   -- cohorts that joined Jul 2025+
        DATE '2026-06-30'  AS window_end,
        'd9f069ca-b22f-40d2-ab2c-0fcfc4b47f96' AS vibe_application_id,
        CAST(0.029 AS DOUBLE) AS gpv_take_rate
),

-- Annual plan Vibe premium sites with their first premium start date
annual_premium_sites AS (
    SELECT
        v.msid,
        v.target_account_id AS account_id,
        date(v.site_creation_ts) AS site_created_date,
        min(s.start_date)        AS first_premium_date
    FROM prod.wt_metasites.vibe v
    INNER JOIN prod.premium.subscriptions_premium_plan_scd s
        ON v.msid = s.msid
        AND s.is_premium_plan = true
        AND lower(s.cycle_name) LIKE '%annual%'
    CROSS JOIN params p
    WHERE date(v.site_creation_ts) >= p.window_start
    GROUP BY v.msid, v.target_account_id, v.site_creation_ts
),

-- A) CHARGE transactions for annual plan sites (the upfront payment at signup)
annual_charges AS (
    SELECT
        a.msid,
        ft.net_collection_usd_for_recognition AS charge_amount,
        ft.transaction_created_date,
        date_diff('day', a.first_premium_date, date(ft.transaction_created_date)) AS days_from_premium_start
    FROM annual_premium_sites a
    INNER JOIN sandbox.ariellez.financial_transactions_vibe_sites ft
        ON a.msid = ft.msid
    WHERE upper(ft.sale_type) = 'CHARGE'
),

-- B) RENEWAL transactions for annual plan sites (at month 12)
annual_renewals AS (
    SELECT
        a.msid,
        ft.net_collection_usd_for_recognition AS renewal_amount,
        ft.transaction_created_date,
        date_diff('day', a.first_premium_date, date(ft.transaction_created_date)) AS days_from_premium_start
    FROM annual_premium_sites a
    INNER JOIN sandbox.ariellez.financial_transactions_vibe_sites ft
        ON a.msid = ft.msid
    WHERE upper(ft.sale_type) = 'RENEWAL'
      AND date_diff('day', a.first_premium_date, date(ft.transaction_created_date))
          BETWEEN 330 AND 400   -- ~12 months window
),

-- C) Monthly GPV take for annual sites in months 2-11 (no subscription collected)
-- Approximate by finding months where there was NO CHARGE or RENEWAL transaction
gpv_ongoing AS (
    SELECT
        a.msid,
        date_trunc('month', date(coalesce(g.transaction_initiated_date, g.created_date))) AS activity_month,
        sum(g.price_in_usd) * p.gpv_take_rate                                            AS gpv_take_usd,
        date_diff(
            'month',
            date_trunc('month', a.first_premium_date),
            date_trunc('month', date(coalesce(g.transaction_initiated_date, g.created_date)))
        ) AS life_month
    FROM annual_premium_sites a
    INNER JOIN prod.payments.gpv_transactions g ON a.msid = g.msid
    CROSS JOIN params p
    WHERE date(coalesce(g.transaction_initiated_date, g.created_date))
              BETWEEN p.window_start AND p.window_end
    GROUP BY a.msid, 2, 4, p.gpv_take_rate, a.first_premium_date
)

-- ── Results ──────────────────────────────────────────────────────────────────

-- A) Average initial CHARGE price for annual plans
SELECT
    'A_avg_annual_charge_price' AS metric,
    round(avg(charge_amount), 2) AS value_usd,
    count(DISTINCT msid)        AS site_count,
    round(min(charge_amount), 2) AS min_usd,
    round(max(charge_amount), 2) AS max_usd,
    round(approx_percentile(charge_amount, 0.5), 2) AS median_usd
FROM annual_charges
WHERE days_from_premium_start BETWEEN -7 AND 30  -- tight window around signup

UNION ALL

-- B) Average RENEWAL price at month 12
SELECT
    'B_avg_annual_renewal_price' AS metric,
    round(avg(renewal_amount), 2),
    count(DISTINCT msid),
    round(min(renewal_amount), 2),
    round(max(renewal_amount), 2),
    round(approx_percentile(renewal_amount, 0.5), 2)
FROM annual_renewals

UNION ALL

-- C) Avg monthly GPV take for annual sites in non-renewal months (LM 2-11)
SELECT
    'C_avg_monthly_gpv_ongoing_annual' AS metric,
    round(avg(gpv_take_usd), 4),
    count(DISTINCT msid),
    round(min(gpv_take_usd), 4),
    round(max(gpv_take_usd), 4),
    round(approx_percentile(gpv_take_usd, 0.5), 4)
FROM gpv_ongoing
WHERE life_month BETWEEN 1 AND 11  -- exclude LM0 (signup month) and LM12+ (renewal)

ORDER BY metric;
