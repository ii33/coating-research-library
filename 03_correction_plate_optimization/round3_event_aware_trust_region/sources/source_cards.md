# Primary sources and adoption boundaries

Access date: 2026-10-02 UTC. The formulas, step proof, interval construction, tests and figures in this package are original derivations on the inherited synthetic contract. No third-party figure or implementation was copied. Sources below provide context, not blanket validation of the present algorithm.

## S01 Trust-region actual and predicted reduction

M. J. D. Powell, On the convergence of a wide range of trust region methods for unconstrained optimization, DAMTP 2008/NA06, revised January 2009. [Author manuscript on Optimization Online](https://optimization-online.org/wp-content/uploads/2010/01/2511.pdf).

Read pages 1–4, equations 1.1–1.6 and 2.1–2.6: a local quadratic model, Cauchy decrease and actual/predicted ratio guide a bounded step. The paper's convergence assumptions include differentiability and a Lipschitz gradient. This package uses the proposal/validation separation, but does not inherit that convergence theorem across visibility switches or uncertain forward values. The new interval acceptance gate is derived here. The PDF was inspected through the web reader; a full local PDF download was not performed and is not claimed. Reader includes this short bibliographic note only.

## S02 Visibility boundary terms

Tzu-Mao Li, Miika Aittala, Frédo Durand, Jaakko Lehtinen, Differentiable Monte Carlo Ray Tracing through Edge Sampling, ACM TOG 37(6), 2018. [Author page](https://people.csail.mit.edu/tzumao/diffrt/), [paper](https://people.csail.mit.edu/tzumao/diffrt/diffrt.pdf), [errata](https://people.csail.mit.edu/tzumao/diffrt/errata.html).

Read abstract and the boundary-derivative structure, alongside the inherited T02 reading of section 3/equations 6–7. Visibility discontinuities require boundary contributions; differentiating only the smooth kernel misses them. This package uses one-dimensional event integration rather than the paper's edge-sampling algorithm. Its rendering unbiasedness and performance claims do not apply here. Author copy says personal use, not redistribution. Existing lawful local research copy was preserved under originals and excluded from every reader file list.

## S03 Event timing and transversality

Nathan J. Kong, J. Joe Payne, James Zhu, Aaron M. Johnson, Saltation Matrices: The Essential Tool for Linearizing Hybrid Dynamical Systems, Proceedings of the IEEE, 2024. [arXiv v3 author text](https://arxiv.org/html/2306.06862v3).

Read event timing and transversality assumptions in section III. Simultaneous events or tangent crossings require additional care beyond an ordinary smooth Jacobian. The present deposition integral has no collision reset, so its event contribution is independently derived with Leibniz's rule. No robot-control stability result is transferred. T02's local paper copy is retained only for research, conservatively excluded despite the open author version.

## S04 Robust encoded geometry

Jonathan Richard Shewchuk, Adaptive Precision Floating-Point Arithmetic and Fast Robust Geometric Predicates, Discrete & Computational Geometry 18, 1997. [Author technical page](https://www.cs.cmu.edu/~quake/robust.html).

Read the author's explanation of floating-point sign errors near geometric degeneracy and exact/adaptive predicates. This supports distinguishing encoded-geometry decisions from generic epsilon heuristics. We do not use his C implementation; rational slab predicates are inherited from frozen T02 and exact affine guards are new. Correct encoded predicates do not measure physical geometry. The author's page copy remains local only.

## S05 Coating angular response

Lichao Zhang, Xikun Cai, Uniformity Masks Design Method Based on the Shadow Matrix for Coating Materials with Different Condensation Characteristics, The Scientific World Journal, 2013:160792. [PMC open original](https://pmc.ncbi.nlm.nih.gov/articles/PMC3817662/).

Read equation 1 and surrounding definitions of emission and condensation characteristics. Coating angular response depends on process/material assumptions, motivating a bounded T04 handoff rather than treating cosine/cosine as universal. The paper's experiments are not data for the user's machine. Its CC BY original was already available locally; this round copies it as a private research reference but does not distribute the full text in the reader.

## Rights and access

Public access does not itself grant redistribution rights. All originals are kept separately and omitted from the allowlist, content manifest and archive. Reader contains only short paraphrases, citations and public source URLs. No publisher accounts, Library identifiers, private download links or account IDs are included. No blocked source access was bypassed.
