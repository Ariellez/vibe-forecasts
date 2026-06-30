# ── 12-Month Revenue Forecast: Vibe Premium — Subscription-Only (Jul 2026 – Jun 2027) ─
# Datadoc: https://bo.wix.com/data-tools/quix/v2/datadoc/111027/?cellId=697721
#
# Parameters sourced from actual query results (v11 — Subscription-only model, 2026-06-30):
#   Q_FA  (cell 697714): active base per plan type (Jan-May 2026 avg)
#   Q_FP2 (cell 697733): conversion rate 3.32% & Annual share 54.6% — ALL 12 cohorts
#                         Jun 2025-May 2026, 554,635 sites
#   Q_FP3 (cell 697734): steady-state churn Annual 6.08% / Monthly 17.96% (pooled cohort)
#   W5 (datadoc/114856 cell 719239): multi-cohort validation (Jan–May 2026 cohorts)
#                         → Month-1 churn: ~20.5% blended (Annual 10.9%, Monthly 32.1%)
#                         → LM1 AI cost: $1.26/site avg across cohorts
#                         → LM2 AI cost: $0.133/site (10.5% of LM1)
#                         → LM3: $0.064 | LM4: $0.044 | LM5: $0.030 | LM6+: decaying tail
#   W9 (datadoc/114856 cell 725342): Jan 2026 premium cohort AI cost by pattern & life-month
#                         → 3,306 premium sites classified into 5 patterns
#                         → Weighted avg per-site: LM1 $8.87 | LM2 $2.91 | LM3 $1.50
#                         → LM4 $1.06 | LM5 $0.73 | LM6 $0.70 (plateau begins)
#                         → Growing sites (4.7%) PEAK at LM4 ($6.87) then decline — no compounding
#   W11 (cohort survival validated): Jan 2026 cohort annual plans → 2%/mo mid-cycle churn
#                         → 12-month survival: M1 (10.9%) × months 2-11 (0.98^11) = 71.3%
#   Monthly plan subscription price: avg RENEWAL transaction $23.96/site (data-validated, 4,670 sites)
#
# Model logic v11 — key changes vs v10:
#   SUBSCRIPTION-ONLY: GPV income excluded from forecast (per user request 2026-06-30).
#   1. MONTHLY_REV_ANNUAL_GPV: $0.66 → $0.00 (annual sites generate no ongoing revenue in
#      non-renewal months; subscription fee is lump-sum at renewal only)
#   2. MONTHLY_REV_MONTHLY: $20.38 → $23.96 (actual avg RENEWAL transaction for monthly plans;
#      data-validated from financial_transactions_vibe_sites, 4,670 sites, median $23.35)
#   All renewal wave logic unchanged from v10 (Q9-validated $114.71 annual price, 15% churn).
#
# Last updated: 2026-06-30 (v11 — Subscription-only model) | Author: Cursor agent
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd

# ── Revenue Parameters ────────────────────────────────────────────────────────

# Active base as of Jun 2026 (Q_FA)
ACTIVE_ANNUAL           = 6_955      # active Annual premium sites
ACTIVE_MONTHLY          = 3_185      # active Monthly premium sites

# Monthly combined revenue per site: net collections + GPV (Q_FA, Jan-May 2026 avg)
# v9: MONTHLY_REV_ANNUAL split into GPV-only ($7.93) + explicit renewal wave.
#     $21.76 total = $13.83 amortized subscription ($166/12) + $7.93 GPV.
#     Annual subscription is now recognized as a lump-sum in the renewal month.
MONTHLY_REV_ANNUAL      = 0.00       # USD / active Annual site / month (GPV EXCLUDED, v11)
                                     # Annual sites generate $0 ongoing revenue between renewals;
                                     # all subscription income arrives as lump-sum at renewal month.
MONTHLY_REV_ANNUAL_NEW  = 114.71     # USD — new annual converts pay full annual price upfront (Q9)
MONTHLY_REV_MONTHLY     = 23.96      # USD / active Monthly site / month (subscription only, v11)
                                     # Data-validated: avg RENEWAL transaction from
                                     # financial_transactions_vibe_sites, 4,670 monthly-plan sites,
                                     # avg $23.96 (median $23.35). Replaces $20.38 Q_FA estimate
                                     # which blended subscription + GPV.
