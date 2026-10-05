# Retained failed or superseded attempts

These files are evidence, not validation passes.

- geometry_vanish_incomplete_tally: real collisionnone run used vanish and surf/collision/tally. Surface tallies did not match nscoll; full conservation audit rejected it. The pinned upstream vanish implementation does not set the reaction output flag; collision tally also has null-pointer hazards. Final geometry uses specular + surf_react global 1 0 and reaction tally.
- static_mesh40_insufficient_initial_majorant.json: the first low-initial-majorant fine-grid result P0=0.9236 versus 0.904837 failed the 4-sigma threshold. All final bath decks initialize the collision majorant using a 4800K collision mixture while actual created distributions remain separately specified.
- thermal_equal_mass_feedback: initial equal-mass thermal bath heated and acquired drift from the tracer pulse. It was not a maintained thermal reference. Final thermal tests use a deliberately synthetic heavy/hot bath that preserves the velocity scale and makes feedback negligible.
- First emit/surf + collision tally run on the emitting surface terminated with signal 11. The parent tool return recorded it; the echo/debug log is preserved as emitter_tally_null_debug.log when available. Input was adjusted without editing upstream solver source.

No failed attempt is included in results/validation_summary.json.
