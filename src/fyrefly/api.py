"""Fyrefly API testing: one function, api.gui(), opens a free Postman-style window in your browser.

    from fyrefly import api

    api.gui()

Everything else in this file is the engine behind that window. It is private (_engine) and not part of the public API.
"""
import json as _json
import mimetypes
import os
import re
import statistics
import time
import warnings
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

__all__ = ["api"]

_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
_MISSING = object()
_TYPE_NAMES = {
    "int": int, "integer": int, "float": float, "number": (int, float), "str": str, "string": str,
    "bool": bool, "boolean": bool, "list": list, "array": list, "dict": dict, "object": dict,
    "null": type(None), "none": type(None), "any": object,
}
_SECRET_HEADERS = ("authorization", "x-api-key", "proxy-authorization", "cookie")
_SECRET_WORDS = ("authorization", "token", "secret", "password", "passwd", "cookie", "signature", "x-auth")
_VAR = re.compile(r"\{\{\s*([A-Za-z0-9_.\-$]+)\s*\}\}")


def _dynamic(name):
    """Built-in values that are new every time they are used: {{$guid}}, {{$timestamp}}, {{$isoTimestamp}}, {{$randomInt}}."""
    import datetime
    import random
    import uuid
    n = name.lower()
    if n in ("$guid", "$randomuuid"):
        return str(uuid.uuid4())
    if n == "$timestamp":
        return str(int(time.time()))
    if n == "$isotimestamp":
        return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    if n == "$randomint":
        return str(random.randint(0, 1000))
    return None


def _is_secret(name):
    """True for any header whose value should never be printed (Authorization, token, X-API-Key, ...)."""
    n = str(name).lower()
    return n in _SECRET_HEADERS or n.endswith("key") or any(w in n for w in _SECRET_WORDS)


def _fill_vars(obj, variables, strict=True):
    """Replace every {{name}} in strings (also inside dicts, lists and tuples) with its value."""
    missing = []

    def sub(text):
        def rep(m):
            name = m.group(1)
            if name in variables:
                return str(variables[name])
            if name.startswith("$") and _dynamic(name) is not None:
                return _dynamic(name)
            missing.append(name)
            return m.group(0)
        return _VAR.sub(rep, text)

    def walk(o):
        if isinstance(o, str):
            return sub(o)
        if isinstance(o, dict):
            return {(walk(k) if isinstance(k, str) else k): walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        if isinstance(o, tuple):
            return tuple(walk(v) for v in o)
        return o

    out = walk(obj)
    if missing and strict:
        names = list(dict.fromkeys(missing))
        raise APIError("No value for " + ", ".join("{{" + n + "}}" for n in names) +
                       ". Give each one a value with api.vars(" + ", ".join(f'{n}="..."' if n.isidentifier() else "{...}" for n in names) + ").")
    return out


def _load_files(files):
    """Turn files= into [(field, (filename, bytes, mimetype))]. Text parts stay as (field, (None, text))."""
    if not files:
        return []
    if isinstance(files, str):
        items = []
        for piece in re.split(r"[,\n;]+", files):
            if not piece.strip():
                continue
            if "=" not in piece:
                raise ValueError(f"'{piece.strip()}' needs an equals sign. Type files like:  file=report.pdf")
            k, v = piece.split("=", 1)
            items.append((k.strip(), v.strip()))
    elif isinstance(files, dict):
        items = list(files.items())
    else:
        items = list(files)
    out = []
    for name, val in items:
        if isinstance(val, str):
            path = os.path.expanduser(val.strip().strip("\"'"))
            if not os.path.isfile(path):
                raise ValueError(f"File not found: {val}. Give the full path to the file, such as files=\"file=C:/docs/report.pdf\".")
            with open(path, "rb") as fh:
                content = fh.read()
            fn = os.path.basename(path)
            out.append((name, (fn, content, mimetypes.guess_type(fn)[0] or "application/octet-stream")))
        elif isinstance(val, tuple) and len(val) == 2 and val[0] is None:
            out.append((name, (None, str(val[1]))))
        elif isinstance(val, tuple) and len(val) >= 2:
            fn, content = val[0], val[1]
            if isinstance(content, str):
                content = content.encode()
            mime = val[2] if len(val) > 2 and val[2] else (mimetypes.guess_type(str(fn))[0] or "application/octet-stream")
            out.append((name, (fn, content, mime)))
        else:
            raise ValueError("files= must be a path like \"file=report.pdf\", or a dict of field name to file path")
    return out


class APIError(Exception):
    """The request never produced an HTTP response (bad address, no connection, timeout)."""


# ---------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------

def _dig(data, path):
    """Follow a dotted path such as 'items.0.name' through dicts and lists. Returns _MISSING if absent."""
    cur = data
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.lstrip("-").isdigit() and -len(cur) <= int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return _MISSING
    return cur


def _type_name(t):
    if isinstance(t, tuple):
        return " or ".join(_type_name(x) for x in t)
    return "null" if t is type(None) else getattr(t, "__name__", str(t))


def _type_ok(value, expected):
    if expected is object or expected == "any":
        return True
    if isinstance(expected, str):
        expected = _TYPE_NAMES.get(expected.lower())
        if expected is None:
            return False
        if expected is object:
            return True
    if expected is None:
        expected = type(None)
    if isinstance(value, bool):  # bool is an int in Python, but not in JSON
        return expected is bool or (isinstance(expected, tuple) and bool in expected)
    return isinstance(value, expected)


def _validate(data, schema, path=""):
    """Return a list of problems (empty list = valid). See Result.schema() for the schema language."""
    problems = []
    here = path or "response"
    if isinstance(schema, dict):
        if not isinstance(data, dict):
            return [f"{here}: expected an object, got {_type_name(type(data))}"]
        for key, sub in schema.items():
            optional = key.startswith("?")
            name = key[1:] if optional else key
            if name not in data:
                if not optional:
                    problems.append(f"{path + '.' if path else ''}{name}: missing")
                continue
            problems += _validate(data[name], sub, f"{path + '.' if path else ''}{name}")
    elif isinstance(schema, list):
        if not isinstance(data, list):
            return [f"{here}: expected a list, got {_type_name(type(data))}"]
        if len(schema) == 1:
            for i, item in enumerate(data):
                problems += _validate(item, schema[0], f"{path}[{i}]")
    else:
        if not _type_ok(data, schema):
            shown = schema if not isinstance(schema, str) else _TYPE_NAMES.get(schema.lower(), schema)
            problems.append(f"{here}: expected {_type_name(shown)}, got {_type_name(type(data))}")
    return problems


def _human_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 ** 2:.1f} MB"


def _substitute(obj, variables):
    """Replace {name} in every string inside obj with a saved value."""
    if not variables:
        return obj
    if isinstance(obj, str):
        for k, v in variables.items():
            obj = obj.replace("{" + k + "}", str(v))
        return obj
    if isinstance(obj, dict):
        return {k: _substitute(v, variables) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute(v, variables) for v in obj]
    return obj


def _status_matches(status, want):
    if isinstance(want, str):
        m = re.fullmatch(r"([1-5])xx", want.lower())
        if m:
            return status // 100 == int(m.group(1))
        return str(status) == want
    if isinstance(want, (list, tuple, set)):
        return any(_status_matches(status, w) for w in want)
    return status == want


