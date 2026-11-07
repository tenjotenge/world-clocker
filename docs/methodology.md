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
