"""Generate private editorial CV previews without changing any source catalogs."""
import argparse
from pathlib import Path
import sys

from build import CV, ROOT, load, validate


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path,
                        help='Review directory outside the site repository and dist/')
    args=parser.parse_args(argv)
    try:
        output=args.output.resolve()
        if output.is_relative_to(ROOT.resolve()):
            raise ValueError('CV preview must stay outside the repository and publication artifact')
        profile,publications,_,_,translations,supervisions,editorial=validate()
        snapshot=CV.prepare(load('cv.json'),profile,publications,supervisions,editorial,translations)
        paths=CV.write_documents(snapshot,output,preview=True)
        for path in paths: print(path)
        print('EDITORIAL PREVIEW ONLY: official catalogs and publication status unchanged.')
        return 0
    except (ValueError,OSError) as error:
        print(f'ERROR: {error}',file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