def _parse_headers(headers):
    """Headers as a dict, or typed simply as  "Name: value; Other-Name: value"  (one per line also works)."""
    if not headers:
        return {}
    if isinstance(headers, dict):
        return dict(headers)
    out = {}
    for piece in re.split(r"[;\n]+", str(headers)):
        if not piece.strip():
            continue
        if ":" not in piece:
            raise ValueError(f"'{piece.strip()}' needs a colon. Type headers like:  Accept: application/json; X-Team: blue")
        k, v = piece.split(":", 1)
        out[k.strip()] = v.strip()
    return out


_STATUS_HELP = {
    200: "OK. It worked.", 201: "Created. The new item was saved.", 202: "Accepted. The server will finish the job later.",
    204: "Done. It worked, and there is nothing to show back.",
    301: "Moved. The address has changed.", 302: "Moved. The address has changed.",
    400: "Bad request. The server did not understand what was sent. Check the values you are sending.",
    401: "Not logged in. This address needs a login. Add token=\"...\" (or user=\"...\", password=\"...\").",
    403: "Not allowed. You are known, but you do not have permission to do this.",
    404: "Not found. The address is wrong, or that item does not exist.",
    405: "Wrong action. This address does not accept that method. Try a different one (get, post, put, delete).",
    408: "The server waited too long for the request.",
    409: "Conflict. This probably already exists.",
    415: "The server does not accept that kind of data.",
    422: "Rejected. The server understood but did not accept the values you sent.",
    429: "Too many requests. Wait a little and try again.",
    500: "Server error. The problem is on the server's side, not yours. Try again later.",
    502: "The server is down or restarting. Try again later.",
    503: "The server is busy or down. Try again later.",
    504: "The server took too long to answer. Try again later.",
}


def _status_help(status):
    if status in _STATUS_HELP:
        return _STATUS_HELP[status]
    return {1: "Information.", 2: "It worked.", 3: "The address has moved.",
            4: "There is a problem with the request you sent.", 5: "The server had a problem."}.get(status // 100, "Unknown status.")


def _speed_word(ms):
    if ms < 300:
        return "fast"
    if ms < 1000:
        return "normal"
    if ms < 3000:
        return "slow"
    return "very slow"


def _guess_value(text):
    t = text.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        return t[1:-1]  # quotes force plain text:  zip="0123"
    low = t.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "none"):
        return None
    try:
        if str(int(t)) == t:  # "0123" or "+91" stay text, so nothing is silently changed
            return int(t)
    except ValueError:
        pass
    try:
        if "." in t and str(float(t)) == t:
            return float(t)
    except ValueError:
        pass
    return t


def _parse_send(send):
    """Turn what a person typed into something to send: a dict, JSON text, or name=value pairs."""
    if send is None or send == "":
        return None
    if isinstance(send, (dict, list, bytes)):
        return send
    text = str(send).strip()
    if text.startswith(("{", "[")):
        try:
            return _json.loads(text)
        except ValueError:
            raise ValueError("That looks like JSON but it is not valid. Check the brackets and quotes, "
                             "or type it simply like:  name=Asha, age=30")
    out = {}
    for piece in re.split(r"[,\n;]+", text):
        if not piece.strip():
            continue
        if "=" not in piece:
            raise ValueError(f"'{piece.strip()}' needs an equals sign. Type it like:  name=Asha, age=30")
        k, v = piece.split("=", 1)
        out[k.strip()] = _guess_value(v)
    return out or None


def _fmt_value(v):
    if isinstance(v, bool):
        return "yes" if v else "no"
    return str(v)


_FILE_LIKE = re.compile(r"(?i:(?:^|[_\-])(?:file|image|photo|attachment|upload|document)s?$)|[a-z](?:File|Image|Photo|Attachment|Upload|Document)s?$")


def _call_text(url, method="get", send=None, headers=None, params=None, auth=None, form=False,
               extra=None, look_for=None, expect=None, show_method=False, files=None):
    """Build a ready-to-copy api.test(...) call. Secrets always appear as placeholders."""
    parts = [f'"{url}"']
    if method != "get" or show_method:
        parts.append(f'method="{method}"')
    if send:
        parts.append('send="' + ", ".join(f"{k}={_fmt_value(v)}" for k, v in send.items()) + '"')
    if files:
        parts.append('files="' + ", ".join(f"{n}=YOUR_FILE_PATH" for n in files) + '"')
    if form:
        parts.append("form=True")
    if headers:
        parts.append('headers="' + "; ".join(
            f"{k}: {'YOUR_VALUE' if _is_secret(k) else v}" for k, v in headers.items()) + '"')
    if params:
        parts.append('params="' + ", ".join(f"{k}={_fmt_value(v)}" for k, v in params.items()) + '"')
    if auth == "token":
        parts.append('token="YOUR_TOKEN"')
    elif auth == "basic":
        parts.append('user="YOUR_USERNAME", password="YOUR_PASSWORD"')
    elif auth == "key":
        parts.append('key="YOUR_API_KEY"')
    if expect is not None:
        parts.append(f"expect={expect}")
    if look_for:
        parts.append("look_for=" + (_json.dumps(look_for) if not isinstance(look_for, str) else f'"{look_for}"'))
    for e in (extra or []):
        parts.append(e)
    return "api.test(" + ", ".join(parts) + ")"


def _server_says(data, text):
    """Pull the server's own explanation and any field names out of an error reply."""
    msgs, fields = [], []

    def walk(v):
        if isinstance(v, str):
            msgs.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and "loc" in item:           # FastAPI style
                    loc = [x for x in item["loc"] if x not in ("body", "query", "path")]
                    if loc:
                        fields.append(str(loc[-1]))
                        msgs.append(f"{loc[-1]}: {item.get('msg', 'invalid')}")
                elif isinstance(item, dict):
                    f = item.get("field") or item.get("param") or item.get("path") or item.get("name")
                    m = item.get("message") or item.get("msg") or item.get("error")
                    if f:
                        fields.append(str(f))
                    if m:
                        msgs.append(f"{f}: {m}" if f else str(m))
                else:
                    walk(item)
        elif isinstance(v, dict):
            if any(k in v for k in ("message", "msg", "error", "detail")) and not any(isinstance(x, list) for x in v.values()):
                for k in ("message", "msg", "error", "detail", "error_description"):
                    if k in v:
                        walk(v[k])
            else:                                                       # {"email": ["can't be blank"]}
                for f, m in v.items():
                    fields.append(str(f))
                    msgs.append(f"{f}: {'; '.join(map(str, m)) if isinstance(m, list) else m}")

    if isinstance(data, dict):
        for k in ("error", "message", "detail", "msg", "errors", "error_description"):
            if k in data:
                walk(data[k])
    elif isinstance(data, list):
        walk(data)
    elif text and text.strip() and len(text) < 300:
        msgs.append(text.strip())
    for m in list(msgs):                                                # "email is required", "missing 'email'"
        for pat in (r"['\"`]?(\w+)['\"`]? (?:is|are) (?:required|missing)", r"missing (?:required )?(?:field |parameter |property )?['\"`]?(\w+)['\"`]?",
                    r"['\"`](\w+)['\"`] is a required property", r"required[:\s]+['\"`]?(\w+)['\"`]?"):
            for f in re.findall(pat, m, re.I):
                if f.lower() not in ("is", "the", "a", "field", "parameter", "property", "required", "and", "or"):
                    fields.append(f)
    dedup = lambda xs: list(dict.fromkeys(xs))
    return dedup(msgs)[:5], dedup(fields)[:8]