ANNUAL_RENEWAL_PRICE    = 114.71     # USD — actual avg annual plan price (Q9: avg CHARGE 5,745 sites)
                                     # Confirmed: Jan 2026 $313K CHARGE / 2,684 sites = $116.71/site
RENEWAL_CHURN           = 0.15       # 15% of annual sites don't renew at month 12 (user assumption)
# Survival to renewal: M1 churn 10.9%, then W11-validated 2%/mo for months 2-11
ANNUAL_SURVIVAL_TO_RENEWAL = (1 - 0.109) * (0.98 ** 11)   # = 0.713

# Steady-state churn rates (Q_FP3: pooled-cohort weighted avg, >= 3 months observation)
ANNUAL_CHURN_STEADY     = 0.0608     # 6.08% — Annual plans (established base)
MONTHLY_CHURN_STEADY    = 0.1796     # 17.96% — Monthly plans (established base)

# Month-1 churn for new converts (W5 multi-cohort validation — datadoc/114856 cell 719239)
# Observed blended M1 churn across Jan–Apr 2026 cohorts: 18.5%, 19.5%, 20.0%, 23.9% → avg 20.5%
# Derived per-plan rates: blended = 0.546 × Annual + 0.454 × Monthly = 20.5%
# Scaling factor vs steady-state implied blended (11.47%): 1.79×
ANNUAL_CHURN_M1         = 0.109      # 10.9% — Annual converts in their first full month
MONTHLY_CHURN_M1        = 0.321      # 32.1% — Monthly converts in their first full month

# New site creation — updated 2026-06-25 (v7) from W7 daily data (datadoc/114856 cell 720680):
#   Post-cliff daily run rate (Jun 3–23): avg ~378/day → ~10,000/month
#   Jun 1–2 had legacy high traffic (1,267 + 997); cliff hit Jun 3 (-57% overnight)
#   Conservative 10K chosen as stable post-cliff baseline (vs earlier 13K WoW extrapolation)
JUNE_BASELINE           = 10_000
NEW_SITES_BASE          = round(JUNE_BASELINE * 0.97)   # = 9,700 — July 2026 first forecast month
MONTHLY_GROWTH_RATE     = -0.03      # -3%/month from July onward

# Conversion funnel (Q_FP2: all 12 cohorts Jun 2025–May 2026 = 554,635 sites)
CONVERSION_RATE         = 0.0332     # 3.32%
ANNUAL_SHARE            = 0.546      # 54.6% Annual; 45.4% Monthly
DAY0_SHARE              = 0.48       # 48% convert Day 0

# ── AI Cost Parameters (spike+tail model, W5 validated) ──────────────────────

# Historical cohort sizes — actual from W5 (datadoc/114856) + WoW weekly data
HIST_COHORT_SIZES = {
    -1:  13_000,    # June 2026 (WoW estimate)
    -2:  41_627,    # May 2026 (WoW: 9332+12394+10789+9112)
    -3:  38_151,    # April 2026 (W5 query)
    -4:  72_832,    # March 2026 (W5 query)
    -5:  77_652,    # February 2026 (W5 query)
    -6:  86_452,    # January 2026 (W5 query)
    -7:  80_000,    # December 2025 (estimated)
    -8:  75_000,    # November 2025 (estimated)
    -9:  65_000,    # October 2025 (estimated)
    -10: 60_000,    # September 2025 (estimated)
    -11: 55_000,    # August 2025 (estimated)
    -12: 50_000,    # July 2025 (estimated)
}

# AI cost per original cohort-site by life month (W5 multi-cohort avg — free + premium blended)
# LM1 dominates (~97% of total cohort AI cost in month 1). Sharp drop to LM2, then tail.
LM_AI_RATES = {
    1:  1.2600,    # $1.26 — avg of Jan $1.35, Feb $0.97, Mar $1.17, Apr $1.43, May $1.43
    2:  0.1330,    # $0.133 — avg across all cohorts (10.5% of LM1)
    3:  0.0640,    # $0.064 — avg (4.7% of LM1)
    4:  0.0440,    # $0.044 — avg (3.4% of LM1)
    5:  0.0300,    # $0.030 — avg (2.4% of LM1)
    6:  0.0260,    # $0.026 — Jan observed
    7:  0.0210,    # extrapolated tail (0.026 × 0.81)
    8:  0.0170,    # extrapolated
    9:  0.0140,    # extrapolated
    10: 0.0110,    # extrapolated
    11: 0.0090,    # extrapolated
    12: 0.0070,    # extrapolated
}
LM_AI_DEFAULT = 0.005   # LM 13+ (very small residual)

