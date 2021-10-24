import json
from typing import Union, List, Dict, Tuple, Optional, Callable, Any, Iterator
from hbreader import hbread

from .extendednamespace import ExtendedNamespace

# Possible types in the JsonObj representation
JsonObjTypes = Union["JsonObj", List["JsonObjTypes"], str, bool, int, float, None]

# Types in the pure JSON representation
JsonTypes = Union[Dict[str, "JsonTypes"], List["JsonTypes"], str, bool, int, float, None]

# Control variables -- note that subclasses can add to this list
hide = ['_if_missing', '_root']


class JsonObj(ExtendedNamespace):
    """ A namespace/dictionary representation of a JSON object. Any name in a JSON object that is a valid python
    identifier is represented as a first-class member of the objects.  JSON identifiers that begin with "_" are
    disallowed in this implementation.
    """

    def __init__(self, list_or_dict: Optional[Union[List, Dict]] = None, *,
                 _if_missing: Callable[["JsonObj", str], Tuple[bool, Any]] = None,
                 **kwargs) -> None:
        """ Construct a JsonObj from set of keyword/value pairs

        :param list_or_dict: A list or dictionary that can be used to construct the object
        :param _if_missing: Function to call if attempt is made to access an undefined value.  Function takes JsonObj
        instance and parameter as input and returns a tuple -- handled (y or n) and result.  If handled is 'n' inline
        processing proceeds.
        :param kwargs: A dictionary as an alternative constructor.
        """
        if _if_missing and _if_missing != self._if_missing:
            self._if_missing = _if_missing
        if list_or_dict is not None:
            if len(kwargs):
                raise TypeError("Constructor can't have both a single item and a dict")
            if isinstance(list_or_dict, (dict, JsonObj)):
                self._init_from_dict(list_or_dict)
            elif isinstance(list_or_dict, list):
                ExtendedNamespace.__init__(self,
                                           _root=[JsonObj(e) if isinstance(e, (dict, list)) else
                                                  e for e in list_or_dict])
            else:
                raise TypeError("JSON Object can only be a list or dictionary")
        else:
            self._init_from_dict(kwargs)

    @staticmethod
    def _if_missing(obj: "JsonObj", item: str) -> Tuple[bool, Any]:
        return False, None

    def _init_from_dict(self, d: Union[dict, "JsonObj"]) -> None:
        """ Construct a JsonObj from a dictionary or another JsonObj """
        if not isinstance(d, dict):
            d = d._as_dict
        ExtendedNamespace.__init__(self, _if_missing=self._if_missing, **{k: JsonObj(**v) if isinstance(v, dict) else v
                                                                          for k, v in d.items()})

    # ===================================================
    # JSON Serializer method
    # ===================================================
    @staticmethod
    def _default(obj, filtr: Callable[[dict], dict] = lambda e: e):
        """ return a serialized version of obj or raise a TypeError.  Used by the JSON serializer

        :param obj:
        :param filtr: dictionary filter
        :return: Serialized version of obj
        """
        return filtr(obj._as_dict) if isinstance(obj, JsonObj) else json.JSONDecoder().decode(obj)

    # ===================================================
    # Underscore equivalent of useful dictionary functions
    # ===================================================
    def _get(self, item: str, default: JsonObjTypes = None) -> JsonObjTypes:
        """ Equivalent to dictionary get function w/o polluting namespace """
        return self[item] if item in self else default

    def _setdefault(self, k: str, value: Union[Dict, JsonTypes]) -> JsonObjTypes:
        """ Equivalent of dictionary setdefault without messing in namespace """
        if k not in self:
            self[k] = JsonObj(_if_missing=self._if_missing, **value) if isinstance(value, dict) else value
        return self[k]

    def _keys(self) -> List[str]:
        """ Return all non-hidden keys """
        for k in self.__dict__.keys():
            if k not in hide:
                yield k

    def _items(self) -> List[Tuple[str, JsonObjTypes]]:
        """ Return all non-hidden items """
        for k, v in self.__dict__.items():
            if k not in hide:
                yield k, v

    # ===================================================
    # Various converters -- use exposed methods in place of underscores
    # ===================================================
    def _as_json_obj(self) -> JsonTypes:
        """ Return self as pure json """
        return json.loads(self._as_json_dumps())

    def __getitem__(self, item):
        if '_root' in self:
            return self._root[item]
        else:
            found, val = self._if_missing(self, item)
            if found:
                return val
            else:
                return super().__getitem__(item)

    def __getattr__(self, item):
        found, val = self._if_missing(self, item)
        if found:
            return val
        else:
            return super().__getattribute__(item)

    def __setattr__(self, key, value):
        super().__setattr__(key, JsonObj(value) if isinstance(value, dict) else value)

    @property
    def _as_json(self) -> str:
        """ Convert a JsonObj into straight json text

        :return: JSON formatted str
        """
        return json.dumps(self, default=self._default)

    def _as_json_dumps(self, indent: str = '   ', filtr: Callable[[dict], dict] = None, **kwargs) -> str:
        """ Convert to a stringified json object.

        This is the same as _as_json with the exception that it isn't
        a property, meaning that we can actually pass arguments...
        :param indent: indent argument to dumps
        :param filtr: dictionary filter
        :param kwargs: other arguments for dumps
        :return: JSON formatted string
        """
        return json.dumps(self, default=lambda obj: self._default(obj, filtr) if filtr else self._default(obj),
                          indent=indent, **kwargs)

    @staticmethod
    def _as_list(value: List[JsonObjTypes]) -> List[JsonTypes]:
        """ Return a json array as a list

        :param value: array
        :return: array with JsonObj instances removed
        """
        return [e._as_dict if isinstance(e, JsonObj) else e for e in value]

    @property
    def _as_dict(self) -> Dict[str, JsonTypes]:
        """ Convert a JsonObj into a straight dictionary

        :return: dictionary that cooresponds to the json object
        """
        return {k: v._as_dict if isinstance(v, JsonObj) else self._as_list(v) if isinstance(v, list) else v
                for k, v in self._items()}


