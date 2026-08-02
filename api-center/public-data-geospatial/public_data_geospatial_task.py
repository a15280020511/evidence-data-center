#!/usr/bin/env python3
"""Bounded, fixed-host public-data and geospatial provider."""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
import requests

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from managed_provider_runtime import bounded_int, bytes_sha, finish_execution, load_json, provider_row, run_cli, utc_now, validate_ticket
SCHEMA_PATH=HERE/'ticket.schema.json'; CATALOG_PATH=HERE/'provider-catalog.json'

class Spec:
    def __init__(self, method:str, url:str, params=None, json_body=None, data_body=None, headers=None, auth=None, credential_mode='none', response_kind='json'):
        self.method=method; self.url=url; self.params=params; self.json_body=json_body
        self.data_body=data_body; self.headers=headers; self.auth=auth
        self.credential_mode=credential_mode; self.response_kind=response_kind

def text(p:Mapping[str,Any],name:str,maximum:int=300,required:bool=False)->str:
    value=str(p.get(name) or '').strip()
    if required and not value: raise ValueError(f'{name} is required')
    if len(value)>maximum or any(ord(ch)<32 for ch in value): raise ValueError(f'{name} is invalid')
    return value

def secret(name:str,required:bool=True)->str:
    value=str(os.environ.get(name) or '').strip()
    if required and not value: raise RuntimeError(f'missing required backend secret or variable: {name}')
    return value

def integer(p:Mapping[str,Any],name:str,default:int,lo:int,hi:int)->int:
    return bounded_int(p.get(name),default=default,minimum=lo,maximum=hi,name=name)

def coords(value:Any,name:str,minimum:int,maximum:int)->list[list[float]]:
    if not isinstance(value,list) or not minimum<=len(value)<=maximum: raise ValueError(f'{name} size is invalid')
    out=[]
    for pair in value:
        if not isinstance(pair,list) or len(pair)!=2: raise ValueError(f'{name} coordinate is invalid')
        lon,lat=float(pair[0]),float(pair[1])
        if not -180<=lon<=180 or not -90<=lat<=90: raise ValueError(f'{name} coordinate is outside WGS84 bounds')
        out.append([lon,lat])
    return out