# ── Premium AI Cost Parameters (W9 validated — Jan 2026 cohort, datadoc/114856 cell 725342) ──
# Per-site monthly AI cost by life-month (LM) of premium subscription
# 3,306 Jan 2026 premium sites classified: spike_only 50%, early_only 28%, declining 14%,
# growing 4.7%, no_ai 4% — weighted avg shows steep LM1 spike then DECLINING tail.
# Key finding: even "growing" pattern sites peak at LM4 ($6.87) then decline → no compounding.
# LM7–12: extrapolated with ~6%/month gentle decline; LM13+: plateau at $0.40/site
PREM_LM_AI_RATES = {
    1:  8.87,    # W9 observed: first-month premium usage spike (all 3,306 sites weighted)
    2:  2.91,    # W9 observed: sharp drop after LM1
    3:  1.50,    # W9 observed
    4:  1.06,    # W9 observed (growing pattern peaks here at $6.87, then declines)
    5:  0.73,    # W9 observed
    6:  0.70,    # W9 observed (plateau beginning — stabilizing ~$0.70/site)
    7:  0.65,    # extrapolated (~7% decline from LM6)
    8:  0.61,    # extrapolated
    9:  0.57,    # extrapolated
    10: 0.53,    # extrapolated
    11: 0.50,    # extrapolated
    12: 0.47,    # extrapolated
}
PREM_LM_AI_DEFAULT = 0.40   # LM13+ residual

# Historical monthly premium converts (new subscriptions per month)
# Jan–Jun 2026: from W5/W7 cohort sizes × 3.32% conversion rate (W5 actual for Jan = 2,776)
# Pre-Jan 2026: estimated from HIST_COHORT_SIZES free-site baseline × 3.32%
PREM_HIST_COHORT_SIZES = {
    -1:    332,   # Jun 2026 (~10,000 × 3.32%)
    -2:  1_382,   # May 2026 (41,627 × 3.32%)
    -3:  1_267,   # Apr 2026 (38,151 × 3.32%)
    -4:  2_418,   # Mar 2026 (72,832 × 3.32%)
    -5:  2_578,   # Feb 2026 (77,652 × 3.32%)
    -6:  2_776,   # Jan 2026 (W5 actual: 2,776 converts)
    -7:  2_656,   # Dec 2025 (~80,000 × 3.32%)
    -8:  2_490,   # Nov 2025 (~75,000 × 3.32%)
    -9:  2_158,   # Oct 2025 (~65,000 × 3.32%)
    -10: 1_992,   # Sep 2025 (~60,000 × 3.32%)
    -11: 1_826,   # Aug 2025 (~55,000 × 3.32%)
    -12: 1_660,   # Jul 2025 (~50,000 × 3.32%)
    -13: 1_500,   # Jun 2025 (estimated)
    -14: 1_400,   # May 2025 (estimated)
    -15: 1_300,   # Apr 2025 (estimated)
    -16: 1_200,   # Mar 2025 (estimated)
    -17: 1_100,   # Feb 2025 (estimated)
    -18: 1_000,   # Jan 2025 (estimated)
}


# ── Month-by-Month Simulation ─────────────────────────────────────────────────

months_labels = []
y, m = 2026, 7
for _ in range(12):
    months_labels.append(f"{y}-{m:02d}")
    m += 1
    if m > 12:
        m = 1; y += 1

# Revenue simulation — two-phase churn model
# State: steady_* = established sites; fresh_* = new converts in their first full month
steady_annual  = float(ACTIVE_ANNUAL)
steady_monthly = float(ACTIVE_MONTHLY)
fresh_annual   = 0.0
fresh_monthly  = 0.0

# Build forecast new_sites list for AI cost indexing
forecast_new_sites = [round(NEW_SITES_BASE * ((1 + MONTHLY_GROWTH_RATE) ** i)) for i in range(12)]

