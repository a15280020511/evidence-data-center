#!/usr/bin/env python3
"""Connector health, source conflict and immutable snapshot metadata helpers."""
from __future__ import annotations
import hashlib, json, math
from datetime import datetime, timezone
from typing import Any

class EvidenceQualityError(ValueError): pass

def classify_health(connector_id: str, http_success_rate: float, business_non_empty_rate: float, freshness_seconds: float, *, schema_changed: bool=False, rate_limited: bool=False, license_or_cost_changed: bool=False, retired: bool=False) -> dict[str, Any]:
    values=[http_success_rate,business_non_empty_rate]
    if not connector_id or any(not 0<=float(v)<=1 for v in values) or freshness_seconds<0: raise EvidenceQualityError('invalid connector health metrics')
    if retired: status='RETIRED'
    elif schema_changed or license_or_cost_changed or http_success_rate<.5 or business_non_empty_rate<.5: status='BLOCKED'
    elif rate_limited or http_success_rate<.95 or business_non_empty_rate<.9: status='DEGRADED'
    else: status='PRODUCTION'
    return {'connector_id':connector_id,'status':status,'last_checked_at':datetime.now(timezone.utc).isoformat(),'http_success_rate':float(http_success_rate),'business_non_empty_rate':float(business_non_empty_rate),'freshness_seconds':float(freshness_seconds),'schema_changed':bool(schema_changed),'rate_limited':bool(rate_limited),'license_or_cost_changed':bool(license_or_cost_changed)}

def compare_sources(metric: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    if not metric or len(sources)<2: raise EvidenceQualityError('metric and at least two sources required')
    normalized=[]
    for s in sources:
        value=float(s['value'])
        if not math.isfinite(value): raise EvidenceQualityError('non-finite source value')
        normalized.append({**s,'value':value})
    originals={str(s.get('original_publisher') or s.get('source_id')) for s in normalized}
    correlated=len(originals)<len(normalized)
    preferred=sorted(normalized,key=lambda s:(not bool(s.get('is_primary')), -float(s.get('quality_score',0)), str(s.get('source_id'))))[0]
    values=[s['value'] for s in normalized]; spread=max(values)-min(values); scale=max(abs(sum(values)/len(values)),1e-12)
    return {'schema_version':'source-comparison-v1','metric':metric,'sources':normalized,'recommended_source':preferred['source_id'],'merge_allowed':not correlated and spread/scale<=.05,'correlated_sources_detected':correlated,'difference_summary':f'absolute_spread={spread:.12g}; relative_spread={spread/scale:.6g}'}

def snapshot_metadata(response: bytes, source_url: str, *, observed_at: str, data_vintage: str, unit: str, geography: str, time_scope: str, license: str) -> dict[str,str]:
    fields=[source_url,observed_at,data_vintage,unit,geography,time_scope,license]
    if any(not str(v).strip() for v in fields): raise EvidenceQualityError('snapshot metadata fields must be non-empty')
    return {'observed_at':observed_at,'data_vintage':data_vintage,'source_url_hash':hashlib.sha256(source_url.encode()).hexdigest(),'response_sha256':hashlib.sha256(response).hexdigest(),'unit':unit,'geography':geography,'time_scope':time_scope,'license':license}
