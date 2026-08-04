# Presentation-ready result tables

Outcome counts cover intrinsic selection configurations. The best rows consider both intrinsic and matched scores, consistent with the Phase 5 report. No configuration reached `Recommend`; the best rows are `Explore`, not confirmed winners.

## Outcome counts

| Dataset | Recommend | Explore | Abstain |
|---|---:|---:|---:|
| ACME | 0 | 21 | 6 |
| CIC-IDS2017 | 0 | 19 | 8 |
| UNSW-NB15 | 0 | 13 | 14 |

## Highest-AP selection configuration

| Dataset | Score | Representation + scorer | Hypothesis | AP | Recall@100 | Precision@100 | Prevalence | Lift@100 | Status |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| ACME | matched | graphsage trained + isolation forest | Local State Modification and Data Access | 0.0498 | 0.6667 | 0.0200 | 0.0036 | 5.49x | Explore |
| CIC-IDS2017 | intrinsic | raw session + isolation forest | Network Flow Volume and Throughput | 0.0373 | 0.0000 | 0.0000 | 0.0060 | 0.00x | Explore |
| UNSW-NB15 | intrinsic | dominant style trained + dominant joint reconstruction | Historical Connection Frequency Context | 0.5845 | 0.0000 | 0.0000 | 0.2278 | 0.00x | Explore |

## Reading note

The stars in Figure 4 identify the highest-AP configuration for each dataset. CIC-IDS2017 and UNSW-NB15 illustrate the central evaluation lesson: their highest-AP configurations retrieved no malicious items in the first 100 reviews.