rows = []
for i, label in enumerate(months_labels):

    # ── BOM active base ──
    annual_bom   = steady_annual  + fresh_annual
    monthly_bom  = steady_monthly + fresh_monthly
    total_bom    = annual_bom + monthly_bom

    # ── New conversions ──
    new_sites    = NEW_SITES_BASE * ((1 + MONTHLY_GROWTH_RATE) ** i)
    new_conv     = new_sites * CONVERSION_RATE
    new_annual   = new_conv * ANNUAL_SHARE
    new_monthly  = new_conv * (1 - ANNUAL_SHARE)

    # ── Revenue: BOM base GPV + Renewal wave + Day-0 new converts ──
    rev_existing = (annual_bom  * MONTHLY_REV_ANNUAL +
                    monthly_bom * MONTHLY_REV_MONTHLY)

    # Renewal wave: cohort from 12 months ago hits renewal date
    # Jan 2026 cohort (month i=6, Jan 2027) uses actual surviving sites = 1,143
    JAN2026_ANNUAL_AT_LM12 = 1_143
    hist_key = i - 12
    if i == 6:   # Jan 2027 — Jan 2026 cohort
        surviving = JAN2026_ANNUAL_AT_LM12
    elif hist_key in PREM_HIST_COHORT_SIZES:
        orig_annual = PREM_HIST_COHORT_SIZES[hist_key] * ANNUAL_SHARE
        surviving   = orig_annual * ANNUAL_SURVIVAL_TO_RENEWAL
    else:
        surviving = 0.0
    renewing_sites = round(surviving * (1 - RENEWAL_CHURN))
    rev_renewal    = renewing_sites * ANNUAL_RENEWAL_PRICE

    # New Day-0 converts use full $21.76 (they just paid their annual fee)
    rev_day0_new = ((new_annual  * DAY0_SHARE) * MONTHLY_REV_ANNUAL_NEW +
                    (new_monthly * DAY0_SHARE) * MONTHLY_REV_MONTHLY)
    total_rev    = rev_existing + rev_renewal + rev_day0_new

    # ── AI cost — free sites spike+tail model ──
    # Sum contributions from: this month's cohort (LM1) + all prior cohorts (LM2+)
    ai_cost_free = 0.0
    for k in range(13):                     # k=0 → this month (LM1); k=1 → last month (LM2)...
        lm = k + 1
        month_idx = i - k                   # forecast month index (negative = historical)
        if month_idx >= 0:
            cohort_size = forecast_new_sites[month_idx]
        elif month_idx in HIST_COHORT_SIZES:
            cohort_size = HIST_COHORT_SIZES[month_idx]
        else:
            cohort_size = 0
        rate = LM_AI_RATES.get(lm, LM_AI_DEFAULT)
        ai_cost_free += cohort_size * rate

    # Premium AI cost — same cohort×LM approach as free AI cost, using W9-validated rates
    ai_cost_prem = 0.0
    for k in range(24):                  # covers up to LM24 (Jan 2025 cohort and older)
        lm = k + 1
        month_idx = i - k
        if month_idx >= 0:
            n = round(forecast_new_sites[month_idx] * CONVERSION_RATE)
        elif month_idx in PREM_HIST_COHORT_SIZES:
            n = PREM_HIST_COHORT_SIZES[month_idx]
        else:
            n = 0
        rate = PREM_LM_AI_RATES.get(lm, PREM_LM_AI_DEFAULT)
        ai_cost_prem += n * rate
    total_ai_cost = ai_cost_free + ai_cost_prem
    net_margin    = total_rev - total_ai_cost
    margin_pct    = (net_margin / total_rev * 100) if total_rev > 0 else 0

    # ── End-of-month base: two-phase churn ──
    # Steady base churns at steady-state rate; fresh converts churn at month-1 rate
    survived_steady_annual  = steady_annual  * (1 - ANNUAL_CHURN_STEADY)
    survived_steady_monthly = steady_monthly * (1 - MONTHLY_CHURN_STEADY)
    survived_fresh_annual   = fresh_annual   * (1 - ANNUAL_CHURN_M1)
    survived_fresh_monthly  = fresh_monthly  * (1 - MONTHLY_CHURN_M1)

    # Survivors (steady + former fresh) become next month's steady pool
    steady_annual_eom  = survived_steady_annual  + survived_fresh_annual
    steady_monthly_eom = survived_steady_monthly + survived_fresh_monthly
    # This month's new converts become next month's fresh pool
    fresh_annual_eom   = new_annual
    fresh_monthly_eom  = new_monthly

    annual_eom  = steady_annual_eom  + fresh_annual_eom
    monthly_eom = steady_monthly_eom + fresh_monthly_eom

    rows.append({
        'month'                    : label,
        'active_annual_bom'        : round(annual_bom),
        'active_monthly_bom'       : round(monthly_bom),
        'total_active_bom'         : round(total_bom),
        'new_sites_created'        : round(new_sites),
        'new_premium_conversions'  : round(new_conv, 1),
        'new_annual_converts'      : round(new_annual, 1),
        'new_monthly_converts'     : round(new_monthly, 1),
        'renewing_annual_sites'    : renewing_sites,
        'rev_renewal_usd'          : round(rev_renewal),
        'rev_existing_gpv_usd'     : round(rev_existing),
        'rev_day0_new_usd'         : round(rev_day0_new),
        'total_monthly_rev_usd'    : round(total_rev),
        'ai_cost_free_usd'         : round(ai_cost_free),
        'ai_cost_premium_usd'      : round(ai_cost_prem),
        'total_ai_cost_usd'        : round(total_ai_cost),
        'net_margin_usd'           : round(net_margin),
        'net_margin_pct'           : round(margin_pct, 1),
        'active_annual_eom'        : round(annual_eom),
        'active_monthly_eom'       : round(monthly_eom),
        'total_active_eom'         : round(annual_eom + monthly_eom),
    })

    steady_annual  = steady_annual_eom
    steady_monthly = steady_monthly_eom
    fresh_annual   = fresh_annual_eom
    fresh_monthly  = fresh_monthly_eom

