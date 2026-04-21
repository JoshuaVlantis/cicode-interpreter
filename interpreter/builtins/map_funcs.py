"""CiCode map (dictionary) built-in functions."""


def register(registry, interp):
    _maps = {}
    _next_handle = [1]
    _iterators = {}

    def _unwrap(v):
        from interpreter import Ref
        return v.value if isinstance(v, Ref) else v

    def MapOpen():
        h = _next_handle[0]
        _next_handle[0] += 1
        _maps[h] = {}
        return h

    def MapClose(hMap):
        h = interp.to_int(_unwrap(hMap))
        _maps.pop(h, None)
        _iterators.pop(h, None)

    def MapValueSet(hMap, sKey, sValue):
        h = interp.to_int(_unwrap(hMap))
        if h in _maps:
            _maps[h][interp.to_str(_unwrap(sKey))] = interp.to_str(_unwrap(sValue))

    def MapValueGet(hMap, sKey):
        h = interp.to_int(_unwrap(hMap))
        if h in _maps:
            return _maps[h].get(interp.to_str(_unwrap(sKey)), '')
        return ''

    def MapKeyExists(hMap, sKey):
        h = interp.to_int(_unwrap(hMap))
        if h in _maps:
            return 1 if interp.to_str(_unwrap(sKey)) in _maps[h] else 0
        return 0

    def MapKeyDelete(hMap, sKey):
        h = interp.to_int(_unwrap(hMap))
        if h in _maps:
            _maps[h].pop(interp.to_str(_unwrap(sKey)), None)

    def MapKeyCount(hMap):
        h = interp.to_int(_unwrap(hMap))
        return len(_maps.get(h, {}))

    def MapKeyFirst(hMap):
        h = interp.to_int(_unwrap(hMap))
        if h in _maps and _maps[h]:
            keys = list(_maps[h].keys())
            _iterators[h] = {'keys': keys, 'idx': 0}
            return keys[0]
        return ''

    def MapKeyNext(hMap):
        h = interp.to_int(_unwrap(hMap))
        it = _iterators.get(h)
        if it:
            it['idx'] += 1
            if it['idx'] < len(it['keys']):
                return it['keys'][it['idx']]
        return ''

    def MapExists(sName):
        return 0

    def MapClear(hMap):
        h = interp.to_int(_unwrap(hMap))
        if h in _maps:
            _maps[h].clear()

    fns = {
        'mapopen': MapOpen,
        'mapclose': MapClose,
        'mapvalueset': MapValueSet,
        'mapvalueget': MapValueGet,
        'mapkeyexists': MapKeyExists,
        'mapkeydelete': MapKeyDelete,
        'mapkeycount': MapKeyCount,
        'mapkeyfirst': MapKeyFirst,
        'mapkeynext': MapKeyNext,
        'mapexists': MapExists,
        'mapclear': MapClear,
    }
    registry.update(fns)
