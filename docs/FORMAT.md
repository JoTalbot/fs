# FSOV v1 Carrier Format

FSOV is an append-only envelope. The host file's original bytes precede the envelope.

```text
+---------------------------+
| host/original file bytes  |
+---------------------------+
| FSOV fixed header         |
+---------------------------+
| authenticated shard body  |
+---------------------------+
| FSOV footer               |
+---------------------------+
```

## Header

The reference implementation reserves a fixed binary header containing:

- magic: `FSOV`
- format version
- header length
- container UUID
- generation
- shard index
- data shard count
- parity shard count
- payload length
- flags
- key version
- nonce/AEAD metadata
- header checksum

All multi-byte integers use network byte order.

## Footer

The footer contains the envelope length and a footer checksum so an auditor can locate and validate the most recent block without trusting mutable host metadata.

## Compatibility

A carrier profile is responsible for determining whether an FSOV envelope can safely be appended. Unknown or structurally unsafe formats must be rejected. Text profiles must use a format-specific representation rather than blindly appending arbitrary binary bytes.

## Generations

A container generation is immutable. Repairs create a new carrier assignment for the missing shard while preserving the logical generation. A later write creates the next generation.

## Integrity

The authenticated shard body plus its manifest hash are required for acceptance. Hash mismatch causes quarantine, not automatic overwrite.
