# Architecture

## Objective
PHANTOMX is a safety-first DeFi arbitrage control plane plus execution system. The MVP is intentionally narrow: one chain, one flash-liquidity provider, real on-chain state, and direct two-pool arbitrage.

## Pipeline
DISCOVER -> QUOTE -> VERIFY -> ECONOMIC CHECK -> SIMULATE -> AUTHORIZE -> EXECUTE -> RECEIPT -> RECONCILE -> REALIZED PNL

## Planes
- Intelligence plane: market/pool discovery, candidate generation, route scoring.
- Truth plane: deterministic quote validation, fee/gas/slippage/price-impact calculation, provider and callback authenticity checks.
- Execution plane: atomic flash-loan route execution with fail-closed controls.
- Evidence plane: immutable-ish event records, test reports, CI artifacts, state checkpoints.
- Mission-control plane: task lock, dependency graph, gate status, next-task selection, recovery state.

## V2 MVP
Direct A -> B -> A using two real pools/venues. No hardcoded profitability. Pool state, fee tiers and amounts come from current on-chain/provider data.

## V3 expansion
Triangular/multi-hop graph routing A -> B -> C -> A. V3 is not admitted into live authorization until the V2 control plane and executor invariants are proven.

## AI swarm
Specialists may propose candidates or analyses, but no agent receives unrestricted execution authority. Deterministic gates are the final authority. Agent memory is represented by checkpointed project state and evidence references.

## Zero-cost constraint
No mandatory paid SaaS, hosted server, proprietary RPC, or paid model is required for the architecture. Optional services can be added only behind adapters and must never become single points of failure.

## Speed constraint
Use async I/O, bounded concurrency, cached static metadata, incremental state updates and deterministic pre-filters before expensive simulation. Correctness always outranks speed.
