# T07R3 narrow independent optical/unit check

Date: 2026-10-02 UTC. Scope: the frozen encoded synthetic optical case only.

## Result

No optical/unit inconsistency was found within the requested narrow scope. All four independently computed characteristic-matrix scalar reflectances fall inside the corresponding exact rational production point enclosures. This is numerical corroboration and a focused contract inspection, **not formal DeepSeek/Seed/Sol review, a formal interval proof, or physical certification**.

Only this report was written. No code or case data were changed; no sweep, installation, device, optimizer, or Monte Carlo was used. Python 3.12.14 standard library only; bytecode writing was disabled.

## Inspected snapshot

SHA-256 of the four principal inputs:

- `data/case.json`: `2f5b2db5845a93f8c5fe0ae56bf4765cbe673fb7d1a4e46a3e8256a85180a631`
- `models/set_exclusion.py`: `bee59cba6587270011801c450fd808baaf0c9235722020cde4b5ace793deb46d`
- `dependencies/t06r3/models/bounded_optics.py`: `4ef1e3afa16bb9bfd726d120dfc7277f8eae471f284d280c681d941e22259b6a`
- `dependencies/t06r3/models/exact_intervals.py`: `81743a9d3705a9a386de67e5caadc72adc47d813fef5974e55d1bcdc3650d1ed`

The inherited `dependencies/t06r3/data/case.json` was also read solely to compare the M0 operator and material state.

## Contract checks

1. **Units.** `bounded_optics.incident_stack`, lines 48–54, divides the physical `thickness_nm` values by 1000. Wavelengths are in µm; `z=h/h_ref` and hypothesis multipliers are dimensionless. Thus `n*d/λ` is dimensionless. For H0 at z=1, the incident-order thicknesses are approximately `[1.98205, 0.66191, 1.28966, 0.52620, 0.22193, 0.64004]` µm. No quarter-wave conversion or 8000 nm reference-wavelength rescaling is applied to the explicit physical thickness table.
2. **Order.** The recipe explicitly says `substrate_to_incident_medium`. `incident_stack` reverses the layers and returns original IDs `[6,5,4,3,2,1]`, incident index 1, layer indices `[1.5,2.2,1.5,2.2,1.5,2.2]`, and substrate index 4. The reverse loop in `reflectance` then correctly starts at the bottom interface while building the incident-side reflection.
3. **Original outer layer 6.** `channel_box`, lines 53–55, first keys multipliers by the original recipe's layer IDs, then applies them using the reversed stack IDs. H_outer10's final multiplier `1.1` therefore affects original layer 6, the incident-most YF3 surrogate, rather than original layer 1. At z=1001/1000 its outer thickness is approximately 2.182435255 µm; the other five layers receive the common z multiplier only.
4. **Phase.** `bounded_optics.reflectance`, lines 56–64, uses `exp(i*4π*n*d/λ)`, the round-trip phase appropriate to its Airy recursion. `exact_intervals.phase` returns `(cos,sin)` intervals. The independent characteristic matrix below instead uses the one-way phase `δ=2π*n*d/λ`. This checks the factor of two using a different optical formulation.
5. **M0 unchanged.** Exact Python object equality succeeded between the derived M0 operator and the copied T06R3 measurement, and between the embedded inherited measurement and that copied measurement. M0 remains the weighted reflectance at 4.25, 4.26, and 4.27 µm with weights 1/4, 1/2, and 1/4. `validate_case`, line 29, guards that operator equality. `channel_box`, line 57, uses the supplied weights and nodes without changing M0 into a single-node or continuous-band measurement.
6. **M1 explicitly derived.** The second operator is a separate discrete 10 µm measurement with unit weight. The derived material extension explicitly postulates the same fixed synthetic real indices at that wavelength, lists all four supported wavelength nodes, sets k=0 and 300 K, retains the parent material hash and same sample-state ID, and says real-film nk is unknown. The extension's sample-state ID equals the copied T06R3 material state. This is an additional synthetic assumption, not measured dispersion or evidence of validity throughout 4.25–10 µm. The code checks the parent state, k=0, and membership in the declared node domain at lines 30–38.
7. **Same latent across channels.** One `z` is applied to every layer in `channel_box`. Within each branch node, `branch_exclude`, lines 79 and 83–84, passes that same `z` into every selected channel. `point_witness`, line 99, also uses one point for all channels. Each alternative hypothesis is evaluated separately, consistently with its own existential z. Interval arithmetic can lose within-box dependency, making the enclosure wider; it does not introduce independent physical latent variables for M0 and M1. No broad branch-and-bound correctness claim is made here.
8. **Encoding.** `exact_intervals.f` converts JSON floating-point thicknesses and indices to their exact binary rational values. The independent calculation preserved those same encoded inputs rather than silently replacing, for example, binary 2.2 with exact decimal 2.2. String wavelengths, z, and hypothesis multipliers were parsed as exact rational numbers. Production uses outward 80-bit dyadic intervals, so a requested rational point can acquire a small enclosing width.