def _advise_response(r, ctx):
    """Plain-language fixes for a response that was not what the person wanted."""
    out = []
    st, data = r.status, r.json
    says, fields = _server_says(data, r.text)
    low = " ".join(says).lower()
    www = (r.headers.get("WWW-Authenticate") or "").lower()
    base = dict(url=ctx["url"], method=ctx["method"], send=ctx["body"], headers=ctx["hdrs"], params=ctx["params"],
                form=ctx["form"], expect=ctx["expect"], look_for=ctx["look_for"], files=ctx.get("files") or None)

    def add(what, where, example=None, note=None):
        out.append({"what": what, "where": where, "example": example, "note": note})

    def need_login():
        if "basic" in www:
            kind, where = "basic", "user= and password= (sent for you as a Basic login)"
        elif re.search(r"api[-_ ]?key|x-api-key", low + www):
            kind, where = "key", 'key= (sent for you as the X-API-Key header). If the docs name a different header, use headers="Header-Name: YOUR_KEY" instead'
        else:
            kind, where = "token", "token= (sent for you in the Authorization header as: Bearer YOUR_TOKEN)"
        add("This address needs a login, and none was sent." if not ctx["auth"] else
            "The login you passed was rejected. It may be wrong, expired, or the wrong kind.", where,
            _call_text(auth=kind, **base),
            "Get the token or key from the API's documentation, your account page, or the response of its login call.")

    if st == 401 or (st == 403 and not ctx["auth"]):
        need_login()
    elif st == 403:
        add("You are logged in, but this account is not allowed to do that.", "a different token or account",
            _call_text(auth=ctx["auth"], **base), "Ask the owner of the API for access, or use an account with more permission.")
    elif st == 404:
        add("Nothing exists at this address.", "the address (the part after the website name)",
            None, "Check: 1) the spelling, 2) that the id in it really exists, 3) whether the API needs a prefix such as /api or /v1 first. "
                  "The API's documentation lists the exact paths.")
    elif st == 405:
        allow = r.headers.get("Allow")
        if allow:
            first = allow.split(",")[0].strip().lower()
            add(f"This address does not accept {ctx['method'].upper()}. It accepts: {allow}.", "method=",
                _call_text(**{**base, "method": first}, show_method=True))
        else:
            add(f"This address does not accept {ctx['method'].upper()}.", "method=", None,
                'Try another action: method="get", "post", "put", "patch" or "delete". The API documentation shows which one this address uses.')
    elif st == 409:
        add("That already exists, or clashes with something that does.", "the values in send=",
            _call_text(**base), "Change the value that has to be unique (an email or a name, for example) and run it again.")
    elif st == 415:
        if ctx["form"]:
            add("The server does not accept a web form here.", "form= (remove it, to send JSON instead)", _call_text(**{**base, "form": False}))
        else:
            add("The server does not accept this kind of data.", "form= or headers=", _call_text(**{**base, "form": True}),
                'If it still fails, set the type yourself: headers="Content-Type: application/json"')
    elif st == 429:
        wait = r.headers.get("Retry-After")
        add("Too many requests, too quickly.", "nothing to pass. Wait, then run it again.", None,
            f"The server asks you to wait {wait} second(s)." if wait else "Wait a minute, and use a smaller times= if you set one.")
    elif 300 <= st < 400:
        loc = r.headers.get("Location")
        if loc:
            add("The address has moved.", "the address", _call_text(**{**base, "url": loc}))
    elif st >= 500:
        add("The server had a problem. Nothing you pass can fix a server error.", "nothing to pass", None,
            "Try again in a few minutes. If it only fails with certain data, check what you pass in send=.")
    elif st >= 400:
        body = ctx["body"] or {}
        have = set(body) | set(ctx.get("files") or [])
        missing = [f for f in fields if f not in have]
        if missing and ctx["method"] in ("post", "put", "patch"):
            file_ones = [f for f in missing if _FILE_LIKE.search(f)]
            text_ones = [f for f in missing if f not in file_ones]
            if file_ones:
                add(f"A file is missing: {', '.join(file_ones)}.", "files=  (the field name, then the path of the file on your computer)",
                    _call_text(**{**base, "files": list(ctx.get("files") or []) + file_ones,
                                  "send": {**body, **{f: f"YOUR_{f.upper()}" for f in text_ones}} or None}),
                    "In the window, set that row of the form-data body to File and choose the file.")
            if text_ones:
                new = {**body, **{f: f"YOUR_{f.upper()}" for f in text_ones}}
                add(f"These fields are missing or not accepted: {', '.join(text_ones)}.", "the body. Use send=",
                    _call_text(**{**base, "send": new}), "Replace each YOUR_... with a real value.")
        elif fields and body and any(_FILE_LIKE.search(f) for f in fields if f in body) and ctx["method"] in ("post", "put", "patch"):
            fl = [f for f in fields if f in body and _FILE_LIKE.search(f)]
            rest = {k: v for k, v in body.items() if k not in fl}
            add(f"{', '.join(fl)} should be a file, but it was sent as plain text.", "files=  (the field name, then the path of the file)",
                _call_text(**{**base, "send": rest or None, "files": list(ctx.get("files") or []) + fl}),
                "In the window, set that row of the form-data body to File and choose the file.")
        elif fields and body:
            new = {**body, **{f: f"NEW_{f.upper()}" for f in fields if f in body}}
            add(f"The server did not accept the value(s) for: {', '.join(fields)}.", "the body. Use send=",
                _call_text(**{**base, "send": new}), "Replace each NEW_... with a value that is allowed.")
        elif ctx["method"] in ("post", "put", "patch") and not body:
            add("Nothing was sent, but this action usually needs data.", "the body. Use send=",
                _call_text(**{**base, "send": {"field1": "value1", "field2": "value2"}}),
                "Use the field names listed in the API's documentation.")
        else:
            add("The server did not accept the request.", "the address, send=, headers=, or params=", None,
                "Read the server's message above. It usually names what to change.")
        hdr = re.findall(r"\b([A-Za-z]+(?:-[A-Za-z]+)+)\b", " ".join(says)) if "header" in low else []
        if hdr and not any(h.lower() == "content-type" for h in hdr):
            add(f"The server asks for a header: {hdr[0]}.", "headers=", _call_text(**{**base, "headers": {**ctx["hdrs"], hdr[0]: "YOUR_VALUE"}}))
        if not ctx["auth"] and re.search(r"token|bearer|authoriz", low):
            add("The server mentions a login token.", "token=", _call_text(auth="token", **base))
        if not ctx["auth"] and re.search(r"api[-_ ]?key", low):
            add("The server mentions an API key.", "key=", _call_text(auth="key", **base))
    if says and st >= 400 and st != 401:
        out.insert(0, {"what": f'The server says: "{says[0][:150]}"', "where": None, "example": None, "note": None})
    return out


