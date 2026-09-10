# Resource Fabric Vertical Slice

This document defines the first executable reference slice of the FS Unified Computer idea.

## Goal

Prove the core semantic loop without touching a host operating system:

```text
application requirements
    -> capability matching
    -> admitted node selection
    -> logical application session
    -> independent presentation endpoint
    -> simulated execution
    -> observable result
```

The slice intentionally uses an in-memory federation. It is a reference model and a conformance target, not a production network daemon.

## Components

### FS-IR

`fs_overlay.ir` provides a compact intermediate representation for intent, requirements, plans, transactions, execution and observation. Validation checks structure and declared verification conditions. FS-IR never grants authority.

### Capability matching

`fs_overlay.matching` compares declared requirements with measurable offers. It reports missing, insufficient and incompatible capabilities separately. Matching is deterministic and does not imply permission.

### Application session

`fs_overlay.session.ApplicationSession` gives an application a stable logical identity while keeping execution placement separate from presentation placement. Mobility is explicit through a declared mobility class.

### Presentation endpoint

`fs_overlay.presentation.PresentationEndpoint` models display, stream, input, audio and remote-desktop surfaces independently of where the application executes.

### Simulated federation

`fs_overlay.federation` models multiple admitted nodes and performs deterministic placement. It has no sockets, credentials, host mutation or privilege escalation.

## Example

A session requiring `windows-runtime` can be placed on a Windows-capable node while its presentation endpoint is an Android display. The reference model therefore proves the semantic relationship without pretending that an Android device can execute an arbitrary Windows binary natively.

The production path will later lower this same semantic request through an admitted compatibility environment, such as a Windows VM/container/runtime where technically and legally supported, and then transport presentation through an explicitly admitted endpoint.

## Safety invariants

- capability does not imply authority;
- discovery does not imply trust;
- execution and presentation are separate capabilities;
- private resources are not shared by default;
- offline nodes cannot be selected;
- simulation performs no host mutation;
- unsupported compatibility fails rather than silently changing semantics.

## Next vertical increments

1. real FS-IR plan compiler;
2. capability negotiation and admission integration;
3. local node identity and signed advertisements;
4. localhost transport;
5. Linux and Windows capability adapters;
6. real two-machine federation;
7. checkpoint/restart semantics for mobile sessions;
8. Android presentation endpoint;
9. policy and authority enforcement at every boundary.