def build(operation:str,p:Mapping[str,Any])->Spec|dict[str,Any]:
    if operation=='catalog-capabilities':
        if p: raise ValueError('catalog-capabilities accepts no parameters')
        return {'provider':provider_row(CATALOG_PATH)}
    if operation=='china-local-open-data-catalog':
        if p: raise ValueError('china-local-open-data-catalog accepts no parameters')
        return {'portals':[
          {'name':'浙江·数据开放','url':'https://data.zjzwfw.gov.cn/dopServer/','coverage':'浙江省','access':'official portal; API/catalog access subject to portal registration'},
          {'name':'深圳市政府数据开放平台','url':'https://opendata.sz.gov.cn/','coverage':'深圳市','access':'official portal; machine-readable datasets and application interfaces vary by dataset'},
          {'name':'上海市公共数据开放平台','url':'https://data.sh.gov.cn/','coverage':'上海市','access':'official portal'},
          {'name':'北京市公共数据开放平台','url':'https://data.beijing.gov.cn/','coverage':'北京市','access':'official portal'},
          {'name':'广东省公共数据开放平台','url':'https://data.gd.gov.cn/','coverage':'广东省','access':'official portal'},
          {'name':'福建省公共数据资源统一开放平台','url':'https://data.fujian.gov.cn/','coverage':'福建省','access':'official portal; availability must be checked per dataset'},
        ],'note':'目录入口只做发现；未把登录、人工审批或人机验证包装为自动 API。'}
    if operation=='china-science-data-centers':
        if p: raise ValueError('china-science-data-centers accepts no parameters')
        return {'centers':[
          {'name':'国家地球系统科学数据中心','url':'https://www.geodata.cn','themes':['land','ecology','resources','environment']},
          {'name':'国家青藏高原科学数据中心','url':'https://data.tpdc.ac.cn','themes':['Tibetan Plateau','cryosphere','atmosphere','hydrology']},
          {'name':'国家林业和草原科学数据中心','url':'https://forestdata.cn','api':'key application; OGC WMTS map services'},
          {'name':'国家气象科学数据中心','url':'https://data.cma.cn','access':'registration and dataset-specific rules'},
          {'name':'国家地震科学数据中心','url':'https://data.earthquake.cn','access':'catalog and dataset-specific services'},
          {'name':'国家海洋科学数据中心','url':'https://mds.nmdis.org.cn','access':'catalog and dataset-specific services'},
          {'name':'国家生态科学数据中心','url':'https://www.cnern.org.cn','access':'catalog and station-network data'},
          {'name':'国家人口健康科学数据中心','url':'https://www.ncmi.cn','access':'registration/data-specific governance; no personal-data automation'},
          {'name':'国家基础地理信息中心公共地理数据','url':'https://www.webmap.cn','access':'public catalog and downloadable basic geographic resources'},
        ],'note':'仅收录公开科学数据目录；涉及个人健康、受控数据或逐项审批的数据不自动调用。'}
    if operation=='ilostat-dataflows':
        return Spec('GET','https://sdmx.ilo.org/rest/dataflow/all/all/latest',headers={'Accept':'application/vnd.sdmx.structure+json;version=2.0.0'})
    if operation=='unicef-dataflows':
        return Spec('GET','https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/dataflow/all/all/latest/',params=[('format','sdmx-json'),('detail','full'),('references','none')])
    if operation=='un-sdg-indicators':
        return Spec('GET','https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List',params=[('includechildren','true' if p.get('include_children') else 'false')])
    if operation=='faostat-definitions':
        lang=text(p,'language',2) or 'en'; return Spec('GET',f'https://fenixservices.fao.org/faostat/api/v1/{lang}/Definitions')
    if operation=='worldpop-catalog':
        q=[]
        if p.get('alias'): q.append(('alias',text(p,'alias',80)))
        if p.get('iso3'): q.append(('iso3',text(p,'iso3',3)))
        return Spec('GET','https://www.worldpop.org/rest/data',params=q)
    if operation=='worldpop-services': return Spec('GET','https://api.worldpop.org/v1/services')
    if operation=='gbif-occurrences':
        q=[('limit',str(integer(p,'limit',20,1,100))),('offset',str(integer(p,'offset',0,0,100000)))]
        mapping={'scientific_name':'scientificName','country':'country','year':'year'}
        for s,t in mapping.items():
            if p.get(s): q.append((t,text(p,s,200)))
        if p.get('decimal_latitude') is not None and p.get('decimal_longitude') is not None:
            lat=float(p['decimal_latitude']); lon=float(p['decimal_longitude']); radius=float(p.get('radius_km') or 10)
            q.append(('geometry',f'POINT({lon} {lat})')); q.append(('geometry_srs','EPSG:4326'))
            q.append(('distanceFromCentroidInMeters',str(int(radius*1000))))
        return Spec('GET','https://api.gbif.org/v1/occurrence/search',params=q)
    if operation=='unhcr-population':
        q=[('limit',str(integer(p,'limit',20,1,100))),('page',str(integer(p,'page',1,1,1000)))]
        for s,t in {'year_from':'yearFrom','year_to':'yearTo','coa':'coa','coo':'coo'}.items():
            if p.get(s) not in (None,''): q.append((t,str(p[s])))
        return Spec('GET','https://api.unhcr.org/population/v1/population/',params=q)
    if operation=='reliefweb-reports':
        q=[('appname',secret('RELIEFWEB_APPNAME')),('limit',str(integer(p,'limit',20,1,50))),('offset',str(integer(p,'offset',0,0,10000))),('profile','list')]
        if p.get('query'): q.append(('query[value]',text(p,'query',300)))
        if p.get('country'): q.extend([('filter[field]','country.name'),('filter[value]',text(p,'country',100))])
        return Spec('GET','https://api.reliefweb.int/v2/reports',params=q,credential_mode='appname')
    if operation=='gleif-lei-search':
        q=[('filter[entity.legalName]',text(p,'query',200,True)),('page[size]',str(integer(p,'page_size',20,1,100))),('page[number]',str(integer(p,'page_number',1,1,1000)))]
        if p.get('country'): q.append(('filter[entity.legalAddress.country]',text(p,'country',2)))
        return Spec('GET','https://api.gleif.org/api/v1/lei-records',params=q)
    if operation=='usaspending-awards':
        start=text(p,'start_date',10,True); end=text(p,'end_date',10,True)
        body={'filters':{'keywords':p['keywords'],'time_period':[{'start_date':start,'end_date':end}]},'fields':['Award ID','Recipient Name','Award Amount','Awarding Agency','Start Date','End Date','Description'],'page':integer(p,'page',1,1,1000),'limit':integer(p,'limit',20,1,100),'subawards':False}
        if p.get('award_type_codes'): body['filters']['award_type_codes']=p['award_type_codes']
        return Spec('POST','https://api.usaspending.gov/api/v2/search/spending_by_award/',json_body=body)
    if operation=='openfda-drug-events':
        q=[('search',text(p,'search',500,True)),('limit',str(integer(p,'limit',20,1,100))),('skip',str(integer(p,'skip',0,0,25000)))]
        key=secret('OPENFDA_API_KEY',False)
        if key: q.append(('api_key',key))
        return Spec('GET','https://api.fda.gov/drug/event.json',params=q,credential_mode='optional-api-key' if key else 'none')
    if operation=='eurostat-data':
        flow=text(p,'dataflow',80,True); key=text(p,'key',300,True)
        q=[('format','csvfile')]
        if p.get('start_period'): q.append(('startPeriod',text(p,'start_period',20)))
        if p.get('end_period'): q.append(('endPeriod',text(p,'end_period',20)))
        return Spec('GET',f'https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0/data/ESTAT/{flow}/1.0/{key}',params=q,response_kind='text')
    if operation=='our-world-in-data-series':
        return Spec('GET',f"https://ourworldindata.org/grapher/{text(p,'slug',120,True)}.csv",response_kind='text')
    if operation=='hdx-hapi-metadata':
        app=secret('HDX_HAPI_APP_IDENTIFIER'); return Spec('GET','https://hapi.humdata.org/api/v2/metadata/',params=[('app_identifier',app)],credential_mode='app-identifier')
    if operation=='iati-activities':
        key=secret('IATI_API_KEY'); body={'q':text(p,'query',500,True),'rows':integer(p,'rows',20,1,100),'start':integer(p,'start',0,0,10000)}
        return Spec('POST','https://api.iatistandard.org/datastore/activity/select',json_body=body,headers={'Ocp-Apim-Subscription-Key':key},credential_mode='api-key')
    if operation=='companies-house-search':
        key=secret('COMPANIES_HOUSE_API_KEY'); q=[('q',text(p,'query',200,True)),('items_per_page',str(integer(p,'items_per_page',20,1,100))),('start_index',str(integer(p,'start_index',0,0,10000)))]
        return Spec('GET','https://api.company-information.service.gov.uk/search/companies',params=q,auth=(key,''),credential_mode='basic-api-key')
    if operation=='sam-opportunities':
        q=[('api_key',secret('SAM_GOV_API_KEY')),('postedFrom',text(p,'posted_from',10,True)),('postedTo',text(p,'posted_to',10,True)),('limit',str(integer(p,'limit',20,1,100))),('offset',str(integer(p,'offset',0,0,1000)))]
        if p.get('keywords'): q.append(('q',text(p,'keywords',200)))
        return Spec('GET','https://api.sam.gov/opportunities/v2/search',params=q,credential_mode='api-key')
    if operation=='openaq-locations':
        key=secret('OPENAQ_API_KEY'); q=[('limit',str(integer(p,'limit',20,1,100))),('page',str(integer(p,'page',1,1,1000)))]
        for s in ('country','city','coordinates','radius'):
            if p.get(s) not in (None,''): q.append((s,str(p[s])))
        return Spec('GET','https://api.openaq.org/v3/locations',params=q,headers={'X-API-Key':key},credential_mode='api-key')
    if operation=='usgs-earthquakes':
        q=[('format','geojson'),('limit',str(integer(p,'limit',200,1,2000))),('orderby','time')]
        for s,t in {'start_time':'starttime','end_time':'endtime','min_magnitude':'minmagnitude','latitude':'latitude','longitude':'longitude','max_radius_km':'maxradiuskm'}.items():
            if p.get(s) not in (None,''): q.append((t,str(p[s])))
        return Spec('GET','https://earthquake.usgs.gov/fdsnws/event/1/query',params=q)
    if operation=='overpass-query':
        q=text(p,'query',8000,True)
        low=q.lower()
        if '[out:json]' not in low or any(x in low for x in ('[out:xml]','adiff','delete','make area','{{')): raise ValueError('overpass query must be bounded read-only JSON QL')
        timeout=integer(p,'timeout_seconds',20,1,25)
        if '[timeout:' not in low: q=f'[out:json][timeout:{timeout}];'+q.replace('[out:json];','',1)
        return Spec('POST','https://overpass-api.de/api/interpreter',data_body={'data':q},response_kind='json')
    if operation=='geonames-search':
        q=[('q',text(p,'query',200,True)),('username',secret('GEONAMES_USERNAME')),('maxRows',str(integer(p,'max_rows',20,1,100))),('startRow',str(integer(p,'start_row',0,0,10000))),('style','FULL')]
        if p.get('country'): q.append(('country',text(p,'country',2)))
        if p.get('feature_class'): q.append(('featureClass',text(p,'feature_class',1)))
        return Spec('GET','https://secure.geonames.org/searchJSON',params=q,credential_mode='username')
    if operation.startswith('openrouteservice-'):
        key=secret('OPENROUTESERVICE_API_KEY'); headers={'Authorization':key,'Content-Type':'application/json'}
        if operation=='openrouteservice-geocode':
            q=[('text',text(p,'text',300,True)),('size',str(integer(p,'size',10,1,40)))]
            if p.get('country'): q.append(('boundary.country',text(p,'country',2).lower()))
            if p.get('focus_point_lat') is not None and p.get('focus_point_lon') is not None:
                q.extend([('focus.point.lat',str(float(p['focus_point_lat']))),('focus.point.lon',str(float(p['focus_point_lon'])))])
            return Spec('GET','https://api.heigit.org/pelias/v1/search',params=q,headers={'Authorization':key},credential_mode='api-key')
        profile=text(p,'profile',30,True)
        if operation=='openrouteservice-directions':
            body={'coordinates':coords(p.get('coordinates'),'coordinates',2,50)}
            for name in ('preference','units','language','instructions'):
                 if p.get(name) is not None: body[name]=p[name]
            return Spec('POST',f'https://api.heigit.org/openrouteservice/v2/directions/{profile}/geojson',json_body=body,headers=headers,credential_mode='api-key')
        if operation=='openrouteservice-matrix':
            body={'locations':coords(p.get('locations'),'locations',2,50),'metrics':p.get('metrics') or ['duration']}
            if p.get('units'): body['units']=p['units']
            return Spec('POST',f'https://api.heigit.org/openrouteservice/v2/matrix/{profile}',json_body=body,headers=headers,credential_mode='api-key')
        body={'locations':coords(p.get('locations'),'locations',1,5),'range':p.get('range')}
        if not isinstance(body['range'],list) or not 1<=len(body['range'])<=10: raise ValueError('range is invalid')
        body['range_type']=p.get('range_type') or 'time'
        if p.get('units'): body['units']=p['units']
        return Spec('POST',f'https://api.heigit.org/openrouteservice/v2/isochrones/{profile}',json_body=body,headers=headers,credential_mode='api-key')
    if operation=='opentopography-globaldem':
        south,north,west,east=map(float,(p['south'],p['north'],p['west'],p['east']))
        if not south<north or not west<east or (north-south)*(east-west)>25: raise ValueError('DEM bounding box must be ordered and <=25 square degrees')
        q=[('demtype',text(p,'dem_type',20,True)),('south',str(south)),('north',str(north)),('west',str(west)),('east',str(east)),('outputFormat',str(p.get('output_format') or 'GTiff')),('API_Key',secret('OPENTOPOGRAPHY_API_KEY'))]
        return Spec('GET','https://portal.opentopography.org/API/globaldem',params=q,credential_mode='api-key',response_kind='binary')
    if operation=='geoboundaries-release':
        product=str(p.get('product') or 'gbOpen'); iso=text(p,'iso3',3,True); adm=text(p,'admin_level',4,True)
        return Spec('GET',f'https://www.geoboundaries.org/api/current/{product}/{iso}/{adm}/')
    if operation=='soilgrids-wcs-capabilities':
        prop=text(p,'property',20,True); return Spec('GET','https://maps.isric.org/mapserv',params=[('map',f'/map/{prop}.map'),('SERVICE','WCS'),('VERSION','2.0.1'),('REQUEST','GetCapabilities')],response_kind='text')
    if operation=='global-fishing-watch-vessels':
        key=secret('GLOBAL_FISHING_WATCH_API_TOKEN'); q=[('query',text(p,'query',100,True)),('limit',str(integer(p,'limit',20,1,50)))]
        return Spec('GET','https://gateway.api.globalfishingwatch.org/v3/vessels/search',params=q,headers={'Authorization':f'Bearer {key}'},credential_mode='bearer-token')
    if operation=='opencharge-map-poi':
        q=[('latitude',str(float(p['latitude']))),('longitude',str(float(p['longitude']))),('distance',str(float(p.get('distance_km') or 25))),('distanceunit','KM'),('maxresults',str(integer(p,'max_results',50,1,100))),('compact','true'),('verbose','false')]
        key=secret('OPENCHARGEMAP_API_KEY',False); headers={'X-API-Key':key} if key else {}
        return Spec('GET','https://api.openchargemap.io/v3/poi/',params=q,headers=headers,credential_mode='optional-api-key' if key else 'none')
    if operation=='transitland-routes':
        q=[('limit',str(integer(p,'limit',20,1,100)))]
        if p.get('bbox'): q.append(('bbox',text(p,'bbox',100)))
        if p.get('operator_onestop_id'): q.append(('operator_onestop_id',text(p,'operator_onestop_id',100)))
        key=secret('TRANSITLAND_API_KEY',False)
        if key: q.append(('apikey',key))
        return Spec('GET','https://transit.land/api/v2/rest/routes',params=q,credential_mode='optional-api-key' if key else 'none')
    if operation=='nbs-search':
        return Spec('GET','https://data.stats.gov.cn/search.htm',params=[('s',text(p,'query',100,True)),('m','searchdata')])
    if operation=='nbs-query-data':
        q=[('m','QueryData'),('dbcode',text(p,'dbcode',4,True)),('rowcode',text(p,'rowcode',4,True)),('colcode',text(p,'colcode',4,True)),('wds',json.dumps(p.get('wds') or [],ensure_ascii=False,separators=(',',':'))),('dfwds',json.dumps(p.get('dfwds') or [],ensure_ascii=False,separators=(',',':'))),('k1',str(int(time.time()*1000))),('h','1')]
        return Spec('GET','https://data.stats.gov.cn/easyquery.htm',params=q,headers={'Referer':'https://data.stats.gov.cn/'})
    if operation=='nbs-new-tree':
        return Spec('GET','https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndexTreeAsync',params=[('pid',text(p,'parent_id',80)),('code',str(integer(p,'code',1,1,14)))],headers={'Referer':'https://data.stats.gov.cn/dg/website/page.html'})
    if operation=='nbs-new-indicators':
        return Spec('GET','https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndicatorsByCid',params=[('cid',text(p,'catalog_id',80,True)),('dt',''),('name',text(p,'name',100)),('rootId',text(p,'root_id',80))],headers={'Referer':'https://data.stats.gov.cn/dg/website/page.html'})
    raise ValueError(f'unsupported operation: {operation}')