def _advise_connection(message, ctx, added):
    out = []
    if message.startswith("No value for"):
        out.append({"what": "A {{variable}} in the request has no value.", "where": "api.vars(...) before the call (or the Variables tab in the window)",
                    "example": 'api.vars(NAME="value")', "note": message})
    elif "SSL certificate" in message:
        out.append({"what": "The server's SSL certificate could not be verified.", "where": "api.verify(False)  (the window: Settings, SSL)",
                    "example": "api.verify(False)", "note": "Only do this for servers you trust, such as your company's internal test server. "
                                                           "Anyone on the network could read or change what you send to a server that is not trusted."})
    elif "timed out" in message:
        out.append({"what": "The address did not answer in time.", "where": "wait= (seconds to wait)",
                    "example": _call_text(ctx["url"], ctx["method"], ctx["body"], ctx["hdrs"], ctx["params"], extra=["wait=60"]),
                    "note": "If it never answers, the server may be down. Try again later."})
    else:
        note = "Check: 1) the spelling of the address, 2) your internet or VPN, 3) that the server is running, if it is on your own computer."
        if added:
            note += " For a server on your own computer, start the address with http:// instead of https://."
        local = re.match(r"^https?://(localhost|127\.|0\.0\.0\.0|\[::1\])", ctx["url"], re.I)
        ex_url = re.sub(r"^https://", "http://", ctx["url"]) if local else ctx["url"]
        out.append({"what": "Could not reach the address.", "where": "the address",
                    "example": _call_text(ex_url, ctx["method"], ctx["body"], ctx["hdrs"], ctx["params"]), "note": note})
    return out


def _print_advice(items):
    print("HOW TO FIX IT")
    for i, a in enumerate(items, 1):
        print(f"  {i}. {a['what']}")
        if a.get("where"):
            print(f"     Where:  {a['where']}")
        if a.get("example"):
            print(f"     Try:    {a['example']}")
        if a.get("note"):
            print(f"     Note:   {a['note']}")
    print()


# ---------------------------------------------------------------------------------------
# the response wrapper
# ---------------------------------------------------------------------------------------

class Result:
    """What every api call returns. Read it, check it, turn it into a table."""

    def __init__(self, raw, method, ms, request_info):
        self.raw = raw
        self.method = method
        self.url = raw.url
        self.status = raw.status_code
        self.reason = raw.reason or ""
        self.ok = raw.status_code < 400
        self.ms = ms
        self.headers = raw.headers
        self.text = raw.text
        self.size = len(raw.content or b"")
        self.request = request_info
        self.passed = None  # set by check()

    # -- reading ----------------------------------------------------------------------
    @property
    def json(self):
        """The body parsed as JSON, or None if it is not JSON."""
        try:
            return self.raw.json()
        except ValueError:
            return None

    def get(self, path, default=None):
        """Read a value by dotted path: r.get("data.0.name")."""
        value = _dig(self.json, path)
        return default if value is _MISSING else value

    def __getitem__(self, key):
        data = self.json
        if data is None:
            raise TypeError("This response body is not JSON")
        return data[key]

    def __repr__(self):
        return f"<Result {self.method} {self.status} {self.reason} {self.ms:.0f} ms>"

    # -- checking ---------------------------------------------------------------------
    def check(self, status=None, has=None, equals=None, contains=None, header=None,
              max_ms=None, schema=None, strict=False, quiet=False):
        """Check the response and print one PASS/FAIL line per check. Returns self, so calls chain.

        status    200, [200, 201], or "2xx"
        has       a key, or a list of keys (dotted paths like "user.id" work)
        equals    {"path": expected_value}
        contains  text that must appear in the body
        header    {"content-type": "json"}  (header must contain the text)
        max_ms    the response must arrive in under this many milliseconds
        schema    see Result.schema()
        strict    raise AssertionError if anything fails (for pytest)
        """
        lines = []

        def rec(ok, text):
            lines.append((bool(ok), text))

        if status is not None:
            rec(_status_matches(self.status, status), f"status is {self.status}" if _status_matches(self.status, status)
                else f"status is {self.status}, expected {status}")
        if has is not None:
            data = self.json
            for key in ([has] if isinstance(has, str) else has):
                found = data is not None and _dig(data, key) is not _MISSING
                rec(found, f"has '{key}'" if found else f"missing '{key}'")
        if equals is not None:
            data = self.json
            for key, want in equals.items():
                got = _MISSING if data is None else _dig(data, key)
                if got is _MISSING:
                    rec(False, f"'{key}' is missing, expected {want!r}")
                else:
                    rec(got == want, f"'{key}' is {got!r}" if got == want else f"'{key}' is {got!r}, expected {want!r}")
        if contains is not None:
            ok = contains in self.text
            rec(ok, f"body contains {contains!r}" if ok else f"body does not contain {contains!r}")
        if header is not None:
            for name, want in header.items():
                got = self.headers.get(name)
                ok = got is not None and (want is True or str(want).lower() in got.lower())
                rec(ok, f"header {name} is {got!r}" if ok else f"header {name} is {got!r}, expected {want!r}")
        if max_ms is not None:
            ok = self.ms <= max_ms
            rec(ok, f"responded in {self.ms:.0f} ms (limit {max_ms})" if ok
                else f"responded in {self.ms:.0f} ms, limit is {max_ms}")
        if schema is not None:
            problems = self.schema(schema, quiet=True)
            if problems:
                for p in problems:
                    rec(False, f"schema: {p}")
            else:
                rec(True, "matches schema")

        self.passed = all(ok for ok, _ in lines)
        if not quiet:
            for ok, text in lines:
                print(f"  [{'PASS' if ok else 'FAIL'}] {text}")
        if strict and not self.passed:
            failed = "; ".join(t for ok, t in lines if not ok)
            raise AssertionError(f"{self.method} {self.url}: {failed}")
        return self

    def schema(self, schema, quiet=False):
        """Compare the JSON body with a schema and return the list of problems (empty = valid).

        Schema language:
            {"id": int, "name": str}        required keys with types
            {"?nickname": str}              a leading ? makes a key optional
            {"tags": [str]}                 a list in which every item is a str
            {"owner": {"id": int}}          nested objects
            "any"                           any type;  None means null
        """
        data = self.json
        problems = ["response body is not JSON"] if data is None and self.text.strip() != "null" else _validate(data, schema)
        if not quiet:
            if problems:
                for p in problems:
                    print(f"  [FAIL] schema: {p}")
            else:
                print("  [PASS] matches schema")
        return problems

    # -- converting -------------------------------------------------------------------
    def df(self, path=None, quiet=False):
        """The JSON body as a pandas DataFrame, ready for sql(). Use path for a nested list."""
        data = self.json
        if data is None:
            raise ValueError("This response body is not JSON, so it cannot become a table")
        if path is not None:
            data = _dig(data, path)
            if data is _MISSING:
                raise ValueError(f"Path '{path}' was not found in the response")
        elif isinstance(data, dict):
            lists = [k for k, v in data.items() if isinstance(v, list) and v and all(isinstance(i, dict) for i in v)]
            if len(lists) == 1:
                data = data[lists[0]]
            elif len(lists) > 1:
                raise ValueError("The response holds several lists of records. Pass path=\"...\" to choose one. "
                                 f"Lists found at: {', '.join(lists)}.")
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise ValueError("The chosen part of the response is not a list of records")
        frame = pd.json_normalize(data)
        if not quiet:
            print(f"Fetched {len(frame)} rows, {len(frame.columns)} columns from '{self.url}'\n")
            print(frame.head())
        return frame

    def curl(self, mask=True):
        """The equivalent curl command. Secrets are hidden unless mask=False."""
        req = self.request
        parts = [f"curl -X {req['method'].upper()} '{req['url']}'"]
        noise = {"user-agent", "accept-encoding", "connection", "content-length"}
        if req.get("form"):
            noise.add("content-type")
        for k, v in req["headers"].items():
            if k.lower() in noise or (k.lower() == "accept" and v == "*/*"):
                continue
            if mask and _is_secret(k):
                v = "***"
            parts.append(f"-H '{k}: {v}'")
        for name, filename, text in req.get("form") or []:
            value = f"@{filename}" if filename else ("" if text is None else str(text))
            parts.append("-F '" + f"{name}={value}".replace("'", "'\\''") + "'")
        if req.get("body") is not None and not req.get("form"):
            body = req["body"]
            body = body if isinstance(body, str) else (f"<{len(body)} bytes>" if isinstance(body, bytes) else _json.dumps(body))
            parts.append("-d '" + body.replace("'", "'\\''") + "'")
        cmd = " \\\n  ".join(parts)
        print(cmd)
        return cmd


