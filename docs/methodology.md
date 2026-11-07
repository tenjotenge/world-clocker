# Behavioral pilot methodology

The unit of observation is a binary decision. Each of eight factorial
priority prompts, a neutral control and a style-only control sees every probe.
The six scenario families span risk, resource sharing and time preference.
Each family contains a base, paraphrase and counterfactual. The generator
uses no scenario text. Three families are reserved for evaluating whether
differences replicate beyond the discovery families. These are hand-written
parallel families and should be treated as a pilot holdout. Option labels are
balanced within cells up to one trial and canonicalized before scoring.
The local smoke config uses a two-prompt subset for integration testing.

## Estimators

- **Effective rank.** Each complete configuration contributes a row of
  estimated probabilities of action 1 on base and paraphrase probes. Center
  columns and use equal weights without variance scaling. The report contains
  the sample covariance spectrum, the exponential entropy of normalized
  covariance eigenvalues and their participation ratio. A zero spectrum
  has rank zero by convention. Rank is bounded by the smaller of feature
  count and configuration count minus one.
- **Conditional entropy.** Binary plug-in entropies under uniform
  configuration and probe weights decompose total decision entropy into
  within-configuration entropy given the probe, configuration information
  given the probe, and probe information. Finite repeats bias the estimates,
  especially apparent configuration information for random decisions.
  A random policy can also produce a broad covariance spectrum through
  estimation noise. Read descriptive rank alongside the stability measures.
- **Stability.** Repeat agreement uses all distinct pairs of draws in a cell.
  Paraphrase agreement is the expected match probability between independent
  draws from base and paraphrase cells. A configuration must pass both
  agreement gates on each split. Counterfactual shifts are reported separately.
- **Repertoire.** Mean binary total variation is the average absolute
  difference in choice probabilities. The packing instead uses conservative
  replicated distance. Per probe, split repeat indices into two halves.
  Keep the smaller absolute difference if both halves agree on direction.
  Average by split and take the smaller split distance. In stable ID order,
  accept a gated candidate only when its distance to every accepted candidate
  is at least epsilon. This greedy packing is a threshold-dependent lower
  bound on the largest packing of the measured candidates.
- **Discovery.** Prefix packing sizes and marginal discoveries describe the
  finite candidate set. The 95% band uses percentiles across shuffled candidate
  orders. It measures order sensitivity. Rank and mean repeat agreement have
  separate exploratory 95% percentile bands using a scenario-family bootstrap
  stratified by split. These bands condition on the observed configurations
  and repeats. Six families give weak uncertainty resolution.

Primary scores require complete base and paraphrase cells. Counterfactual
shifts use complete counterfactual cells and report their family coverage.
Coverage and parsing failures are
reported, including exclusions. Missingness correlated with configuration or
scenario can bias complete-case results. Compare matched, complete runs under
a common plan and report inference deviations. Equal temperature values need
empirical calibration before interpreting them as equivalent sampling entropy.

## Interpretation and validation

This pilot measures accessible behavior for a specific prompt search,
probe bank and inference setup. Rank is a spectral summary. Packing counts
separated prompt-conditioned policies within that experiment. A plateau
describes the sampled search. Storage, parameter count, population size,
internal representations and functional specialization require separate
evidence. Explicit priority instructions can confound the measurement with
prompt compliance. Neutral and style-only prompts and synthetic policies
are sanity checks. Blind external probes, weaker steering controls,
threshold sensitivity, quantization comparisons and downstream validation
are needed before interpreting cross-model differences as a model property.

## v0.2 factorial design

The pilot crosses four binary factors with a three-level verification
factor to obtain 48 profiles. Each profile has two prompt treatments.
Strong prompts state behavioral priorities directly. Weak prompts
describe previous roles and work without instructing the model to favor
an option. The third level leaves the verification cue unspecified. Four
non-steering control wordings bring the total to 100. The structured
oracle follows binary axes and maps the unspecified level to its default.
The random oracle selects independently using the planned trial seed.
The constant oracle always selects the same canonical action.