def row_count(payload:Any)->int:
    if isinstance(payload,list): return len(payload)
    if isinstance(payload,Mapping):
        for key in ('data','results','features','entries','items','records','geonames','response','portals','centers'):
            v=payload.get(key)
            if isinstance(v,list): return len(v)
            if isinstance(v,Mapping):
                for sub in ('data','results','items','records'):
                    sv=v.get(sub)
                    if isinstance(sv,list): return len(sv)
        return 1
    return 0

def execute(ticket_path:Path,output_dir:Path)->int:
    output_dir.mkdir(parents=True,exist_ok=True)
    ticket=load_json(ticket_path); validate_ticket(ticket,schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH)
    operation=str(ticket['operation']); p=dict(ticket.get('parameters') or {}); acc=dict(ticket['acceptance'])
    timeout=bounded_int(acc.get('timeout_seconds'),default=30,minimum=5,maximum=120,name='timeout_seconds')
    max_bytes=bounded_int(acc.get('max_response_bytes'),default=5000000,minimum=1024,maximum=20000000,name='max_response_bytes')
    started_at,started_perf=utc_now(),time.perf_counter(); status='INTEL_PUBLIC_DATA_FAILED'; failure=None; snapshot=None
    metadata={'upstream_called':False,'requests_per_ticket_max':1,'automatic_retry':False,'automatic_pagination':False,'secret_values_exposed':False,'operation':operation}
    try:
        spec=build(operation,p)
        if isinstance(spec,dict): snapshot={'provider':'public-data-geospatial','operation':operation,'row_count':row_count(spec),'data':spec}
        else:
            parsed=urlparse(spec.url)
            if parsed.scheme!='https' or not parsed.hostname: raise RuntimeError('non-HTTPS or invalid fixed endpoint')
            headers={'Accept':'application/json, application/xml;q=0.9, text/csv;q=0.8, text/plain;q=0.7','User-Agent':'intelligence-center-public-data/1',**(spec.headers or {})}
            kwargs={'params':spec.params,'headers':headers,'timeout':timeout,'allow_redirects':False}
            if spec.auth: kwargs['auth']=spec.auth
            if spec.method=='POST':
                if spec.json_body is not None: kwargs['json']=spec.json_body
                if spec.data_body is not None: kwargs['data']=spec.data_body
                response=requests.post(spec.url,**kwargs)
            else: response=requests.get(spec.url,**kwargs)
            raw=bytes(response.content or b'')
            metadata.update({'upstream_called':True,'api_host':parsed.hostname,'request_path':parsed.path,'http_status':response.status_code,'content_type':response.headers.get('Content-Type',''),'response_bytes_raw':len(raw),'credential_mode':spec.credential_mode})
            if len(raw)>max_bytes: raise RuntimeError(f'response exceeds acceptance.max_response_bytes={max_bytes}')
            if not response.ok: raise RuntimeError(f'upstream HTTP {response.status_code}: {raw[:1000].decode("utf-8",errors="replace")}')
            if spec.response_kind=='binary':
                stored=raw; (output_dir/'response.bin').write_bytes(stored); data={'binary':True,'content_type':response.headers.get('Content-Type',''),'bytes':len(stored)}
            elif spec.response_kind=='text':
                value=raw.decode('utf-8',errors='replace'); stored=(value if value.endswith('\n') else value+'\n').encode(); (output_dir/'response.txt').write_bytes(stored); data={'text':value[:200000],'truncated_for_snapshot':len(value)>200000}
            else:
                try: data=response.json()
                except ValueError:
                    value=raw.decode('utf-8',errors='replace'); data={'text':value[:200000],'truncated_for_snapshot':len(value)>200000}
                stored=(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode(); (output_dir/'response.json').write_bytes(stored)
            if len(stored)>max_bytes: raise RuntimeError('sanitized response exceeds max_response_bytes')
            rows=row_count(data); snapshot={'provider':'public-data-geospatial','operation':operation,'row_count':rows,'data':data}
            metadata.update({'response_bytes':len(stored),'response_sha256':bytes_sha(stored),'row_count':rows})
        status='INTEL_PUBLIC_DATA_COMPLETED'
    except Exception as exc: failure={'type':type(exc).__name__,'message':str(exc)[:2000]}
    return finish_execution(ticket=ticket,output_dir=output_dir,status=status,snapshot=snapshot,metadata=metadata,failure=failure,started_at=started_at,started_perf=started_perf,schema_prefix='public-data-geospatial')

if __name__=='__main__':
    raise SystemExit(run_cli(execute=execute,ticket_prefix='[intel-public-data]',schema_path=SCHEMA_PATH,catalog_path=CATALOG_PATH,status_schema='public-data-geospatial-ticket-status-v1',display_name='Public Data & Geospatial'))
