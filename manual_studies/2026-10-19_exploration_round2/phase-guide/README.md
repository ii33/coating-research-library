# Fixed-plane reflection homotopy screening

Read 研究报告.md for the evidence and negative conclusion. This standalone research package does not modify or publish the production software.

Reproduce with:

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_phase.py
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python withdrawal_and_counterexamples.py
    python -m unittest -v test_phase
    python write_report.py

The final 2049-point grid is a nested densification; it is used for explicit post-run archive selection, not an untouched statistical holdout or continuous proof.