# ---------------------------------------------------------------------------------------
# the namespace object
# ---------------------------------------------------------------------------------------

class _API:
    """Test an API from Python.

    Every HTTP method is a method: api.get, api.post, api.put, api.patch, api.delete, api.head, api.options.
    Each call prints a one-line summary and returns a Result you can check.

        api.base("https://api.example.com")       # optional: then use short paths
        api.auth("my-token")                       # optional: sent as a Bearer token on every call
        r = api.post("/users", json={"name": "Asha"})
        r.check(status=201, has="id")
    """

    def __init__(self):
        self._base = None
        self._headers = {}
        self._auth = None
        self._key = None
        self._timeout = 30
        self._session = requests.Session()
        self._vars = {}
        self._verify = True
        self._proxy = None
        self._redirects = True
        self._last = None

    # -- defaults ---------------------------------------------------------------------
    def base(self, url=_MISSING):
        """Set the base address, so api.get("/users") works. api.base() returns the current one."""
        if url is _MISSING:
            return self._base
        self._base = url.rstrip("/") if url else None
        return self._base

    def headers(self, **headers):
        """Set headers sent on every call: api.headers(Accept="application/json"). No arguments returns them."""
        self._headers.update({k.replace("_", "-"): v for k, v in headers.items()})
        return dict(self._headers)

    def auth(self, credentials=_MISSING):
        """Set default auth. A string is a Bearer token; a (user, password) tuple is Basic auth."""
        if credentials is _MISSING:
            return self._auth
        self._auth = credentials
        return None

    def key(self, value, header="X-API-Key"):
        """Send an API key header on every call."""
        self._key = (header, value)

    def timeout(self, seconds):
        """Seconds to wait for each response before giving up (default 30)."""
        self._timeout = seconds

    def vars(self, _values=None, **values):
        """Name values once, use them anywhere as {{name}}: api.vars(HOST="https://api.example.com", TOKEN="abc").

        With no arguments it returns the current variables. api.vars(clear=True) is not special: use api.reset().
        """
        if _values:
            self._vars.update(_values)
        self._vars.update(values)
        return dict(self._vars)

    def verify(self, flag=_MISSING):
        """Check the server's SSL certificate (default True). api.verify(False) skips the check, for servers you trust
        such as an internal test server. With no argument it returns the current setting."""
        if flag is _MISSING:
            return self._verify
        self._verify = bool(flag)

    def proxy(self, url=_MISSING):
        """Send every call through a proxy: api.proxy("http://proxy.company.com:8080"). api.proxy(None) turns it off."""
        if url is _MISSING:
            return self._proxy
        self._proxy = url or None

    def redirects(self, flag=_MISSING):
        """Follow redirects (default True). api.redirects(False) shows the redirect itself instead of following it."""
        if flag is _MISSING:
            return self._redirects
        self._redirects = bool(flag)

    def cookies(self, clear=False):
        """The cookies the API has set so far, as a dict. They are sent back automatically on later calls. clear=True forgets them."""
        if clear:
            self._session.cookies.clear()
        return requests.utils.dict_from_cookiejar(self._session.cookies)

    def reset(self):
        """Forget the base address, headers, auth, key, cookies, and last result."""
        self.__init__()

    @property
    def last(self):
        """The most recent Result."""
        return self._last

    # -- sending ----------------------------------------------------------------------
    def _resolve_url(self, url):
        if re.match(r"^https?://", url, re.I):
            return url
        if not self._base:
            raise ValueError(
                f"'{url}' is not a full address, and no base is set. "
                "Pass a full URL, or call api.base(\"https://...\") first."
            )
        return f"{self._base}/{url.lstrip('/')}"

    def _send(self, method, url, params=None, json=None, data=None, headers=None, auth=None, key=None,
              timeout=None, retries=0, redirects=None, use_session=True, files=None):
        method = method.upper()
        url = self._resolve_url(_fill_vars(url, self._vars))
        hdrs = {**self._headers, **(headers or {})}
        auth = auth if auth is not None else self._auth
        key = key if key is not None else self._key
        hdrs, params, json, data, auth, key = _fill_vars((hdrs, params, json, data, auth, key), self._vars)
        parts = _load_files(_fill_vars(files, self._vars)) if files else None
        req_auth = None
        if isinstance(auth, str):
            hdrs.setdefault("Authorization", f"Bearer {auth}")
        elif isinstance(auth, (tuple, list)) and len(auth) == 2:
            req_auth = tuple(auth)
        elif auth is not None:
            raise ValueError("auth must be a token string, or a (user, password) tuple")
        if key is not None:
            name, value = key if isinstance(key, tuple) else ("X-API-Key", key)
            hdrs.setdefault(name, value)

        sender = self._session if use_session else requests
        follow = self._redirects if redirects is None else redirects
        proxies = {"http": self._proxy, "https": self._proxy} if self._proxy else None
        attempt = 0
        while True:
            start = time.perf_counter()
            try:
                with warnings.catch_warnings():
                    if not self._verify:
                        warnings.simplefilter("ignore")      # the person chose to skip the certificate check
                    raw = sender.request(method, url, params=params, json=json, data=data, headers=hdrs, files=parts,
                                         auth=req_auth, timeout=timeout or self._timeout, allow_redirects=follow,
                                         verify=self._verify, proxies=proxies)
            except requests.exceptions.Timeout:
                if attempt < retries:
                    time.sleep(0.25 * 2 ** attempt); attempt += 1; continue
                raise APIError(f"{method} {url} timed out after {timeout or self._timeout} s. "
                               "Raise it with timeout=... or api.timeout(...).") from None
            except requests.exceptions.SSLError:
                raise APIError(f"{method} {url} has an SSL certificate that could not be verified. "
                               "For a server you trust, such as an internal test server, you can skip the check with api.verify(False).") from None
            except requests.exceptions.ConnectionError as e:
                if attempt < retries:
                    time.sleep(0.25 * 2 ** attempt); attempt += 1; continue
                raise APIError(f"{method} {url} could not connect. Check the address and your network. ({type(e).__name__})") from None
            except requests.exceptions.InvalidURL as e:
                raise APIError(f"'{url}' is not a valid address: {e}") from None
            ms = (time.perf_counter() - start) * 1000
            if raw.status_code in (502, 503, 504) and attempt < retries:
                time.sleep(0.25 * 2 ** attempt); attempt += 1; continue
            break

        sent = raw.request
        body = json if json is not None else data
        info = {"method": method, "url": sent.url, "headers": dict(sent.headers), "body": body}
        if parts:
            info["form"] = [(n, v[0], None if v[0] else v[1]) for n, v in parts]
        result = Result(raw, method, ms, info)
        self._last = result
        return result

    def request(self, method, url, quiet=False, **opts):
        """Send any method by name: api.request("GET", "/users")."""
        m = method.lower()
        if m not in _METHODS:
            raise ValueError(f"Unknown method '{method}'. Use one of: {', '.join(x.upper() for x in _METHODS)}")
        result = self._send(m, url, **opts)
        if not quiet:
            self._print(result)
        return result

    def _print(self, r, preview_lines=14):
        print(f"{r.method} {r.url} -> {r.status} {r.reason}  ({r.ms:.0f} ms, {_human_size(r.size)})")
        if r.method == "HEAD" or not r.text.strip():
            return
        data = r.json
        text = _json.dumps(data, indent=2, ensure_ascii=False) if data is not None else r.text.strip()
        lines = text.splitlines()
        shown = lines[:preview_lines]
        for ln in shown:
            print("  " + (ln if len(ln) <= 110 else ln[:107] + "..."))
        if len(lines) > preview_lines:
            print(f"  ... ({len(lines) - preview_lines} more lines)")

    def get(self, url, **opts):
        """GET: read something."""
        return self.request("get", url, **opts)

    def post(self, url, **opts):
        """POST: create something. Pass json={...} for a JSON body or data={...} for a form."""
        return self.request("post", url, **opts)

    def put(self, url, **opts):
        """PUT: replace something."""
        return self.request("put", url, **opts)

    def patch(self, url, **opts):
        """PATCH: change part of something."""
        return self.request("patch", url, **opts)

    def delete(self, url, **opts):
        """DELETE: remove something."""
        return self.request("delete", url, **opts)

    def head(self, url, **opts):
        """HEAD: like GET, but only the headers come back."""
        return self.request("head", url, **opts)

    def options(self, url, **opts):
        """OPTIONS: ask which methods the address allows."""
        return self.request("options", url, **opts)

    def __call__(self, url, **opts):
        """api(url) is a shortcut for api.get(url)."""
        return self.get(url, **opts)


    # -- the simple way ---------------------------------------------------------------
    def test(self, url=None, method="get", send=None, headers=None, token=None, user=None, password=None, key=None,
             params=None, expect=None, look_for=None, times=1, form=False, wait=None, files=None, gui=False):
        """Test an API in plain English. Give it a web address and it tells you if it works.

            api.test("https://example.com/users/1")

        Everything except the address is optional:
            method    "get" (default), "post", "put", "patch" or "delete"
            send      what to send, typed simply:  "name=Asha, age=30"   (or a dict)
            headers   extra settings the API asks for:  "Accept: application/json; X-Team: blue"
            token     your access token, if the API needs a login
            user, password   a username and password, if the API asks for them
            key       an API key, if the API asks for one
            params    things to add to the address after a ?:  "page=2, limit=10"
            expect    the status number you expect, such as 200 or 201
            look_for  a field you expect in the answer, or a list of them
            times     ask this many times to measure speed
            form      True to send as a web form instead of JSON
            wait      seconds to wait for an answer (default 30)
            files     files to upload:  "file=report.pdf"   (the address, send= and files= go out as multipart/form-data)
            gui       True to open a Postman-like window in your browser, filled in with what you passed

        Anything can contain {{name}}; give it a value once with api.vars(name="...").

        If anything fails, it tells you what to pass, where it goes, and shows a corrected call to copy.
        Call api.test() with nothing at all and it will ask you each question.
        """
        if gui:
            return self.gui(url=url, method=method, send=send, headers=headers, token=token, user=user, password=password,
                            key=key, params=params, expect=expect, look_for=look_for, times=times, form=form, wait=wait)
        interactive = url is None
        if interactive:
            url, method, params, send, headers, token, user, password, expect, look_for, times = self._ask_questions()

        url = str(url).strip().strip("\"'")
        parts = url.split(None, 1)
        if len(parts) == 2 and parts[0].lower() in _METHODS:
            method, url = parts[0], parts[1].strip()
        method = str(method).strip().lower()
        if method not in _METHODS:
            print(f"'{method}' is not a known action. Use one of: {', '.join(_METHODS)}.")
            return None
        added = False
        filled = _fill_vars(url, self._vars, strict=False)
        if not re.match(r"^https?://", filled, re.I) and not self._base and not filled.startswith("{{"):
            url, added = "https://" + url, True
            filled = "https://" + filled

        try:
            body = _parse_send(send)
            qparams = _parse_send(params)
            hdrs = _parse_headers(headers)
            parts = _load_files(files)
        except ValueError as e:
            print(f"\n{e}")
            return None
        raw_body = isinstance(body, bytes)
        opts = {}
        if body is not None:
            opts["data" if (form or parts or raw_body) else "json"] = body
        if parts:
            opts["files"] = parts
        if hdrs:
            opts["headers"] = hdrs
        if qparams:
            opts["params"] = qparams
        if wait:
            opts["timeout"] = wait
        auth_kind = None
        if token:
            opts["auth"], auth_kind = token, "token"
        elif user is not None:
            opts["auth"], auth_kind = (user, password or ""), "basic"
        if key:
            opts["key"], auth_kind = key, auth_kind or "key"
        if not auth_kind and (self._auth or self._key):
            auth_kind = "token" if isinstance(self._auth, str) else ("basic" if self._auth else "key")

        full = url if "{{" in url else self._resolve_url(url)
        try:
            shown = self._resolve_url(filled)
        except ValueError:             # an address that begins with a variable that has no value yet
            shown = filled
        if raw_body:
            body = None
        sent_fields = body if isinstance(body, dict) else None
        file_fields = [n for n, (fn, *_r) in parts if fn]
        if parts:                      # text parts of a multipart form count as the body, for the advice
            text_parts = {n: t for n, (fn, t, *_r) in parts if not fn}
            body = {**(body if isinstance(body, dict) else {}), **text_parts} or None
        ctx = dict(url=full, method=method, body=body, hdrs=hdrs, params=qparams, form=form, auth=auth_kind,
                   expect=expect, look_for=look_for, files=file_fields)
        print(f"\nTesting:  {method.upper()} {shown}" + ("   (added https:// for you)" if added else ""))
        if not self._verify:
            print("Note:  SSL certificate checking is OFF for this call.")
        if qparams:
            print("Address extras:  " + ", ".join(f"{k}={_fmt_value(v)}" for k, v in qparams.items()))
        if parts:
            print("Form parts:  " + ", ".join(
                f"{n} (file: {fn}, {_human_size(len(c))})" if fn else f"{n} (text)" for n, (fn, c, *_m) in parts) + "   (as multipart/form-data)")
        elif raw_body:
            print(f"Sending:  {_human_size(len(opts['data']))} of text")
        if body is not None and not parts:
            print(f"Sending:  {_json.dumps(body, ensure_ascii=False)}" + ("   (as a web form)" if form else ""))
        if parts and sent_fields:
            print(f"Form fields:  {', '.join(map(str, sent_fields))}")
        if hdrs:
            print("Headers:  " + ", ".join(f"{k}: {'***' if _is_secret(k) else v}" for k, v in hdrs.items()))
        print()

        problems, advice = 0, []
        base_kw = dict(url=full, method=method, send=body, headers=hdrs, params=qparams, form=form, files=file_fields or None)

        def line(ok, text):
            nonlocal problems
            if not ok:
                problems += 1
            print(f"  [{'OK  ' if ok else 'FAIL'}] {text}")

        try:
            r = self._send(method, url, **opts)
        except APIError as e:
            line(False, str(e))
            print()
            _print_advice(_advise_connection(str(e), ctx, added))
            print("RESULT: PROBLEM. There was no answer from the address.")
            return None

        # 1. did it answer the way you wanted?
        if expect is not None:
            ok = _status_matches(r.status, expect)
            line(ok, f"Status {r.status}. " + _status_help(r.status) if ok
                 else f"You expected status {expect} but got {r.status}. " + _status_help(r.status))
            if not ok and r.status < 400:
                advice.append({"what": f"You expected {expect} but got {r.status}.", "where": "expect=",
                               "example": _call_text(**base_kw, auth=auth_kind, expect=r.status),
                               "note": f"Use expect={r.status} if that is the answer you want. Otherwise check the address and what you send."})
        else:
            line(r.status < 400, f"Status {r.status}. " + _status_help(r.status))
        if r.status >= 400 or (expect is not None and not _status_matches(r.status, expect) and r.status >= 300):
            advice += _advise_response(r, ctx)

        # 2. how fast?
        line(r.ms < 3000, f"Speed: {r.ms:.0f} ms ({_speed_word(r.ms)})")
        if r.ms >= 3000:
            advice.append({"what": "The answer took more than 3 seconds.", "where": "wait= (to allow more time)",
                           "example": _call_text(**base_kw, auth=auth_kind, extra=["wait=60"]),
                           "note": "If it is always slow, the server may be overloaded. Try again later."})

        # 3. what came back?
        data = r.json
        if method == "head":
            pass
        elif data is None and r.text.strip():
            snippet = r.text.strip().replace("\n", " ")
            print(f"  [INFO] It sent back text: {snippet[:80]}{'...' if len(snippet) > 80 else ''}")
        elif isinstance(data, dict):
            keys = list(data.keys())
            shown = ", ".join(keys[:8]) + (f", and {len(keys) - 8} more" if len(keys) > 8 else "")
            print(f"  [INFO] It sent back data with {len(keys)} field(s): {shown}")
        elif isinstance(data, list):
            first = data[0] if data else None
            extra = f", each with: {', '.join(list(first)[:8])}" if isinstance(first, dict) else ""
            print(f"  [INFO] It sent back a list of {len(data)} item(s){extra}")
        elif data is None:
            print("  [INFO] It sent back nothing.")

        # 4. did it contain what you wanted?
        if look_for:
            wanted = [look_for] if isinstance(look_for, str) else list(look_for)
            missing = [w for w in wanted if data is None or _dig(data, w) is _MISSING]
            if missing:
                line(False, f"Could not find: {', '.join(missing)}")
                have = list(data.keys()) if isinstance(data, dict) else (list(data[0].keys()) if isinstance(data, list) and data and isinstance(data[0], dict) else [])
                if have:
                    advice.append({"what": f"The answer does not contain: {', '.join(missing)}.", "where": "look_for=",
                                   "example": _call_text(**base_kw, auth=auth_kind, look_for=have[0]),
                                   "note": f"The answer has these fields: {', '.join(have[:10])}. Use one of those names."})
                else:
                    advice.append({"what": f"The answer does not contain: {', '.join(missing)}.", "where": "look_for=", "example": None,
                                   "note": "The answer was empty or not data (JSON), so there are no field names to look for."})
            else:
                line(True, f"Found everything you looked for: {', '.join(wanted)}")

        # 5. speed test
        if times and times > 1:
            try:
                st = self.bench(url, n=times, method=method, quiet=True, **opts)
                ok = st["errors"] == 0
                line(ok, f"Asked {times} times: average {st['avg']:.0f} ms, slowest {st['max']:.0f} ms, "
                         f"{st['errors']} failure(s)")
                if not ok:
                    advice.append({"what": "Some of the repeated requests failed.", "where": "times=",
                                   "example": _call_text(**base_kw, auth=auth_kind, extra=["times=5"]),
                                   "note": "Many APIs limit how fast you can ask. Try fewer repeats."})
            except APIError as e:
                line(False, str(e))

        print()
        if advice:
            _print_advice(advice)
        if problems:
            print(f"RESULT: PROBLEM ({problems} issue{'s' if problems != 1 else ''}). See the FAIL line{'s' if problems != 1 else ''} above and HOW TO FIX IT.")
        else:
            print("RESULT: WORKING")
        return r

    def gui(self, url=None, method="get", send=None, headers=None, token=None, user=None, password=None, key=None,
            params=None, expect=None, look_for=None, times=1, form=False, wait=None, port=0, open_browser=True, block=None,
            folder=None):
        """Open a Postman-like window in your browser to build a request, send it, and see the answer.

            api.gui()                                  # an empty window
            api.test("https://example.com/users", gui=True)   # filled in with what you pass

        It runs only on your computer (127.0.0.1) and sends each request through api.test(), so you get the
        same plain-English report and HOW TO FIX IT advice. Variables from api.vars() are filled in.
        Saved requests ("collections"), environments (UAT, SIT, Prod ...) and history live in the folder
        ~/fyrefly_api (choose another with folder="...", or folder=False to save nothing). Tokens and passwords
        are never written into the shared files.
        Pass open_browser=False to only print the address. In a notebook it returns at once; in a script it
        waits until you click Quit (or press Ctrl+C).
        """
        from . import _apigui
        preset = _apigui.make_preset(url=url, method=method, send=send, headers=headers, token=token, user=user,
                                     password=password, key=key, params=params, expect=expect, look_for=look_for,
                                     times=times, form=form, wait=wait, variables=self._vars)
        return _apigui.serve(self, preset, port=port, open_browser=open_browser, block=block, folder=folder)

    def from_curl(self, text):
        """Turn a curl command (copied from API docs or a browser) into the Fyrefly call that does the same.

            api.from_curl("curl -X POST https://api.example.com/users -H 'Content-Type: application/json' -d '{\"name\": \"Asha\"}'")

        Prints the api.test(...) line, and returns it as text. Tokens become placeholders such as YOUR_TOKEN.
        """
        from . import _apigui, _apistore
        parsed = _apistore.parse_curl(text)
        req = parsed["req"]
        for r in req["body"].get("rows") or []:
            if r.get("kind") == "file" and not r.get("file"):
                r["file"] = {"name": "YOUR_FILE", "b64": ""}
        _, code, _ = _apigui.build_call(req, {})
        if req.get("verify") is False:
            code = "api.verify(False)\n" + code
        for note in parsed["notes"]:
            print("Note: " + note)
        print(code)
        return code

    def import_postman(self, path, folder=None):
        """Import a Postman collection or environment export (a .json file) into your Fyrefly folder (default ~/fyrefly_api).

        Open it afterwards with api.gui(). Tokens and passwords typed straight into a request are not saved to the files.
        """
        from . import _apistore
        with open(os.path.expanduser(path), "r", encoding="utf-8") as fh:
            text = fh.read()
        ws = _apistore.Workspace(folder or _apistore.default_folder())
        result = ws.import_text(text)
        if result["kind"] == "collection":
            print(f"Imported collection '{result['collection']}': {result['requests']} request(s)"
                  + (f", and its variables as the environment '{result['environment']}'" if result.get("environment") else "") + ".")
        else:
            print(f"Imported environment '{result.get('environment')}': {result.get('variables')} variable(s).")
        for note in result.get("notes", []):
            if note:
                print("Note: " + note)
        print(f"Saved in {ws.folder}. Open it with api.gui().")
        return result

    @staticmethod
    def _ask_questions():
        """Ask a person the questions, one at a time, in plain words."""
        import getpass
        print("Let's test an API. Press Enter to skip any question that has (optional).\n")
        url = ""
        while not url.strip():
            url = input("1. Paste the web address to test: ")
        method = input("2. What do you want to do? get / post / put / patch / delete  (Enter = get): ").strip() or "get"
        params = input("3. Anything to add to the address after a ?  Type like  page=2, limit=10  (optional): ").strip() or None
        send = None
        if method.strip().lower() in ("post", "put", "patch"):
            send = input("4. What do you want to send? Type like  name=Asha, age=30  (optional): ").strip() or None
        headers = input("5. Extra headers the API asks for? Type like  Accept: application/json  (optional): ").strip() or None
        token = getpass.getpass("6. Access token, if the API needs a login (typing is hidden) (optional): ").strip() or None
        user = password = None
        if not token:
            user = input("7. Username (optional): ").strip() or None
            if user:
                password = getpass.getpass("   Password (typing is hidden): ")
        look = input("8. A field you expect in the answer, such as name (optional): ").strip() or None
        expect = input("9. The status number you expect, such as 200 (optional): ").strip()
        expect = int(expect) if expect.isdigit() else None
        times = input("10. How many times to test the speed? (Enter = once): ").strip()
        times = int(times) if times.isdigit() else 1
        return url, method, params, send, headers, token, user, password, expect, look, times

    # -- tables -----------------------------------------------------------------------
    def df(self, url, path=None, **opts):
        """GET an address and return its JSON records as a DataFrame, ready for sql()."""
        r = self._send("get", url, **opts)
        if not r.ok:
            raise APIError(f"GET {r.url} returned {r.status} {r.reason}, so there is no table to build")
        return r.df(path=path)

    # -- measuring --------------------------------------------------------------------
    def bench(self, url, n=20, method="get", workers=1, quiet=False, **opts):
        """Send the same request n times and report how fast it is.

        workers>1 sends requests in parallel to see how the API behaves under load.
        Returns a dict: n, errors, min, avg, median, p95, max (milliseconds), and rps.
        """
        if n < 1:
            raise ValueError("n must be at least 1")
        method = method.lower()
        if method not in _METHODS:
            raise ValueError(f"Unknown method '{method}'")
        shared = workers <= 1

        def one(_):
            try:
                r = self._send(method, url, use_session=shared, **opts)
                return r.ms, (r.status >= 400)
            except APIError:
                return None, True

        start = time.perf_counter()
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                outcomes = list(pool.map(one, range(n)))
        else:
            outcomes = [one(i) for i in range(n)]
        wall = time.perf_counter() - start

        times = sorted(ms for ms, _ in outcomes if ms is not None)
        errors = sum(1 for _, bad in outcomes if bad)
        if not times:
            raise APIError(f"All {n} requests to {url} failed to connect.")
        p95 = times[min(len(times) - 1, int(round(0.95 * (len(times) - 1))))]
        stats = {"n": n, "errors": errors, "min": times[0], "avg": statistics.mean(times),
                 "median": statistics.median(times), "p95": p95, "max": times[-1], "rps": n / wall if wall else float("inf")}
        if not quiet:
            print(f"{method.upper()} {self._resolve_url(url)}  x{n}" + (f"  ({workers} at a time)" if workers > 1 else ""))
            print(f"  min {stats['min']:.0f} ms   avg {stats['avg']:.0f} ms   median {stats['median']:.0f} ms   "
                  f"p95 {stats['p95']:.0f} ms   max {stats['max']:.0f} ms")
            print(f"  {stats['rps']:.1f} requests/second, {errors} error(s) out of {n}")
        return stats

    # -- test suites ------------------------------------------------------------------
    def run(self, tests, strict=False):
        """Run a list of API tests (or a JSON file of them) and print a pass/fail report.

        Each test is a dict:
            {"name": "create user", "method": "post", "url": "/users", "json": {"name": "Asha"},
             "expect": {"status": 201, "has": "id"}, "save": {"uid": "id"}}

        "save" stores values from the JSON response; later tests can use them as {uid}.
        Returns {"passed": n, "failed": n, "results": [...]}.
        """
        if isinstance(tests, str):
            with open(tests, encoding="utf-8") as f:
                tests = _json.load(f)
        if not isinstance(tests, list):
            raise ValueError("tests must be a list of dicts, or the path to a JSON file holding one")
        variables, results = {}, []
        for i, spec in enumerate(tests, 1):
            spec = _substitute(dict(spec), variables)
            name = spec.pop("name", f"test {i}")
            method = spec.pop("method", "get")
            url = spec.pop("url", None)
            if url is None:
                raise ValueError(f"Test '{name}' has no 'url'")
            expect = dict(spec.pop("expect", {}))
            save = spec.pop("save", {})
            try:
                r = self._send(method, url, **spec)
                r.check(quiet=True, **expect)
                ok = r.passed is not False
                note = ""
                for var, path in save.items():
                    value = r.get(path, _MISSING)
                    if value is _MISSING:
                        ok, note = False, f"could not save '{var}': '{path}' not in response"
                    else:
                        variables[var] = value
                if not ok and not note:
                    note = self._why(r, expect)
                results.append({"name": name, "passed": ok, "ms": r.ms, "status": r.status, "note": note})
                tag = "PASS" if ok else "FAIL"
                print(f"[{tag}] {name}  ({r.method} {r.status}, {r.ms:.0f} ms)" + (f"\n       {note}" if note else ""))
            except APIError as e:
                results.append({"name": name, "passed": False, "ms": None, "status": None, "note": str(e)})
                print(f"[FAIL] {name}\n       {e}")
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed
        print(f"\n{passed} passed, {failed} failed, {len(results)} total")
        if strict and failed:
            raise AssertionError(f"{failed} API test(s) failed: " + ", ".join(r["name"] for r in results if not r["passed"]))
        return {"passed": passed, "failed": failed, "results": results}

    @staticmethod
    def _why(r, expect):
        """Run the checks silently and return the first failure's text."""
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r.check(**expect)
        fails = [ln.strip()[7:] for ln in buf.getvalue().splitlines() if ln.strip().startswith("[FAIL]")]
        return "; ".join(fails)


_engine = _API()                    # the engine behind the window; private


class _ApiNamespace:
    """Fyrefly API testing. The one public function is gui()."""

    __slots__ = ()
    gui = staticmethod(_engine.gui)

    def __getattr__(self, name):
        raise AttributeError(f"fyrefly.api has only one function: api.gui(). There is no api.{name}. Run api.gui() to open the window.")

    def __dir__(self):
        return ["gui"]

    def __repr__(self):
        return "<fyrefly.api: use api.gui()>"


api = _ApiNamespace()