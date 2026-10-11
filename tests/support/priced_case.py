"""Current test support; historical stage script is not imported."""
from actio.interfaces.store import Store
from actio.adapters.transport.transport import transport_spec
from actio.application.transport import scheduling_transport
from actio.tasks.scheduling import task_card
from actio.interfaces.export import export_bundle

def run(root,cfg,ledger_path,secret,variant='compatible',runtime_type=None):
    root.mkdir(parents=True,exist_ok=True);s=Store(root/'ledger.sqlite',create=True)
    try:
        for a in ('ACTOR_A','ACTOR_B'):s.agent(a,transport_spec(a,cfg))
        bindings={seat:{'agent':a,'spec_hash':s.agent(a)['spec_hash']} for seat,a in [('A','ACTOR_A'),('B','ACTOR_B')]}
        task=task_card(variant,bindings,'priced_rehearsal');error=None
        try:scheduling_transport(s,'episode',root,task=task,config=cfg,ledger_path=ledger_path,credential=secret,**({'runtime_type':runtime_type} if runtime_type else {}))
        except Exception as e:error={'type':type(e).__name__,'reason':str(e)}
        result=s.run('episode');exported=export_bundle(s.path,'episode',root/'bundle')
        return {'run':result,'error':error,'export':exported}
    finally:s.close()
