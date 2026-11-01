#!/usr/bin/env python3
"""Verify public reference identity; no optimizer, private export or network."""
import argparse,hashlib,json
from pathlib import Path

def canonical(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()

def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",required=True);a=p.parse_args();root=Path(a.repo);case=json.loads((Path(__file__).parent/"public-reference-case.json").read_text())
    for f in case["public_sources"]:
        data=(root/f["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest()!=f["sha256"]:raise ValueError("public source file hash mismatch: "+f["path"])
    catalog=json.loads((root/"data/optical_catalog.json").read_text());supplement=json.loads((root/"coat_sim/core/resources/optical_substrate_supplement.json").read_text());materials={x["builtin_material_id"]:x for x in catalog["materials"]};keys=("kind","wavelength_unit","wavelength_min","wavelength_max","wavelengths","n","k","parameters")
    for ref in case["material_references"]:
        mid,oid=ref["material_id"],ref["optical_set_id"]
        if mid in materials:matches=[x for x in materials[mid]["optical_constants"] if x["id"]==oid]
        else:matches=[x for m in supplement["materials"] for x in m["optical_sets"] if x["id"]==oid]+[m["record"] for m in supplement["optical_set_additions"] if m["record"]["id"]==oid]
        if len(matches)!=1:raise ValueError("ambiguous public optical record: "+oid)
        record=matches[0];projection={k:record[k] for k in keys if k in record}
        if hashlib.sha256(canonical(projection)).hexdigest()!=ref["canonical_optical_fields_sha256"] or hashlib.sha256(canonical(record)).hexdigest()!=ref["canonical_public_record_sha256"]:raise ValueError("public optical record mismatch: "+oid)
    goals=case["measurement"]["objectives"]
    expected=[(400.,500.,101,.8,1.),(510.,550.,41,0.,.006500000000000001),
              (560.,700.,141,.8,1.),(1040.,1080.,41,0.,.006500000000000001)]
    if len(goals)!=4:raise ValueError("case goal count changed")
    for goal,values in zip(goals,expected):
        actual=(goal["wavelength_min_nm"],goal["wavelength_max_nm"],goal["samples"],
                goal["pointwise_lower_inclusive"],goal["pointwise_upper_inclusive"])
        if (actual!=values or goal["metric"]!="T" or not goal["pointwise_enabled"] or
                goal["mean_enabled"] or goal["weight"]!=1.0 or goal["normalization_scale"]!=1.0):
            raise ValueError("case goal semantics changed")
    env=case["environment"];settings=case["reference_search_settings"]
    expected_films=[{"material_id":"builtin_research_SiO2_film","optical_set_id":"ri_sio2_rodriguez_de_marcos"},
                    {"material_id":"builtin_research_TiO2_film","optical_set_id":"rii_tio2_franta"}]
    expected_air={"material_id":"builtin_ideal_air","optical_set_id":"ideal_air_n1_k0"}
    if (case["measurement"]["angle_deg"]!=0.0 or case["measurement"]["polarization"]!="unpolarized"
            or case["measurement"]["sample_spacing_nm"]!=1.0 or env["reference_wavelength_nm"]!=550.0
            or env["substrate"]["thickness_mm"]!=3.0 or env["substrate"]["sides"]!="double"
            or env["substrate"]["mode"]!="auto" or env["substrate"]["optical_set_id"]!="cdgm_hk9l_sellmeier_nm"
            or env["candidate_films_ordered"]!=expected_films or env["incident_and_exit_medium"]!=expected_air
            or env["layer_order"]!="substrate_outward" or env["first_surface"]!="front"
            or env["engine_flags"]["assume_lossless"] is not True or env["engine_flags"]["use_k"] is not True
            or env["initial_front_layers"] or env["initial_back_layers"] or settings["selected_surfaces"]!=["front"]
            or settings["back_surface_optimized"] is not False or settings["cpu_workers"]!=1
            or settings["search_until_target"] is not True or settings["validation_samples_multiplier"]!=2
            or any(settings[k] is not None for k in ("max_layers","max_layer_thickness_nm","max_total_thickness_nm","minimum_nonzero_thickness_nm"))):
        raise ValueError("case geometry, absorption or resource boundary changed")
    print("PASS: two public source files and four optical records; no optical synthesis executed")
if __name__=="__main__":main()
