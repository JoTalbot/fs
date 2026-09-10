# FS Resource Fabric Model

The Genesis model requires a precise answer to the phrase "the user gets the
whole world": the user gets a **single logical control surface over resources
for which the user has authority**, not unrestricted ownership of every joined
machine.

## Node admission

A node contributes to the fabric only after:

`identity -> discovery -> trust decision -> policy admission -> capability verification -> resource offer`

A discovered node can advertise capabilities without becoming trusted.

## Resource offers

Resources are offered explicitly as bounded offers:

`Offer = node + capability + quantity + unit + share class + lease + privacy boundary`

Share classes are PRIVATE, SHARED, LEASED, FEDERATED and PUBLIC.
PRIVATE resources never enter the matching pool. Private data is never implied
by a storage or compute offer.

## Reciprocal computing

Suppose Node A is an idle Windows laptop and Node B is an Android phone.

- A may offer a bounded Windows application environment and selected compute.
- B may offer selected compute, storage, sensors or other capabilities.
- B can request a compatible Windows application session.
- The scheduler can place execution on A if trust, policy, resources, network,
  application compatibility and licensing permit it.
- A can simultaneously request an Android environment if an admitted B backend
  can provide the required semantics.

This is resource reciprocity, not magical hardware fusion. The network,
latency, licensing, GPU features, device APIs and application architecture
still exist. Physics remains annoyingly employed.

## Session abstraction

The user's local device becomes a **presentation endpoint** when execution is
remote. Input, output, display, audio, clipboard and other session channels
are separate capabilities and must be admitted individually.

The logical identity is:

`ApplicationSessionID -> Application -> Environment -> Placement -> PresentationEndpoint`

Placement may change while the logical session remains stable, subject to the
backend's migration/checkpoint capabilities.

## Fairness and safety

A production fabric needs:

- quotas and resource budgets;
- lease expiration and revocation;
- per-user/per-node accounting;
- privacy classes;
- data-locality constraints;
- bandwidth/latency constraints;
- energy and thermal limits;
- failure-domain awareness;
- admission control;
- cancellation and compensation;
- provenance of allocations;
- explicit billing/reward semantics if an economic layer is added.

No resource is silently consumed merely because it appears idle.

## Global logical namespace

The eventual interface can make heterogeneous resources appear as one logical
computer:

`fs:///world/users/...`
`fs:///world/apps/...`
`fs:///world/resources/...`
`fs:///world/sessions/...`

The namespace is semantic. Physical placement remains visible as metadata and
is used by the scheduler.

## Bootstrap-to-world path

`tiny bootstrap`
`  -> local identity`
`  -> explicit resource policy`
`  -> node admission`
`  -> capability advertisement`
`  -> resource fabric`
`  -> logical Computer`
`  -> universal application/session`
`  -> distributed placement`
`  -> verified result`
`  -> FS World`

This makes the tiny starting artifact genuinely powerful without making it
privileged. Its power comes from the system it joins and the authority the
operator explicitly grants.
