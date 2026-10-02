"""Attach accurate human-readable titles to already-verified catalogue records."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
T={
'ISO 10110-9:2016':'Optics and photonics — Preparation of drawings for optical elements and systems — Part 9: Surface treatment and coating',
'ISO 10110-7:2017':'Optics and photonics — Preparation of drawings for optical elements and systems — Part 7: Surface imperfections',
'ISO 10110-8:2019':'Optics and photonics — Preparation of drawings for optical elements and systems — Part 8: Surface texture',
'ISO 14997:2017':'Optics and photonics — Test methods for surface imperfections of optical elements',
'ISO 9211-1:2024':'Optics and photonics — Optical coatings — Part 1: Vocabulary',
'ISO 9211-2:2024':'Optics and photonics — Optical coatings — Part 2: Optical properties',
'ISO 9211-3:2024':'Optics and photonics — Optical coatings — Part 3: Environmental durability',
'ISO 9211-4:2022':'Optics and photonics — Optical coatings — Part 4: Specific test methods: abrasion, adhesion and resistance to water',
'ISO 9211-5:2018':'Optics and photonics — Optical coatings — Part 5: Minimum requirements for antireflecting coatings',
'ISO 9211-6:2018':'Optics and photonics — Optical coatings — Part 6: Minimum requirements for reflecting coatings',
'ISO 9211-7:2021':'Optics and photonics — Optical coatings — Part 7: Minimum requirements for neutral beam splitter coatings',
'ISO 9211-8:2018':'Optics and photonics — Optical coatings — Part 8: Minimum requirements for coatings used for laser optics',
'ISO 9022-1:2016':'Optics and photonics — Environmental test methods — Part 1: Definitions, extent of testing',
'ISO 9022-2:2015':'Optics and photonics — Environmental test methods — Part 2: Cold, heat and humidity',
'ISO 9022-2:2015/Amd 1:2023':'Optics and photonics — Environmental test methods — Part 2: Cold, heat and humidity — Amendment 1',
'ISO 9022-4:2014':'Optics and photonics — Environmental test methods — Part 4: Salt mist',
'ISO 9022-4:2014/Amd 1:2023':'Optics and photonics — Environmental test methods — Part 4: Salt mist — Amendment 1',
'ISO 21254-1:2025':'Lasers and laser-related equipment — Test methods for laser-induced damage threshold — Part 1: Definitions and general principles',
'ISO 21254-2:2011':'Lasers and laser-related equipment — Test methods for laser-induced damage threshold — Part 2: Threshold determination',
'ISO 21254-3:2011':'Lasers and laser-related equipment — Test methods for laser-induced damage threshold — Part 3: Assurance of laser power (energy) handling capabilities',
'ISO/TR 21254-4:2011':'Lasers and laser-related equipment — Test methods for laser-induced damage threshold — Part 4: Inspection, detection and measurement',
'ISO 15368:2021':'Optics and photonics — Measurement of reflectance of plane surfaces and transmittance of plane parallel elements',
'ISO 13697:2006':'Optics and photonics — Lasers and laser-related equipment — Test methods for specular reflectance and regular transmittance of optical laser components',
'ISO 13696:2022':'Optics and photonics — Test method for total scattering by optical components',
'ISO 11551:2026':'Optics and photonics — Lasers and laser-related equipment — Test method for absorptance of optical laser components',
'ISO 11554:2025':'Optics and photonics — Lasers and laser-related equipment — Test methods for laser beam radiant power, radiant energy and temporal characteristics',
'ISO/IEC 17025:2017':'General requirements for the competence of testing and calibration laboratories',
'ISO 2859-1:2026':'Sampling procedures for inspection by attributes — Part 1: Sampling schemes indexed by acceptance quality limit (AQL) for lot-by-lot inspection',
'ASTM D3359-23':'Standard Test Methods for Rating Adhesion by Tape Test',
'ASTM D4060-25':'Standard Test Method for Abrasion Resistance of Organic Coatings by the Taber Abraser',
'ASTM B117-26a':'Standard Practice for Operating Salt Spray (Fog) Apparatus',
'ASTM D2247-25':'Standard Practice for Testing Water Resistance of Coatings in 100% Relative Humidity',
'ASTM D1003-21':'Standard Test Method for Haze and Luminous Transmittance of Transparent Plastics',
'JCGM 106:2012':'Evaluation of measurement data — The role of measurement uncertainty in conformity assessment',
'ILAC G8:09/2019':'Guidelines on Decision Rules and Statements of Conformity',
'NIST optical scattering from surfaces':'Optical scattering from surfaces',
'Ma et al. Optics Letters 42 478-481 (2017)':'Effect of boundary continuity on nanosecond laser damage of nodular defects in high-reflection coatings',
'Cheng et al. Applied Optics 65 A52-A57 (2026)':'Adhesion and environmental durability of anti-reflective coatings on cycloolefin copolymer',
'Gibson et al. durable infrared coatings Applied Optics 59 2731 (2020)':'Durable infrared optical coatings based on pulsed DC-sputtering of hydrogenated amorphous carbon (a-C:H)'}
extras=json.loads((P/'data/official_status_mil_gb.json').read_text())['standards']
T.update({s['id']:s['title'] for s in extras})
for filename,key in [('source_registry.json','sources'),('standards_map.json','standards'),('standards_map_base.json','standards')]:
 path=P/'data'/filename;r=json.loads(path.read_text())
 for s in r[key]:
  s['title']=T[s['identity']]
  if s['identity'].startswith('Ma et al.'):
   s['doi']='10.1364/OL.42.000478';s['authors']='Hongping Ma; Xinbin Cheng; Jinlong Zhang; Hongfei Jiao; Bin Ma; Yongjian Tang; Zhouling Wu; Zhanshan Wang'
  if s['identity'].startswith('Cheng et al.'):
   s['doi']='10.1364/AO.577683';s['authors']='Yan Cheng; Yusi Wang; Kaixin Yuan; Tingting Zheng; Yujie Liu; Han Wu; Chenying Yang; Yueguang Zhang; Weidong Shen'
  if s['identity'].startswith('Gibson et al.'):
   s['doi']='10.1364/AO.378266';s['publication_date']='2020-03-12';s['pages']='2731-2738';s['authors']='Des Gibson; Shigeng Song; Lewis Fleming; Sam Ahmadzadeh; Hin On Chu; Stephen Sproules; Ryan Swindell; Xiaoling Zhang; Parnia Navabpour; Caspar Clark; Mark Bailey'
 path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
