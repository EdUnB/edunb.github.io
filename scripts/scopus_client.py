"""Read-only official Scopus API connector. Credentials never enter artifacts.

Reference: https://dev.elsevier.com/sc_api_spec.html
Live entitlement/response compatibility must still be verified with a real key.
"""
from collections import Counter
from datetime import date
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, HTTPRedirectHandler, build_opener

AUTHOR_ID='57195100508'
ORCID='0000-0002-7582-5010'


class ScopusError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def integer(value):
    if type(value) is int and value>=0:return value
    if isinstance(value,str) and re.fullmatch(r'[0-9]+',value):return int(value)
    raise ScopusError('Scopus returned an invalid numeric field')


def many(value):
    return value if isinstance(value,list) else [value] if isinstance(value,dict) else []


def json_request(path,params,key,token=None):
    # Fixed host + no redirects prevents forwarding credentials to another host.
    url='https://api.elsevier.com'+path+'?'+urlencode(params)
    headers={'Accept':'application/json','X-ELS-APIKey':key}
    if token:headers['X-ELS-Insttoken']=token
    try:
        with build_opener(NoRedirect).open(Request(url,headers=headers),timeout=20) as response:
            raw=response.read(5_000_001)
        if len(raw)>5_000_000:raise ScopusError('Scopus response exceeds size limit')
        return json.loads(raw)
    except HTTPError as error:
        if error.code in (401,403):raise ScopusError('Scopus authentication or institutional entitlement required') from None
        if error.code==429:raise ScopusError('Scopus API quota reached; previous data retained') from None
        raise ScopusError('Scopus HTTP failure; previous data retained') from None
    except (URLError,TimeoutError,OSError,UnicodeError,json.JSONDecodeError):
        # Never include URLs, headers, response bodies or exception strings.
        raise ScopusError('Scopus connection or response failure; previous data retained') from None


def citation_batch(payload,ids,years):
    """Require exact document/year coverage, using official column headings."""
    try:
        response=payload['abstract-citations-response']
        headings=many(response['citeColumnTotalXML']['citeCountHeader']['columnHeading'])
        columns=[integer(item['$']) for item in headings]
        if columns!=years:raise ScopusError('Scopus citation-year coverage is incomplete')
        rows=many(response['citeInfoMatrix']['citeInfoMatrixXML']['citationMatrix']['citeInfo'])
        found=set();counts=Counter()
        for row in rows:
            identifier=row['dc:identifier'].removeprefix('SCOPUS_ID:')
            if identifier not in ids or identifier in found:raise ScopusError('Scopus citation document mismatch')
            values=[integer(item['$']) for item in many(row['cc'])]
            if len(values)!=len(years):raise ScopusError('Scopus citation values are missing')
            if integer(row.get('pcc','0'))>0:
                raise ScopusError('Scopus reports citations before the requested interval; range review required')
            found.add(identifier)
            counts.update(dict(zip(years,values)))
        if found!=set(ids):raise ScopusError('Scopus citation documents are incomplete')
        return counts
    except (KeyError,TypeError,AttributeError):
        raise ScopusError('Scopus citation response format requires review') from None


def fetch_metrics(key,token=None,*,request=None,today=None):
    """Collect totals and full annual series, or fail without a partial snapshot."""
    if not key:raise ScopusError('Scopus API key is not configured')
    request=request or (lambda path,params:json_request(path,params,key,token))
    today=today or date.today()
    try:
        response=request('/content/author/author_id/'+AUTHOR_ID,{'view':'METRICS'})
        authors=many(response['author-retrieval-response'])
        if len(authors)!=1:raise ScopusError('Scopus author identity is ambiguous')
        author=authors[0];core=author['coredata']
        if core['dc:identifier']!='AUTHOR_ID:'+AUTHOR_ID:raise ScopusError('Scopus returned another author')
        snapshot={'source':'Scopus','author_id':AUTHOR_ID,'orcid':ORCID,
                  'profile_url':'https://www.scopus.com/authid/detail.uri?authorId='+AUTHOR_ID,
                  'verified_on':today.isoformat(),'collection_method':'authorized_api',
                  'documents':integer(core['document-count']),'citations':integer(core['citation-count']),
                  'citing_documents':integer(core['cited-by-count']),'h_index':integer(author['h-index']),
                  'annual_series':None}
        expected=snapshot['documents']
        if expected>5000:raise ScopusError('Scopus document count exceeds this connector limit')
        if not expected:
            if snapshot['citations']:raise ScopusError('Scopus has citations without author documents')
            return snapshot
        documents={};offset=0
        while offset<expected:
            result=request('/content/search/scopus',{'query':'AU-ID('+AUTHOR_ID+')','view':'STANDARD','count':25,'start':offset})['search-results']
            if integer(result['opensearch:totalResults'])!=expected:
                raise ScopusError('Scopus profile/search counts differ; incomplete collection rejected')
            entries=many(result['entry'])
            if not entries:raise ScopusError('Scopus document pagination is incomplete')
            for item in entries:
                identifier=item['dc:identifier'].removeprefix('SCOPUS_ID:')
                if not identifier.isdigit() or identifier in documents:raise ScopusError('Scopus duplicate or invalid document')
                year=integer(item['prism:coverDate'][:4])
                if not 1900<=year<=today.year:raise ScopusError('Scopus future publication year requires review')
                documents[identifier]=year
            offset+=len(entries)
        if len(documents)!=expected:raise ScopusError('Scopus document collection is incomplete')
        first_year=min(documents.values());years=list(range(first_year,today.year+1))
        citations=Counter();ids=list(documents)
        # Citation Overview supplies full yearly columns for all requested IDs.
        for index in range(0,len(ids),25):
            batch=ids[index:index+25]
            payload=request('/content/abstract/citations',{'scopus_id':','.join(batch),'date':f'{first_year}-{today.year}','count':25})
            citations.update(citation_batch(payload,batch,years))
        if sum(citations.values())!=snapshot['citations']:
            raise ScopusError('Scopus annual citation total differs from profile; review required')
        output=Counter(documents.values())
        snapshot['annual_series']={'documents':[{'year':year,'value':output[year]} for year in years],
                                   'citations':[{'year':year,'value':citations[year]} for year in years]}
        return snapshot
    except (KeyError,TypeError,AttributeError,IndexError):
        raise ScopusError('Scopus response format requires review') from None
