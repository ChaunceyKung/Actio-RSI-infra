import argparse
import json
from pathlib import Path
from actio.evidence.campaigns.transport_campaign import verify_campaign

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args(argv)
    result=verify_campaign(a.directory);print(json.dumps(result));return 0 if result['valid'] else 2