Ten scenario families cover risk, resource sharing, time preference,
information disclosure, and verification. Each family contributes a
base, paraphrase, and counterfactual probe. Five parallel families are
held out from the discovery distance, with one held-out family per
axis. These are authored parallel probes. They need independent
validation before they can support broad generalization claims.

The v2 raw estimator tolerates missing primary responses when every
primary cell retains at least 75% of scheduled repeats and both
preassigned repeat halves. Repeat agreement uses the observed number of
valid draws, and distances retain the original half assignments. The
v0.1 estimator keeps its complete-cell rule. Missing decisions can bias
both estimators, especially if errors favor a particular choice or prompt.

## Historical calibration v1

Scoring v1 uses the weak-prompt repertoire only. Among weak prompts
that pass the repeated and paraphrase agreement gates on both splits,
collapse identical repeat-half choice probability vectors and greedily
pack candidates in lexicographic vector order. Each pair must meet
the replicated distance threshold on both discovery and held-out
families. Strong and neutral packs are reported separately as diagnostics.
Stable weak repertoire gets weight 1. Descriptive rank and entropy get
weight 0. Adding an unstable prompt or an exact measured duplicate does
not increase the pack. Finite-sample coincidences and near duplicates
can still affect it.

Let K be the weak pack size, Kref the upper anchor repertoire, and Pmin
and Pref the two calibration populations. The provisional normalized
quantity is max(0, K - 1) / (Kref - 1). Interpolate linearly between
log(Pmin) and log(Pref) using that quantity, then exponentiate and round.
Calibration v1 defaults to 500 at zero or one policy and 40,000,000 at
40 policies. The default structured synthetic control has 32 distinct
policies, below the New York City and Tokyo aspirational references.
These are illustrative design choices. No benchmark observations
establish a frontier range. Extrapolated scores carry a warning and
retain their numerical value. The city label is the catalog entry
with minimum absolute log-population distance.

A numeric score requires a finished v0.2 pilot with all 100 planned
prompts, 30 probes, at least four repeats, and at least 95% valid
decisions overall. The gates require distance of at least 0.2 and
stability of at least 0.8. At least 36 weak, 36 strong, and two neutral
prompts must have scorable primary cells. All numeric estimates are
provisional. Confidence is exploratory for model runs, synthetic-control
for mock runs, and insufficient-evidence when the score is uncalibrated.
The population interval reflects sensitivity to greedy packing order
on the observed data. The raw family bootstrap reflects probe sampling
sensitivity for rank and repeat agreement. Neither measures population
calibration error.

