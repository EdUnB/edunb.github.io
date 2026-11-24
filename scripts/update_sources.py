"""One local collection/review entry point. Never publishes or writes catalogs.

Configure credentials/private Lattes location once, then run when the owner
requests an update. Missing access is explicit; existing values stay untouched.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sys

import build
from import_lattes import extract,parse,merge_publications
from import_supervisions import extract_records,prepare_review
from compare_lattes import editorial_records
from scopus_client import fetch_metrics,ScopusError


def discover_lattes(directory=None):
    """Find the newest dated export in the existing private sibling folder."""
    directory=Path(directory) if directory else build.ROOT.parent/'_edgar-website-privado'
    if not directory.is_dir():return None
    if directory.resolve().is_relative_to(build.ROOT.resolve()):
        raise ValueError('Lattes discovery directory must stay private')
    candidates=[path for path in directory.iterdir() if path.suffix.lower() in ('.xml','.zip')]
    if len(candidates)>20:raise ValueError('Private Lattes source selection requires review')
    ranked=[]
    for path in candidates:
        root=extract(path)
        stamp=root.get('DATA-ATUALIZACAO','')
        try:updated=datetime.strptime(stamp,'%d%m%Y')
        except ValueError:raise ValueError('Lattes source date requires review') from None
        ranked.append((updated,path.stat().st_mtime,path))
    return max(ranked,key=lambda row:(row[0],row[1]))[2] if ranked else None


def collect(*,lattes=None,offline=False,environ=None,fetcher=None):
    environ=os.environ if environ is None else environ
    fetcher=fetcher or fetch_metrics
    build.validate()
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'mode':'review_only',
            'sources':{},'proposals':{}}
    current=build.load('scopus.json')
    key=environ.get('SCOPUS_API_KEY') or environ.get('ELSEVIER_API_KEY')
    if offline:
        scopus={'status':'not_checked_offline','retained_verified_on':current['verified_on']}
    elif not key:
        scopus={'status':'initial_setup_required','reason':'Scopus API credentials are not configured',
                'retained_verified_on':current['verified_on']}
    else:
        try:
            candidate=fetcher(key,environ.get('SCOPUS_INST_TOKEN'))
            build.validate_scopus(candidate)
            changed=[field for field in ('documents','citations','citing_documents','h_index','annual_series') if current[field]!=candidate[field]]
            scopus={'status':'changes_ready_for_review' if changed else 'checked_unchanged',
                    'changed_fields':changed,'verified_on':candidate['verified_on']}
            report['proposals']['scopus']=candidate
        except (ScopusError,ValueError):
            scopus={'status':'access_or_data_review_required',
                    'reason':'No complete verified snapshot obtained; existing data retained',
                    'retained_verified_on':current['verified_on']}
    report['sources']['scopus']=scopus
    discovery_failed=False
    try:location=lattes or environ.get('LATTES_XML_PATH') or discover_lattes()
    except Exception:location=None;discovery_failed=True
    if not location:
        report['sources']['lattes']={'status':'source_review_required' if discovery_failed else 'initial_setup_required',
                                     'reason':'Private Lattes source needs review or initial location configuration'}
    else:
        source=Path(location).expanduser().resolve()
        if source.is_relative_to(build.ROOT.resolve()):
            report['sources']['lattes']={'status':'private_location_required'}
        else:
            try:
                # Safe XML/ZIP loader and conservative publication merge remain unchanged.
                root=extract(source);incoming=parse(root)
                existing=build.load('publications.json')['items']
                merged,new,ambiguous=merge_publications(existing,incoming)
                report['sources']['lattes']={'status':'changes_ready_for_review',
                    'source_path':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                    'export_updated_at':root.get('DATA-ATUALIZACAO'),
                    'articles_identified':len(incoming),'new_articles':len(new),'ambiguous_matches':len(ambiguous)}
                report['proposals']['publications']={'items':merged,'review_required':ambiguous}
                try:
                    records,issues=extract_records(root)
                    previous=[]
                    reviews=sorted(source.parent.glob('orientacoes-revisao*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
                    review_path=environ.get('LATTES_SUPERVISIONS_REVIEW') or (reviews[0] if reviews else None)
                    if review_path:
                        review_path=Path(review_path).resolve()
                        if review_path.is_relative_to(build.ROOT.resolve()):raise ValueError('Private review location required')
                        previous=json.loads(review_path.read_text('utf-8'))['items']
                    proposed,counts=prepare_review(records,previous)
                    report['proposals']['supervisions']={'items':proposed,'source_issues':dict(issues)}
                    report['sources']['supervisions']={'status':'changes_ready_for_review','counts':dict(counts),
                                                      'baseline':'private_review' if review_path else 'no_previous_review'}
                except Exception:
                    report['sources']['supervisions']={'status':'source_review_required'}
                report['proposals']['editorial']={'incoming':editorial_records(root),
                                                  'preserved_approved':build.load('editorial.json')['items']}
                report['sources']['editorial']={'status':'editorial_review_required','source':'same_private_lattes'}
            except Exception:
                # Do not leak XML snippets, personal records, tokens or HTTP details.
                report['sources']['lattes']={'status':'source_review_required','reason':'Private source could not be safely processed'}
    for name in ('profile','projects','collaborations','translations'):
        report['sources'][name]={'status':'preserve_editorial_content','reason':'Changes require evidence and editorial review'}
    report['sources']['cv']={'status':'derived_on_next_build','source':'same_reviewed_catalogs'}
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-dir',required=True,type=Path)
    parser.add_argument('--lattes',type=Path,help='Optional private XML/ZIP path; otherwise LATTES_XML_PATH')
    parser.add_argument('--offline',action='store_true',help='Validate sources/configuration without network requests')
    args=parser.parse_args(argv)
    output=args.review_dir.resolve()
    if output.is_relative_to(build.ROOT.resolve()):
        print('ERROR: use a review directory outside the repository and dist/',file=sys.stderr);return 1
    report=collect(lattes=args.lattes,offline=args.offline)
    output.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path=output/f'update-review-{stamp}.json'
    with path.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2)
    for name,result in report['sources'].items():print(name+': '+result['status'])
    print('Private review report:',path)
    print('No official catalogs, deployment configuration or published site changed.')
    return 0


if __name__=='__main__':sys.exit(main())
