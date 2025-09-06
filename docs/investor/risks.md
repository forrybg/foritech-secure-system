# Risk Register

| ID | Risk                         | Likelihood | Impact | Mitigation                                  |
|----|------------------------------|------------|--------|----------------------------------------------|
| R1 | PQC libs/API changes         | M          | M      | Pin versions; adapters; monitor OQS          |
| R2 | Performance regressions      | M          | M      | Benchmarks; optional hybrid modes            |
| R3 | User complexity              | M          | M      | Tutorials; one-click demos                   |
| R4 | Security misconfiguration    | L          | H      | Safe defaults; SECURITY.md; code review      |
| R5 | Resource/time overrun        | M          | M      | Scope guard; milestones; weekly review       |
| R6 | Upstream compatibility drift | L          | M      | Test matrix across versions                  |
