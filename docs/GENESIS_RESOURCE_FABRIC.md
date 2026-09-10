# FS Genesis Resource Fabric

## Purpose

FS can begin from an extremely small, user-controlled bootstrap component. The
component does not contain the whole system. It establishes identity, discovers
permitted capabilities, connects to an admitted FS control plane/federation,
and loads only the modules required for the current intent.

The result is a **logical computer/world entry point** rather than a claim that
one device literally owns every resource on Earth.

## Genesis principle

A user may start FS on a server, PC, laptop, phone, ARM board, IoT device, VM,
or another supported platform with the smallest practical bootstrap:

`bootstrap -> identity -> admission -> capability discovery -> policy -> resource fabric -> intent`

After admission, the device can contribute selected resources and consume
resources contributed by other admitted nodes.

### Important distinction

- **Available to the world** is not the same as **owned by the user**.
- **Discoverable** is not **trusted**.
- **Capability** is not **permission**.
- **Idle capacity** is not automatically shareable capacity.
- **Private data** is never published merely because a device joins.
- **Remote execution** is possible only when the workload, backend, license,
  policy, network path and security boundary support it.

## Resource reciprocity

The central abstraction is a bidirectional resource fabric:

`User A device <-> FS Resource Fabric <-> User B device`

A laptop may contribute idle CPU, GPU, storage, memory or an explicitly shared
application environment. A phone may contribute compute, sensors, storage,
network or other explicitly admitted capabilities. Scheduling can then place
work where the declared semantics and constraints are best satisfied.

The contribution is governed by explicit leases, quotas, revocation, privacy
boundaries, failure domains and accounting. A device remains usable by its
owner; FS only allocates the portion admitted by policy.

## Universal application experience

A user-facing application is represented as a logical application/environment,
not as a platform-specific process. The control plane selects an execution
location and a compatible backend.

Example:

`Android client -> intent: use Windows application -> capability match -> Windows node -> isolated application environment -> verified remote session -> Android presentation`

The Android device does not magically execute a Windows binary. It presents a
logical application session whose execution may occur on a compatible Windows
node. The same model works in the opposite direction when an Android-native
runtime is the best admitted backend.

## What the user should experience

The long-term UX target is deliberately simple:

1. Install/start a tiny FS bootstrap.
2. The bootstrap creates or imports a local identity.
3. The user explicitly chooses what the device contributes.
4. FS joins the permitted resource fabric.
5. The user sees a single logical namespace and resource view.
6. An intent such as `run application`, `process data`, or `open environment`
   is compiled into a verified plan.
7. The scheduler chooses the best admitted execution resources.
8. The result is presented through the user's local device/session.

The complexity belongs below the interface. Humans have already suffered
through enough configuration dialogs.

## Scaling model

The same semantic model must work for:

- one device;
- a household or small LAN;
- a trusted private cluster;
- a company or lab;
- a federated collection of independent users;
- a heterogeneous global fabric.

Scale changes placement, trust, latency, accounting and failure behavior, but
must not change the core object, capability, authority, transaction or
verification semantics.

## Resource contribution classes

### PRIVATE
Never exposed to the fabric.

### SHARED
Explicitly available for selected workloads or users.

### LEASED
Temporarily allocatable under bounded conditions.

### FEDERATED
Available across a trusted federation according to policy.

### PUBLIC
Intentionally exposed by the operator. Public does not mean trusted.

## Minimum viable bootstrap

The first practical implementation should be intentionally boring:

- small executable;
- local configuration and identity;
- secure outbound connection to a known control endpoint;
- capability advertisement;
- explicit admission/policy receipt;
- heartbeat and health reporting;
- worker launcher through supported OS mechanisms;
- no kernel replacement;
- no stealth persistence;
- no arbitrary remote command execution;
- no automatic publication of user files or credentials.

Everything else is a module loaded only when needed.

## Architectural consequence

This concept turns the existing FS Unified Computer and Resource Mesh into a
clear **Genesis-to-World path**:

`tiny bootstrap -> admitted node -> resource contribution/consumption -> logical Computer -> distributed execution -> FS World`

The bootstrap is therefore an entry point into the system, not the system
itself. This keeps startup tiny while allowing the architecture above it to
become extremely large.