def loads(s: str, **kwargs) -> JsonObj:
    """ Convert a json_str into a JsonObj

    :param s: a str instance containing a JSON document
    :param kwargs: arguments see: json.load for details
    :return: JsonObj representing the json string
    """
    if isinstance(s, (bytes, bytearray)):
        s = s.decode(json.detect_encoding(s), 'surrogatepass')
    return json.loads(s, object_hook=lambda pairs: JsonObj(**pairs), **kwargs)


def load(source, **kwargs) -> JsonObj:
    """ Deserialize a JSON source.

    :param source: a URI, File name or a .read()-supporting file-like object containing a JSON document
    :param kwargs: arguments. see: json.load for details
    :return: JsonObj representing fp
    """
    return loads(hbread(source, accept_header="application/json, text/json;q=0.9"), **kwargs)


def as_dict(obj: Union[JsonObj, List]) -> Union[List, Dict[str, JsonTypes]]:
    """ Convert a JsonObj into a straight dictionary

    :param obj: pseudo 'self'
    :return: dictionary that cooresponds to the json object
    """
    return [e._as_dict if isinstance(e, JsonObj) else e for e in obj] if isinstance(obj, list) else obj._as_dict


def as_list(obj: Union[JsonObj, List]) -> List[JsonTypes]:
    """ Return a json array as a list

    :param obj: pseudo 'self'
    """
    return obj._as_list


def as_json(obj: Union[JsonObj, List], indent: Optional[str] = '   ',
            filtr: Callable[[dict], dict] = None, **kwargs) -> str:
    """ Convert obj to json string representation.

        :param obj: pseudo 'self'
        :param indent: indent argument to dumps
        :param filtr: filter to remove unwanted elements
        :param kwargs: other arguments for dumps
        :return: JSON formatted string
       """
    if isinstance(obj, JsonObj) and '_root' in obj:
        obj = obj._root
    return obj._as_json_dumps(indent, filtr=filtr, **kwargs) if isinstance(obj, JsonObj) else \
        json.dumps(obj, default=lambda o: JsonObj._default(o, filtr) if filtr else JsonObj._default(o),
                      indent=indent, **kwargs)


def as_json_obj(obj: Union[JsonObj, List]) -> JsonTypes:
    """ Return obj as pure python json (vs. JsonObj)
        :param obj: pseudo 'self'
        :return: Pure python json image
    """
    return [e._as_json_obj() if isinstance(e, JsonObj) else e for e in obj] \
        if isinstance(obj, list) else obj._as_json_obj()


def get(obj: JsonObj, item: str, default: JsonObjTypes = None) -> JsonObjTypes:
    """ Dictionary get routine """
    return obj._get(item, default)


def setdefault(obj: JsonObj, k: str, value: Union[Dict, JsonTypes]) -> JsonObjTypes:
    """ Dictionary setdefault reoutine """
    return obj._setdefault(k, value)


def keys(obj: JsonObj) -> Iterator[str]:
    """ same as dict keys() without polluting the namespace """
    return obj._keys()


def items(obj: JsonObj) -> Iterator[Tuple[str, JsonObjTypes]]:
    """ Same as dict items() except that the values are JsonObjs instead of vanilla dictionaries
    :return:
    """
    return obj._items()
