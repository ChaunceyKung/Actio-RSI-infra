"""Single public CLI; import only the selected handler, pass explicit argv."""
import sys

HELP = """Actio 0.2 — modular single-host infrastructure
Usage: actio COMMAND [arguments]
  run                    original fixture/database commands
  verify                 verify a sealed bundle
  evaluate               offline evaluation commands
  candidate              candidate proposal and lineage
  candidate-evaluation   evaluation campaign commands
  preflight readiness gateway pilot suite robustness
  diagnostics task       task diagnostics
  diagnostics transport  transport diagnostics / run-local
  campaign verify        verify a campaign directory
Use actio COMMAND --help for argparse-based commands.
Diagnostics: plan | verify PATH | analyze PATH | export NEW_DIRECTORY
"""

def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if not args or args in (['--help'],['-h']):
        print(HELP);return 0
    if args==['--version']:
        from actio import __version__
        print(__version__);return 0
    command=args.pop(0)
    if command=='run':
        from actio.interfaces.cli.run import main as handler
    elif command=='verify':
        from actio.interfaces.cli.verify import main as handler
    elif command=='evaluate':
        from actio.interfaces.cli.evaluation import main as handler
    elif command=='candidate':
        from actio.interfaces.cli.candidate import main as handler
    elif command=='candidate-evaluation':
        from actio.interfaces.cli.candidate_evaluation import main as handler
    elif command=='preflight':
        from actio.interfaces.cli.preflight import main as handler
    elif command=='readiness':
        from actio.interfaces.cli.readiness import main as handler
    elif command=='gateway':
        from actio.interfaces.cli.gateway import main as handler
    elif command=='pilot':
        from actio.interfaces.cli.pilot import main as handler
    elif command=='suite':
        from actio.interfaces.cli.suite import main as handler
    elif command=='robustness':
        from actio.interfaces.cli.robustness import main as handler
    elif command=='diagnostics' and args:
        family=args.pop(0)
        if family=='task':
            from actio.interfaces.cli.task_diagnostics import main as handler
        elif family=='transport':
            from actio.interfaces.cli.transport_diagnostics import main as handler
        else:
            print('unknown diagnostic family',file=sys.stderr);return 2
        if args in (['--help'],['-h']):
            print(HELP);return 0
    elif command=='campaign' and args and args.pop(0)=='verify':
        from actio.interfaces.cli.campaign_verify import main as handler
    else:
        print('unknown command; use actio --help',file=sys.stderr);return 2
    return handler(args)
