# MVP ROADMAP

## Gate 0 - Clean bootstrap
- Canonical mission statement
- State/control plane
- No-secret policy
- CI skeleton
- deterministic schemas

## Gate 1 - Market truth
- chain adapter
- pool registry
- live block/quote reader
- freshness checks
- pair discovery

## Gate 2 - Economic truth
- exact fee accounting
- gas estimation
- slippage and price-impact bounds
- conservative MEV/risk buffer
- minimum net profit threshold > $0.50
- no fixed loan-size assumption

## Gate 3 - Provider/executor truth
- provider authenticity
- callback sender validation
- exact repayment semantics
- allowance lifecycle
- reentrancy protection
- active-state cleanup

## Gate 4 - Deterministic simulation
- fork/integration testing
- negative and adversarial paths
- insufficient repayment
- stale quote
- unauthorized callback
- gas shock
- slippage breach
- state corruption

## Gate 5 - Safe execution harness
- signed transaction interface without repository-stored secrets
- nonce/gas controls
- preflight authorization
- fail-closed broadcast guard
- receipt capture

## Gate 6 - Independent reconciliation
- receipt parser
- wallet balance snapshot
- token balance delta
- realized PnL calculation
- evidence bundle

## Gate 7 - V3 expansion
- graph construction
- triangular paths
- fee-tier optimization
- multi-hop simulation
- V3 callback/provider semantics

## Goal gate
The project is not declared complete until a real, independently reconciled, conservative net positive result is proven. Software readiness is not profit realization.