The v1 catalog uses U.S. Census incorporated-place boundaries for
small settlements and urban-area boundaries for larger cities. Each
entry carries its source, geography and reference year. Urban areas
represent settlement footprints. The UN Degree of Urbanization and
U.S. Census criteria delineate these footprints differently. Tokyo
and New York City are UN urban areas in the matching catalog. The
separate metropolitan Tokyo aspirational tier uses the four-prefecture
definition from Japan's preliminary 2025 census. City labels are
illustrative analogies sensitive to the available references and their
boundaries. [U.S. incorporated places](https://tigerweb.geo.census.gov/tigerwebmain/Files/acs26/tigerweb_acs26_incplace_2020_tab20_ny.html) · [U.S. urban areas](https://www.census.gov/programs-surveys/geography/guidance/geo-areas/urban-rural/2020-ua-facts.html) · [UN urban areas](https://population.un.org/wup/assets/Publications/undesa_pd_2025_wup2025_summary_of_results_final.pdf) · [Japan census](https://www.stat.go.jp/english/info/news/20260625.html)

## v0.3 population rescaling

The saved v0.2 controls recovered 32, one and zero stable weak policies
for the structured, constant and random oracles. The v1 formula mapped
those counts to 3,947,280, 500 and 500. The observed control separation
validates the mechanics of packing and rejection. It supplies no
real-model population anchor. The available live runs were underpowered
smoke tests and supply no complete model score distribution.

v0.3 keeps the experiment, eligibility requirements and scoring v1 pack.
Calibration v2 first computes **I = max(0, K - 1)** in excess-policy units,
where one unit is one additional distinguishable policy beyond a single
baseline policy. The index has no fixed upper bound. Then it computes
**P = 100 × (1 + I)²**. The floor of 100 sets the illustrative scale
for zero or one stable policy. The square makes a doubling in
baseline-adjusted repertoire correspond to a fourfold population change.
Both choices are conventional and fixed for v2. They were neither fitted
to synthetic controls nor tuned to model names or desired populations.
For comparison, v1 used **I = max(0, K - 1) / 39** and
**P = round(500 × (40,000,000 / 500)^I)** at its default settings.

The 48 weak prompts permit at most 49 raw integer counts and 48 distinct
population values. The pilot has not established how many counts can be
distinguished reliably across independent runs. The largest possible
pilot output is 230,400, so the upper conceptual tiers remain outside
its evidence range. London (10,416,000, UN urban area, 2025) is an
aspirational reference alongside New York City and metropolitan Tokyo.
The transform itself has no city cap. Larger input counts are hypothetical
until a future protocol can measure them. Catalog v1 remains available
with calibration v1. [UN World Urbanization Prospects 2025](https://population.un.org/wup/assets/Publications/undesa_pd_2025_wup2025_summary_of_results_final.pdf)

Under v2 the structured oracle maps to 102,400 and the constant and
random oracles map to 100. These are mathematical diagnostics.
An exact output or a zero-width packing-order band says nothing about
calibration validity. The population band maps the 2.5th and 97.5th
percentiles of repertoire over shuffled packing orders on the same
observations. It does not estimate differences between independent
inference runs or uncertainty in the choice of calibration. Quantization
comparisons need replicated matched runs to assess whether observed
differences exceed experimental variability.

### Generational comparisons

Parameter count measures the number of learned coefficients. Architectural
capacity concerns the structures a design can represent. Realized behavioral
complexity is the stable differentiation observed under this protocol.
Behavioral efficiency asks how much realized complexity training produces
within a resource budget. Population-equivalent interpretation gives that
measured differentiation a geographic metaphor. Changes in training,
architecture, or post-training could let a newer 7B model express far
more stable policies than an older 7B model. The opposite ordering is
also possible on these probes. Parameter count, release date, specialization,
and quantization belong in explanatory metadata. They carry no scoring
weight, and the historical population ranges are hypotheses to compare
against evidence rather than calibration labels.

## Research bibliography

- Pugh, Soros and Stanley motivate future diversity-driven candidate search.
  [Quality Diversity](https://doi.org/10.3389/frobt.2016.00040)
- Bettini, Shankar and Prorok motivate comparing policies on common inputs.
  Their multi-agent setup differs from this prompt-conditioned experiment.
  [System Neural Diversity](https://www.jmlr.org/papers/volume26/24-1477/24-1477.pdf)
- Park et al. study interactive agents and simulation design.
  [Generative Agents](https://arxiv.org/abs/2304.03442)
- Santurkar et al. motivate external validation and separate tests for
  steerability and population fidelity.
  [Whose Opinions Do Language Models Reflect?](https://arxiv.org/abs/2303.17548)
- Tishby, Pereira and Bialek provide a starting point for future work on
  bounded policy representations and information retention.
  [The Information Bottleneck Method](https://arxiv.org/abs/physics/0004057)
- Roy and Vetterli motivate entropy-based spectral summaries. This pilot
  uses the covariance eigenvalues rather than the centered feature matrix's
  singular values as the spectrum.
  [The Effective Rank](https://infoscience.epfl.ch/bitstreams/2907ab8a-23f5-481d-bb07-1d56a3f3511f/download)
