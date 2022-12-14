from typing import Dict
from functools import partial
from pathlib import Path
import json
from dictdiffer import diff
import sys

self_dir = Path(__file__).parent
sys.path.append(str(self_dir))
from lib.parsers import read_info_once

REGEX_ESCAPE = r'.'
METADATA_KEYS = ["match", "mapto"]
SUBREPO_DEFAULT_EXCLUDE = ["old_raw", "sample"]

read_metadata = partial(read_info_once, METADATA_KEYS, ':')

def regex_unescape(astr):
    astr = str(astr)
    for c in REGEX_ESCAPE:
        astr = astr.replace(r'\%s' % c, c)
    return astr

def collect_repo_info(repo_dir: Path) -> Dict[str, Dict[str, Dict[str, str]]]:
    all_repo_info = {}
    subdirs = filter(lambda p: p.is_dir(), repo_dir.iterdir())
    for subrepo_dir in filter(lambda p: not (p.name in SUBREPO_DEFAULT_EXCLUDE), subdirs):
        all_repo_info[subrepo_dir.name] = {}
        all_repo_info[subrepo_dir.name]["direct_match"] = {}
        all_repo_info[subrepo_dir.name]["regex"] = {}
        all_repo_info[subrepo_dir.name]["mapto"] = {}
        
        for impl_path in filter(lambda p: p.suffix == '.js', subrepo_dir.iterdir()):
            with open(impl_path, encoding='utf-8') as fp:
                flines = fp.readlines()
            
            impl_metadata, _ = read_metadata(flines)
            impl_name = impl_path.stem
            impl_match = impl_metadata["match"]
            impl_mapto = impl_metadata["mapto"]
            
            is_dmatch = impl_name in regex_unescape(impl_match)
            impl_dmatch = "direct_match" if is_dmatch else "regex"
            
            all_repo_info[subrepo_dir.name][impl_dmatch][impl_name] = impl_match
            if impl_mapto: all_repo_info[subrepo_dir.name]["mapto"][impl_name] = impl_mapto
    
    return all_repo_info


def main(repo_path_str: str):
    repo_path = Path(repo_path_str)
    all_repo_info = collect_repo_info(repo_path)
    with open(repo_path / 'repo.json', 'r') as orig_repo_info_fp:
        orig_repo_info = json.load(orig_repo_info_fp)
    info_diff = list(diff(orig_repo_info, all_repo_info))

    if info_diff:
        diff_json = json.dumps(info_diff, indent=4)
        print('Repo info diff as JSON:')
        print(diff_json)
        cont = input('Proceed? (Y/n) ')
        cont = cont.lower() in ('y', 'yes')
        if cont:
            with open(repo_path / 'repo.json', 'w') as orig_repo_info_fp:
                json.dump(all_repo_info, orig_repo_info_fp, indent=4)
        else:
            print('Aborted.')
    else:
        print('Repo info makes no difference. Aborted.')

if __name__ == '__main__':
    main(*sys.argv[1:])