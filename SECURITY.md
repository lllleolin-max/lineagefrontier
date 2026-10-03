# Security and reporting

Only read regular local files under the caller's explicit root. Relative traversal, absolute/drive/UNC paths and root-escaping symlinks are rejected. Reads stream with a per-file limit; metadata changes during one hash fail. The package never follows remote URIs, executes instructions, modifies input files, verifies signatures or certifies authenticity. Builder IDs are untrusted text; recorded SHA-256 detects differences only relative to supplied records. A malicious record can lie about omitted dependencies, costs, equivalence and builder identity.

Use a stable read-only snapshot supplied by a trusted caller. Path resolution and metadata checks are not an OS sandbox and do not defend a hostile concurrent filesystem writer or supply an atomic multi-file view. Catalog actions and provenance completeness are caller policy inputs; successful planning does not prove successful builds, scientific validity or current remote content. Report JSON contains file digests, IDs and supplied revocation explanations; avoid sensitive names/reasons. File contents are not included.

Report a reproducible problem to repository maintainers using an issue without sensitive files, credentials or private paths. For sensitive reports, request a private channel first; none is fabricated here. No external audit or verified security contact is claimed. Include Python/platform, manifest subset, expected behavior and a minimal synthetic reproduction.

Snapshot/report digests prevent accidental association or mutation errors. They are unkeyed and are not signatures, identity verification or protection against a malicious report author who recomputes them. Planner inputs should come from a fresh `assess()` result for the same inventory/provenance and stable local filesystem snapshot.

The planner's descendant/action masks are constructed locally after assessment
association/integrity checks for every invocation and are discarded afterward.
They are not authenticated generation IDs, a persistent cache or a concurrency
protocol. All historical descendants of selected atomic co-outputs remain
excluded from reuse. The independent checker still performs its own complete
historical invalidation and prerequisite replay. Limits remain 1000 artifacts,
10000 edges and at most 18 relevant actions for exact subset selection. Bitset
precomputation uses additional memory and does not remove exponential selection
or dense cause/witness output costs; use process limits for hostile workloads.