## Independent scalar method

Exactly four scalar reflectances were recomputed. The independent calculation used `decimal.Decimal` at precision 90, with π generated by nine Gauss–Legendre iterations and sine/cosine by a separately implemented Taylor recurrence after reduction to [−π,π]. It did not call the inherited Airy recursion, inherited π/trigonometric routines, or `scalar_observation` to obtain the independent scalar.

For layers taken directly from the recipe in reversed order, use

`L_j = [[cos δ_j, i sin δ_j/n_j], [i n_j sin δ_j, cos δ_j]]`,

`δ_j = 2π n_j (d_nm,j/1000) z m_j / λ`, and `M = L_6 L_5 ... L_1`.

Writing `M=[[a,i b],[i c,d]]`, each layer updates

- `a' = a cosδ − b n sinδ`
- `b' = a sinδ/n + b cosδ`
- `c' = c cosδ + d n sinδ`
- `d' = d cosδ − c sinδ/n`

With incident and substrate indices `n0, ns`, evaluate

`R = ((n0*a − ns*d)^2 + (n0*ns*b − c)^2) / ((n0*a + ns*d)^2 + (n0*ns*b + c)^2)`.

For comparison, the production `channel_box` was evaluated once for each case, using a transient in-memory one-node copy of the appropriate operator. This isolates one scalar node while retaining the actual production unit/order/multiplier mapping. No on-disk operator was edited. The reported inclusion tests converted the 90-digit Decimal result to an exact Fraction and compared it against the exact rational interval endpoints, rather than checking rounded float bounds.

### Case 1: H0, z=1, λ=4.26 µm

- Multipliers in original order: `[1,1,1,1,1,1]`
- Independent R: `0.0115756017094748420839872671484191412436362597119723933448884857731367769758640299654587922`
- Production exact lower: `13994043784159376051637/1208925819614629174706176`
- Production exact upper: `1749255473019922006471/151115727451828646838272`
- Enclosure width: approximately `1.0836066024444663e-22`
- Independent scalar inside exact enclosure: **true**

### Case 2: H0, z=1, λ=10 µm

- Multipliers in original order: `[1,1,1,1,1,1]`
- Independent R: `0.0170708841309547913569162342736765105124476554723209463200599786139987621878212259507001061`
- Production exact lower: `5159358147390221954495/302231454903657293676544`
- Production exact upper: `10318716294780443909057/604462909807314587353088`
- Enclosure width: approximately `1.1084220208210571e-22`
- Independent scalar inside exact enclosure: **true**
- This is consistent with the declared rounded synthetic M1 center `0.017070884`.

### Case 3: H_outer10, z=1001/1000, λ=4.26 µm

- Multipliers in original order: `[1,1,1,1,1,11/10]`
- Independent R: `0.00767976078712616963492352022565140153424849177780139900362977461259767388484545648017718534`
- Production exact lower: `9284261104020794316717/1208925819614629174706176`
- Production exact upper: `9284261104020794316813/1208925819614629174706176`
- Enclosure width: approximately `7.940933880509066e-23`
- Independent scalar inside exact enclosure: **true**

### Case 4: H_outer10, z=1001/1000, λ=10 µm

- Multipliers in original order: `[1,1,1,1,1,11/10]`
- Independent R: `0.0346179340526216394393167388252087125248052758141713559414615331967781455493573913539963904`
- Production exact lower: `41850514297930796792985/1208925819614629174706176`
- Production exact upper: `20925257148965398396601/604462909807314587353088`
- Enclosure width: approximately `1.7949819292400701e-22`
- Independent scalar inside exact enclosure: **true**

Cases 3 and 4 deliberately use the same nonunit rational z and the same original layer-6 perturbation. The 90-digit scalar arithmetic itself has no directed-rounding error certificate; the inclusion results are independent numerical checks, not proofs that a scalar oracle is exact.

## Not reviewed / not established

- No independent numeric evaluation of the 4.25 or 4.27 µm nodes, full weighted M0 center, H_global002, or non-point z boxes. The M0 operator identity was checked structurally and against the copied case, not rederived by three scalar evaluations.
- No complete proof or broad test of interval arithmetic, trigonometric remainder/range-reduction correctness, complex denominator safety for arbitrary boxes, branch coverage, exclusion results, witnesses, budgets, sensitivity, or identifiability.
- No full dependency-manifest audit, source/retention bridge recomputation, measurement acquisition, material calibration, or real-film validity assessment.
- No backside, absorption, oblique incidence, polarization separation, spatial variation, continuous wavelength band, temperature dispersion, or different-batch model.
- No formal stage acceptance, no formal review-chain completion, and no advancement of point12 or point2 status. The inherited partial / conditional non-strict limitations and synthetic-only status remain.
