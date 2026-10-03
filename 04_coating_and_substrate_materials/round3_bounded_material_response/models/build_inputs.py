from bounded_response import *
from dataclasses import asdict,replace
if __name__=='__main__':
 inp={'dataset_kind':'synthetic','candidates':[asdict(Scene(half_width_m=.08)),asdict(Scene(half_width_m=.09))],'source_nodes_m':[0.],'source_weights':[1.],'target_m':1e-9,'responses':{'angular_exact':asdict(Response(angular_a=(1.,1.))),'angular_uncertain':asdict(Response(angular_a=(0.,1.)))}}
 (R/'data/driver_inputs.json').write_text(json.dumps(inp,indent=2)+'\n')
 p={'schema_version':'T04-r3-response-validation-1','execution_mode':'plan_only','execution_authorized':False,'authorization_evidence':'','host_access_confirmed':False,'device_label':'','input_sha256':digest(inp),'panel_levels':[128,256,512,1024],'max_forward_calls':16,'max_total_panels':40000,'max_wall_seconds':600,'relative_thickness_tolerance':.001,'stop_when_resolved':True,'purpose':'bounded material re-evaluation only; no hostquota bypass, no source-clock changes, no historical oracle completion'}
 (R/'data/device_validation_plan.json').write_text(json.dumps(p,indent=2)+'\n')
 props={}
 for k,v in asdict(Response()).items():
  if isinstance(v,tuple):props[k]={'anyOf':[{'type':'array','minItems':2,'maxItems':2,'items':{'type':'number'}},{'type':'null'}]}
  else:props[k]={'type':'string'}
 schema={'$schema':'https://json-schema.org/draft/2020-12/schema','title':'T04 bounded response input','type':'object','additionalProperties':False,'required':list(props),'properties':props,'$comment':'Syntax only; Response.validate enforces ordered intervals, positivity, histories, density basis and allowed synthetic/unmeasured states. Physically measured response is not supported.'}
 (R/'data/response.schema.json').write_text(json.dumps(schema,indent=2)+'\n')
