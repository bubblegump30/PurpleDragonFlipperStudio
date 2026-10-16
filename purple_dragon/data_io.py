"""Bounded UTF-8 and strict JSON input shared by local stores and file imports."""
import json
import math
from pathlib import Path


def read_text(path, limit):
    with Path(path).open('rb') as stream:data=stream.read(limit+1)
    if len(data)>limit:raise ValueError('File exceeds the '+str(limit)+'-byte limit.')
    return data.decode('utf-8-sig')


def load_json(text, limit=5_000_000):
    if not isinstance(text,str):raise ValueError('JSON input must be text.')
    try:
        if len(text.encode('utf-8'))>limit:raise ValueError('JSON exceeds its size limit.')
        def pairs(items):
            result={}
            for key,value in items:
                if key in result:raise ValueError('Duplicate JSON fields are not supported.')
                result[key]=value
            return result
        def constant(value):raise ValueError('Non-finite JSON numbers are not supported.')
        def integer(value):
            if len(value)>64:raise ValueError('JSON integer exceeds its digit limit.')
            return int(value)
        result=json.loads(text,object_pairs_hook=pairs,parse_constant=constant,parse_int=integer)
        stack=[(result,0)]
        while stack:
            value,depth=stack.pop()
            if depth>32:raise ValueError('JSON nesting exceeds 32 levels.')
            if isinstance(value,dict):stack.extend((x,depth+1) for x in value.values())
            elif isinstance(value,list):stack.extend((x,depth+1) for x in value)
            elif isinstance(value,str):value.encode('utf-8')
            elif isinstance(value,float) and not math.isfinite(value):raise ValueError('Non-finite JSON numbers are not supported.')
        return result
    except (RecursionError,UnicodeError,OverflowError) as exc:
        raise ValueError('JSON contains excessive nesting or invalid Unicode.') from exc


def setting_int(settings, key, default, low, high):
    try:value=int(settings.value(key,default))
    except (TypeError,ValueError,OverflowError):return default
    return max(low,min(high,value))
