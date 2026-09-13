# PHANTOMX MVP Control Plane

The control plane is the resumable mission ledger.

## Rules
- State transitions are explicit.
- A task is GREEN only when required evidence exists.
- Dependent tasks remain BLOCKED until their dependency is GREEN.
- Checkpoints must survive interruption.
- Historical evidence is append-only in spirit: do not silently rewrite claims.
- Live capital remains BLOCKED until final authorization gates are independently satisfied.

## Active bootstrap task
`P0-MVP-0.1` Clean architecture/bootstrap.

## Next engineering gate
`P0-MVP-1.1` Chain adapter and live-state truth layer.
