# 2026-10-21 coating-sim optical research results

This dated research package collects finished public findings on ultrabroadband antireflection, finite-audit validation, worker scaling, and broadband high-reflector search. It contains research reports and compact evidence only. It does not publish or modify the coating-sim software repository.

## Main findings

- The 48-run study reports finite sampled-model audit passes, not continuous-domain, experimental, or manufacturing certification. All six `ar_v_visible` rows are explicitly conditional on unknown extinction coefficient k being set to zero; do not treat them as unconditional material validation. See [the report](reports/cloud_48run_validation_zh.md) and [compact run evidence](evidence/public-audit-summary.json).
- Two-worker trials do not establish stable acceleration. The paired 3-seed samples include slower two-worker runs, and measured gains remain limited by startup, IPC, task selection, and shared-host variability. See [the worker study](reports/cloud_worker_pairing_zh.md) and [paired evidence](evidence/public-worker-audit-summary.json).
- The coarse-grid HR champion reached training min R=0.967129, then failed independent audit at R=0.212431 near 407.702 nm; a classical reference replay reached R=0.922099 and also failed the 0.98 floor. This is a narrow-notch counterexample, not a solved design and not an infeasibility proof. See [the failure report](reports/hard_hr_coarse_grid_failure_zh.md), [compact audit evidence](evidence/hard-hr-evidence-summary.json), and [spectrum](figures/reflection-spectrum.svg).
- Two fresh production-entry searches, trained at 5 nm and 1 nm respectively, each hit the 120 s cancellation boundary. Their returned-candidate independent audit minima were 0.959279 and 0.957951, both below 0.98. The old narrow-notch candidate still fails in the new audit at about 0.212431. No hard case is reported as solved. See [the production report](reports/hard_hr_production_failures_zh.md) and [compact production evidence](evidence/production-run-summaries.json).
- The ultrabroadband AR report synthesizes cited literature and engineering boundaries; it reports no new coating optimization, fabrication, or experiment. See [the research note](reports/ultrabroadband_ar_research.md).

## Evidence and scope

The summaries retain concise run identifiers, paired request/candidate hashes, finite audit outcomes, and relevant timing/resource fields. Per-process PIDs, detailed batch traces, repeated event payloads, raw logs, large archives, and high-volume candidate data are intentionally excluded. The selected classical-screen prescription and small evidence summaries are retained for traceability.

These files reflect research computations under specified finite models and budgets. None is an experimental, continuous-spectrum, manufacturing-tolerance, or production qualification certificate.
