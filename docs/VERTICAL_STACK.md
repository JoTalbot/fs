# FS Vertical Stack

## Purpose

FS is designed as a vertically composable system substrate rather than a component locked to one layer of a conventional operating system.

The architecture spans the path from hardware and firmware to user intent and can operate at different deployment levels without changing the logical object model.

## Vertical model

```text
USER / INTENT
     |
FS EXPERIENCE
     |
APPLICATION / SERVICE
     |
UNIVERSAL RUNTIME
     |
ENVIRONMENT
     |
FS COMPUTER
     |
META SCHEDULER
     |
CONTROL / RESOURCE / DATA FABRICS
     |
FS OBJECT GRAPH
     |
REALITY ENGINE
     |
HARDWARE FABRIC
     |
FIRMWARE / BOOT
     |
PHYSICAL HARDWARE
```

Cross-cutting planes operate across the stack:

```text
Security
Identity
Policy
Knowledge
Simulation
Observability
Recovery
Provenance
```

## Deployment levels

The same logical FS architecture may be deployed as:

1. an application on an existing host;
2. a resident runtime and control plane;
3. a container or sandbox;
4. a virtual machine;
5. a bootable/system environment;
6. a distributed logical computer;
7. a World-level control plane managing multiple Computers.

Moving to a stronger level requires an explicit deployment mode and supported platform mechanism. A user-space installation does not silently acquire kernel, firmware, or administrative authority.

## Hardware Fabric

The lowest FS layer models measurable hardware capabilities through adapters:

- CPU and topology;
- memory and NUMA characteristics;
- storage and I/O;
- GPU and accelerators;
- PCIe and device capabilities;
- network interfaces and links;
- display, audio and input;
- power, battery and thermal state.

Hardware identity and capability fingerprints are distinct from logical FS object identity.

## FS Hardware Abstraction Layer

Platform-specific hardware behavior belongs behind versioned capability-aware contracts. The HAL reports what is actually available instead of exposing a fictional uniform machine.

A capability record may include:

```text
identity
architecture
topology
capacity
features
performance hints
health
power/thermal state
virtualization support
I/O capabilities
firmware capabilities
```

## FS Time Fabric

Distributed operation requires a first-class time model:

```text
physical time
monotonic time
logical event time
snapshot time
simulation time
```

Time ordering must not depend on wall-clock equality across nodes. Transactions, events, snapshots, replay and simulation use explicit ordering and correlation metadata.

## FS Reality Engine

The Reality Engine continuously reconciles the modeled world with observations:

```text
OBSERVE
  -> NORMALIZE
  -> UPDATE OBJECT GRAPH
  -> COMPARE DESIRED/ACTUAL
  -> PLAN
  -> SIMULATE WHEN REQUIRED
  -> EXECUTE TRANSACTION
  -> VERIFY
  -> COMMIT OBSERVED RESULT
```

The model is never treated as proof that reality matches it.

## Object Graph

The Object Graph is the common structural model connecting all FS layers. Objects include Computers, Nodes, Resources, Environments, Applications, Processes, Services, Volumes, Devices, Networks, Sessions, Snapshots and Packages.

Relationships include:

```text
contains
hosts
provides
requires
depends_on
attached_to
located_on
compatible_with
replicates
migrates_to
observed_as
```

Logical identity remains independent of physical placement.

## Meta Scheduler

Scheduling is hierarchical:

```text
World Scheduler
    -> Computer Scheduler
        -> Node Scheduler
            -> Environment Scheduler
                -> Runtime Scheduler
                    -> Process/Task Scheduler
```

Higher layers choose intent and topology. Lower layers make local decisions inside constraints inherited from above. No lower scheduler may silently expand the authority granted by a higher policy.

## Intent Layer

The top layer accepts desired outcomes instead of requiring users to specify implementation details.

Example:

```text
Intent:
  run application X
  interactive: true
  private-data: true
  network: restricted
  recovery: required
```

FS derives requirements, selects an environment and runtime, reserves resources, chooses placement, and executes a verifiable plan.

## Recursive composition

A Computer may consume another logical Computer as a resource or execution backend:

```text
FS World
  -> Computer A
      -> Resource
          -> Computer B
              -> Environment
                  -> Application
```

This recursion is logical. Each boundary still exposes explicit capabilities, identity, trust and policy.

## Architectural law

**FS must be able to move vertically without losing logical identity.**

The same Environment, Application, Volume or Session can be represented consistently whether it is backed by a local process, VM, remote node, or larger logical Computer, provided the selected backend supports the required semantics.

## Safety boundary

Vertical control never means unrestricted control. FS must not use the architecture to bypass host security, obtain hidden privileges, silently persist, harvest credentials, or inspect unrelated systems. Stronger authority is obtained only through explicit installation, authorization, isolation, boot, hypervisor or hardware mechanisms supported by the platform.