df = pd.DataFrame(rows)
df['cumulative_revenue_usd']   = df['total_monthly_rev_usd'].cumsum().round(0)
df['cumulative_ai_cost_usd']   = df['total_ai_cost_usd'].cumsum().round(0)
df['cumulative_net_margin_usd'] = df['net_margin_usd'].cumsum().round(0)

# ── Summary ───────────────────────────────────────────────────────────────────
total_12m_rev    = int(df['total_monthly_rev_usd'].sum())
total_12m_cost   = int(df['total_ai_cost_usd'].sum())
total_12m_margin = int(df['net_margin_usd'].sum())
avg_margin_pct   = round(total_12m_margin / total_12m_rev * 100, 1)
final_active     = int(df['total_active_eom'].iloc[-1])
month1_rev       = int(df['total_monthly_rev_usd'].iloc[0])
month12_rev      = int(df['total_monthly_rev_usd'].iloc[-1])
month1_margin_pct = df['net_margin_pct'].iloc[0]
month12_margin_pct = df['net_margin_pct'].iloc[-1]

print("=" * 72)
print("  12-MONTH REVENUE FORECAST  (Jul 2026 – Jun 2027)  [v9 — Renewal Waves + 15% churn]")
print("=" * 72)
print(f"  Starting active premium sites : {ACTIVE_ANNUAL + ACTIVE_MONTHLY:,}")
print(f"  Ending   active premium sites : {final_active:,}")
print(f"  Monthly revenue  Jul 2026     : ${month1_rev:>10,}")
print(f"  Monthly revenue  Jun 2027     : ${month12_rev:>10,}")
print(f"  Total 12-month revenue        : ${total_12m_rev:>10,}")
print(f"  Total 12-month AI cost        : ${total_12m_cost:>10,}")
print(f"  Total 12-month net margin     : ${total_12m_margin:>10,}")
print(f"  Avg net margin %              :  {avg_margin_pct:>9}%")
print(f"  Margin range                  :  {month1_margin_pct}% (Jul) → {month12_margin_pct}% (Jun 2027)")
print("=" * 72)
total_renewal_rev = int(df['rev_renewal_usd'].sum())
print("Key model changes vs v8:")
print(f"  Renewal wave model      : $166 lump-sum at month 12 (was amortized $13.83/mo)")
print(f"  Renewal churn           : 15% at renewal date")
print(f"  Annual survival rate    : 71.3% (M1 10.9% + 2%/mo × 11 months, W11 validated)")
print(f"  MONTHLY_REV_ANNUAL      : $7.93 GPV-only (was $21.76 total)")
print(f"  12-month renewal rev    : ${total_renewal_rev:,} ({total_renewal_rev/total_12m_rev*100:.1f}% of total revenue)")

print("\nFull monthly breakdown:")
print(df.to_string())
