"""Saved requests, environments, history, and import/export for the Fyrefly API window.

Everything lives in one plain folder (default ~/fyrefly_api):

    collections/<name>.json     saved requests. Safe to share or commit: tokens and passwords are never written here.
    environments/<name>.json    named sets of variables (UAT, SIT, Prod ...). Values marked secret are blank in this file.
    secrets.json                the real values of secret variables. Created with owner-only permission, listed in .gitignore.
    history.json                the last 100 requests sent (secrets removed). Listed in .gitignore.
    settings.json               SSL / redirects / proxy / timeout / the environment that was active.

Nothing here talks to the network. It is plain Python so it can be tested without a browser.
"""
import copy
import json
import os
import re
import shlex
import threading
import time
import uuid
from urllib.parse import parse_qsl, unquote_plus, urlsplit

from .api import _is_secret

GLOBALS = "Globals"
MAX_HISTORY = 100
DEFAULT_SETTINGS = {"verify": True, "redirects": True, "proxy": "", "timeout": "", "active_env": GLOBALS}
_REF = re.compile(r"^\s*\{\{[^{}]+\}\}\s*$")


def new_id():
    return uuid.uuid4().hex[:10]


def slug(name):
    s = re.sub(r"[^A-Za-z0-9._ \-]+", "_", str(name)).strip(" ._")[:60]
    return s or "untitled"


def blank_request(**kw):
    """A request in the shape the window uses."""
    req = {"method": "get", "url": "", "params": [], "headers": [], "auth": {"type": "none"},
           "body": {"type": "none"}, "expect": "", "look_for": "", "times": 1, "timeout": "", "saves": [],
           "verify": None, "redirects": None}
    req.update(kw)
    return req


def _row(k, v="", on=True, **extra):
    return {"on": bool(on), "k": str(k), "v": "" if v is None else str(v), **extra}


def _is_ref(text):
    return not text or bool(_REF.match(str(text)))


def strip_secrets(req):
    """A copy of a request that is safe to write to disk, and how many secret values were left out."""
    clean, n = copy.deepcopy(req), 0
    clean.pop("variables", None)
    for group in ("params", "headers"):                       # drop the empty row the window keeps at the bottom
        clean[group] = [r for r in clean.get(group) or [] if str(r.get("k", "")).strip()]
    if isinstance(clean.get("body"), dict) and "rows" in clean["body"]:
        clean["body"]["rows"] = [r for r in clean["body"]["rows"] if str(r.get("k", "")).strip()]
    clean["saves"] = [r for r in clean.get("saves") or [] if str(r.get("var", "")).strip() and str(r.get("path", "")).strip()]
    auth = clean.get("auth") or {}
    for key in ("token", "password", "value"):
        if auth.get(key) and not _is_ref(auth[key]):
            auth[key], n = "", n + 1
    for group in ("headers", "params"):
        for r in clean.get(group) or []:
            if _is_secret(r.get("k", "")) and r.get("v") and not _is_ref(r["v"]):
                r["v"], n = "", n + 1
    body = clean.get("body") or {}
    for r in body.get("rows") or []:
        if r.get("kind") == "file":
            r["file"] = None            # file contents are never stored; choose the file again
        elif _is_secret(r.get("k", "")) and r.get("v") and not _is_ref(r["v"]):
            r["v"], n = "", n + 1
    return clean, n


def _atomic_write(path, text, private=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 if private else 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
    if private:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def default_folder():
    return os.environ.get("FYREFLY_API_HOME") or os.path.join(os.path.expanduser("~"), "fyrefly_api")


class Workspace:
    """Collections, environments, history and settings. folder=None keeps everything in memory only."""

    def __init__(self, folder=None):
        self.folder = os.path.abspath(os.path.expanduser(folder)) if folder else None
        self.lock = threading.RLock()
        self.envs = {GLOBALS: []}
        self.collections = {}
        self.history = []
        self.settings = dict(DEFAULT_SETTINGS)
        self.problems = []
        if self.folder:
            self._load()

    # ---- disk -----------------------------------------------------------------------------
    def _path(self, *parts):
        return os.path.join(self.folder, *parts)

    def _read(self, path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as e:
            self.problems.append(f"Could not read {os.path.basename(path)} ({e}). It was left untouched.")
            return None

    def _load(self):
        secrets = self._read(self._path("secrets.json")) or {}
        for fn in sorted(os.listdir(self._path("environments"))) if os.path.isdir(self._path("environments")) else []:
            d = self._read(self._path("environments", fn))
            if isinstance(d, dict) and d.get("name"):
                rows = []
                for r in d.get("variables", []):
                    row = _row(r.get("k", ""), r.get("v", ""), r.get("on", True), secret=bool(r.get("secret")))
                    if row["secret"]:
                        row["v"] = str((secrets.get(d["name"]) or {}).get(row["k"], ""))
                    rows.append(row)
                self.envs[d["name"]] = rows
        self.envs.setdefault(GLOBALS, [])
        for fn in sorted(os.listdir(self._path("collections"))) if os.path.isdir(self._path("collections")) else []:
            d = self._read(self._path("collections", fn))
            if isinstance(d, dict) and d.get("name"):
                d.setdefault("requests", [])
                self.collections[d["name"]] = d
        h = self._read(self._path("history.json"))
        self.history = h if isinstance(h, list) else []
        s = self._read(self._path("settings.json"))
        if isinstance(s, dict):
            self.settings.update({k: s[k] for k in DEFAULT_SETTINGS if k in s})

    def _ensure_folder(self):
        if not self.folder:
            return False
        os.makedirs(self.folder, exist_ok=True)
        gi = self._path(".gitignore")
        if not os.path.exists(gi):
            _atomic_write(gi, "secrets.json\nhistory.json\n*.tmp\n")
        return True

    def _fname(self, kind, name):
        """File name for a collection/environment, kept stable and unique."""
        base = slug(name)
        fn, i = f"{base}.json", 2
        while True:
            d = self._read_quiet(self._path(kind, fn))
            if d is None or d.get("name") == name:
                return fn
            fn, i = f"{base}-{i}.json", i + 1

    def _read_quiet(self, path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                d = json.load(fh)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return None

    def _flush_env(self, name):
        if not self._ensure_folder():
            return
        rows = self.envs[name]
        public = [{"k": r["k"], "v": "" if r.get("secret") else r["v"], "secret": bool(r.get("secret")), "on": r.get("on", True)} for r in rows]
        _atomic_write(self._path("environments", self._fname("environments", name)),
                      json.dumps({"name": name, "variables": public}, indent=2, ensure_ascii=False))
        secrets = self._read(self._path("secrets.json")) or {}
        mine = {r["k"]: r["v"] for r in rows if r.get("secret") and r["v"] != ""}
        if mine:
            secrets[name] = mine
        else:
            secrets.pop(name, None)
        if secrets or os.path.exists(self._path("secrets.json")):
            _atomic_write(self._path("secrets.json"), json.dumps(secrets, indent=2, ensure_ascii=False), private=True)

    def _flush_collection(self, name):
        if self._ensure_folder():
            _atomic_write(self._path("collections", self._fname("collections", name)),
                          json.dumps(self.collections[name], indent=2, ensure_ascii=False))

    def _remove(self, kind, name):
        if self.folder:
            try:
                os.remove(self._path(kind, self._fname(kind, name)))
            except OSError:
                pass

    def _flush_settings(self):
        if self._ensure_folder():
            _atomic_write(self._path("settings.json"), json.dumps(self.settings, indent=2))

    def _flush_history(self):
        if self._ensure_folder():
            _atomic_write(self._path("history.json"), json.dumps(self.history, indent=1, ensure_ascii=False))

    # ---- what the page sees -----------------------------------------------------------------
    def state(self):
        with self.lock:
            envs = {n: [{"on": r.get("on", True), "k": r["k"], "secret": bool(r.get("secret")),
                         "v": "" if r.get("secret") else r["v"], "has": bool(r["v"]) if r.get("secret") else False,
                         "keep": bool(r.get("secret")) and bool(r["v"])} for r in rows]
                    for n, rows in self.envs.items()}
            return {"folder": self.folder, "persist": bool(self.folder), "settings": dict(self.settings), "envs": envs,
                    "collections": [self.collections[n] for n in sorted(self.collections, key=str.lower)],
                    "history": list(self.history), "problems": list(self.problems), "globals": GLOBALS}

    # ---- environments -----------------------------------------------------------------------
    def resolved(self, env=None):
        """Variable name -> value, for every switched-on variable: Globals first, then the active environment on top."""
        out = {}
        with self.lock:
            for name in (GLOBALS, env if env and env != GLOBALS else None):
                for r in self.envs.get(name, []) if name else []:
                    if r.get("on", True) and r["k"].strip():
                        out[r["k"].strip()] = r["v"]
        return out

    def save_env(self, name, rows):
        name = str(name).strip()
        if not name:
            raise ValueError("Give the environment a name.")
        with self.lock:
            old = {r["k"]: r for r in self.envs.get(name, [])}
            new, seen = [], set()
            for r in rows or []:
                k = str(r.get("k", "")).strip()
                if not k or k in seen:
                    continue
                seen.add(k)
                secret = bool(r.get("secret")) or _is_secret(k) and r.get("secret") is None
                v = str(r.get("v", ""))
                if secret and r.get("keep") and k in old:
                    v = old[k]["v"]
                new.append(_row(k, v, r.get("on", True), secret=secret))
            self.envs[name] = new
            self._flush_env(name)

    def new_env(self, name):
        name = str(name).strip()
        if not name:
            raise ValueError("Give the environment a name.")
        with self.lock:
            if name in self.envs:
                raise ValueError(f"There is already an environment called '{name}'.")
            self.envs[name] = []
            self._flush_env(name)

    def duplicate_env(self, name, new_name):
        with self.lock:
            if name not in self.envs:
                raise ValueError("That environment does not exist.")
            self.new_env(new_name)
            self.envs[new_name] = [dict(r) for r in self.envs[name]]
            self._flush_env(new_name)

    def delete_env(self, name):
        with self.lock:
            if name == GLOBALS:
                raise ValueError("Globals cannot be deleted. Clear its rows instead.")
            if name in self.envs:
                self._remove("environments", name)
                del self.envs[name]
                if self.folder:
                    secrets = self._read(self._path("secrets.json")) or {}
                    if secrets.pop(name, None) is not None:
                        _atomic_write(self._path("secrets.json"), json.dumps(secrets, indent=2), private=True)
                if self.settings.get("active_env") == name:
                    self.settings["active_env"] = GLOBALS
                    self._flush_settings()

    def set_var(self, env, key, value):
        """Set one variable (used by 'save to variable'). Creates it, as a secret if its name looks like one."""
        env = env if env in self.envs else GLOBALS
        key = str(key).strip()
        if not key:
            raise ValueError("A variable needs a name.")
        with self.lock:
            for r in self.envs[env]:
                if r["k"] == key:
                    r["v"], r["on"] = str(value), True
                    break
            else:
                self.envs[env].append(_row(key, value, True, secret=_is_secret(key)))
            self._flush_env(env)
            return env, bool([r for r in self.envs[env] if r["k"] == key and r.get("secret")])

    # ---- collections -------------------------------------------------------------------------
    def new_collection(self, name):
        name = str(name).strip()
        if not name:
            raise ValueError("Give the collection a name.")
        with self.lock:
            if name in self.collections:
                raise ValueError(f"There is already a collection called '{name}'.")
            self.collections[name] = {"name": name, "requests": []}
            self._flush_collection(name)

    def rename_collection(self, name, new_name):
        new_name = str(new_name).strip()
        with self.lock:
            if name not in self.collections:
                raise ValueError("That collection does not exist.")
            if not new_name or (new_name != name and new_name in self.collections):
                raise ValueError("Pick a name that is not used yet.")
            self._remove("collections", name)
            c = self.collections.pop(name)
            c["name"] = new_name
            self.collections[new_name] = c
            self._flush_collection(new_name)

    def delete_collection(self, name):
        with self.lock:
            if name in self.collections:
                self._remove("collections", name)
                del self.collections[name]

    def save_request(self, collection, req, name=None, folder=None, rid=None):
        """Save (or overwrite, when rid matches) a request. Returns (id, number_of_secrets_left_out)."""
        collection = str(collection or "").strip()
        if not collection:
            raise ValueError("Choose a collection to save into.")
        clean, n = strip_secrets(req)
        with self.lock:
            c = self.collections.setdefault(collection, {"name": collection, "requests": []})
            existing = next((r for r in c["requests"] if rid and r["id"] == rid), None)
            title = (name or (existing or {}).get("name") or "").strip() or _default_name(clean)
            where = (existing or {}).get("folder", "") if folder is None else str(folder).strip("/ ")
            entry = {"id": rid if existing else new_id(), "name": title, "folder": where, "req": clean}
            if existing:
                existing.update(entry)
            else:
                c["requests"].append(entry)
            self._flush_collection(collection)
            return entry["id"], n

    def delete_request(self, collection, rid):
        with self.lock:
            c = self.collections.get(collection)
            if c:
                c["requests"] = [r for r in c["requests"] if r["id"] != rid]
                self._flush_collection(collection)

    def duplicate_request(self, collection, rid):
        with self.lock:
            c = self.collections.get(collection)
            r = next((r for r in (c or {}).get("requests", []) if r["id"] == rid), None)
            if not r:
                raise ValueError("That request does not exist.")
            c["requests"].append({**copy.deepcopy(r), "id": new_id(), "name": r["name"] + " copy"})
            self._flush_collection(collection)

    # ---- history, settings -------------------------------------------------------------------
    def add_history(self, req, status, ms):
        clean, _ = strip_secrets(req)
        entry = {"id": new_id(), "at": int(time.time()), "status": status, "ms": ms, "req": clean}
        with self.lock:
            self.history = ([entry] + self.history)[:MAX_HISTORY]
            self._flush_history()

    def clear_history(self):
        with self.lock:
            self.history = []
            self._flush_history()

    def update_settings(self, data):
        with self.lock:
            for k in DEFAULT_SETTINGS:
                if k in data:
                    self.settings[k] = data[k]
            self.settings["verify"] = bool(self.settings["verify"])
            self.settings["redirects"] = bool(self.settings["redirects"])
            self._flush_settings()

    # ---- import / export ---------------------------------------------------------------------
    def import_text(self, text, collection=None):
        """Import pasted text: a Postman collection, a Postman environment, or a curl command. Returns a summary."""
        text = (text or "").strip()
        if not text:
            raise ValueError("Paste something to import, or choose a file.")
        if re.match(r"^curl\b", text, re.I):
            parsed = parse_curl(text)
            return {"kind": "curl", "requests": 1, "notes": parsed["notes"], "open": [parsed["req"]]}
        try:
            data = json.loads(text)
        except ValueError:
            raise ValueError("That is not JSON and does not start with curl. Paste a Postman collection or environment export, or a curl command.")
        if isinstance(data, dict) and "info" in data and "item" in data:
            return self._import_collection(data)
        if isinstance(data, dict) and isinstance(data.get("values"), list):
            name = str(data.get("name") or "Imported environment")
            rows = [{"k": v.get("key", ""), "v": v.get("value", ""), "on": v.get("enabled", True) is not False,
                     "secret": v.get("type") == "secret"} for v in data["values"] if isinstance(v, dict)]
            with self.lock:
                if name in self.envs:
                    name = f"{name} (imported)"
                self.save_env(name, rows)
            return {"kind": "environment", "environment": name, "variables": len(rows),
                    "notes": ["Values marked secret were imported into the protected secrets file." if any(r["secret"] for r in rows) else ""]}
        raise ValueError("This JSON is not a Postman collection (v2.x) or Postman environment export.")

    def _import_collection(self, data):
        parsed = parse_postman_collection(data)
        name = parsed["name"]
        with self.lock:
            if name in self.collections:
                name = f"{name} (imported)"
            self.collections[name] = {"name": name, "requests": []}
            stripped = 0
            for item in parsed["requests"]:
                _, n = self.save_request(name, item["req"], item["name"], item["folder"])
                stripped += n
            env_name = None
            if parsed["variables"]:
                env_name = f"{name} variables"
                self.save_env(env_name, parsed["variables"])
        notes = list(parsed["notes"])
        if stripped:
            notes.append(f"{stripped} literal token/password value(s) were not saved to disk. Put them in an environment as secret variables.")
        return {"kind": "collection", "collection": name, "requests": len(parsed["requests"]), "environment": env_name, "notes": notes}

    def export_collection(self, name):
        with self.lock:
            if name not in self.collections:
                raise ValueError("That collection does not exist.")
            return to_postman_collection(self.collections[name])

    def export_env(self, name):
        with self.lock:
            rows = self.envs.get(name)
            if rows is None:
                raise ValueError("That environment does not exist.")
            return {"id": new_id(), "name": name, "_postman_variable_scope": "environment",
                    "values": [{"key": r["k"], "value": "" if r.get("secret") else r["v"], "enabled": r.get("on", True),
                                "type": "secret" if r.get("secret") else "default"} for r in rows]}


def _default_name(req):
    url = (req.get("url") or "").split("?")[0].rstrip("/")
    tail = url.rsplit("/", 1)[-1] if url else ""
    tail = tail if tail and not tail.startswith("{{") else (re.sub(r"^\w+://", "", url) or "request")
    return f"{str(req.get('method', 'get')).upper()} {tail}"[:80]


# ---------------------------------------------------------------------------------------
# curl
# ---------------------------------------------------------------------------------------

_CURL_ARG = {"-X": "method", "--request": "method", "-H": "header", "--header": "header", "-d": "data", "--data": "data",
             "--data-raw": "data", "--data-binary": "data", "--data-ascii": "data", "--data-urlencode": "dataenc",
             "-F": "form", "--form": "form", "-u": "user", "--user": "user", "-b": "cookie", "--cookie": "cookie",
             "-A": "agent", "--user-agent": "agent", "--url": "url", "-m": "timeout", "--max-time": "timeout",
             "-x": "proxy", "--proxy": "proxy", "-e": "skip", "--referer": "skip", "-o": "skip", "--output": "skip",
             "--connect-timeout": "skip", "--retry": "skip", "-w": "skip", "-T": "skip"}
_CURL_FLAGS = set("sSLkviIGgf")


def parse_curl(text):
    """A curl command -> a request in the window's shape, plus notes about anything that could not be carried over."""
    t = re.sub(r"\\\r?\n", " ", text.strip())
    try:
        toks = shlex.split(t)
    except ValueError:
        raise ValueError("That curl command has an unclosed quote. Copy the whole command again.")
    if toks and toks[0].lower() == "curl":
        toks = toks[1:]
    notes, opts, urls, i = [], {"header": [], "data": [], "dataenc": [], "form": []}, [], 0
    flags = set()
    while i < len(toks):
        tok = toks[i]
        if tok.startswith("--") and "=" in tok and tok.split("=", 1)[0] in _CURL_ARG:
            tok, val = tok.split("=", 1)
            toks[i:i + 1] = [tok, val]
        if tok in _CURL_ARG:
            if i + 1 >= len(toks):
                raise ValueError(f"curl option {tok} needs a value.")
            kind, val = _CURL_ARG[tok], toks[i + 1]
            if kind in opts:
                opts[kind].append(val)
            elif kind != "skip":
                opts[kind] = val
            i += 2
            continue
        if re.match(r"^-[A-Za-z]{2,}$", tok) and set(tok[1:]) <= _CURL_FLAGS:
            flags |= set(tok[1:]); i += 1; continue
        if tok in ("-k", "--insecure"):
            flags.add("k")
        elif tok in ("-L", "--location"):
            flags.add("L")
        elif tok in ("-I", "--head"):
            flags.add("I")
        elif tok in ("-G", "--get"):
            flags.add("G")
        elif tok.startswith("-") and len(tok) > 1:
            if tok not in ("-s", "--silent", "-S", "--show-error", "-v", "--verbose", "-i", "--include", "--compressed",
                           "-g", "-f", "--fail", "--http1.1", "--http2", "-#", "--progress-bar"):
                notes.append(f"The curl option {tok} is not supported and was ignored.")
        else:
            urls.append(tok)
        i += 1
    url = opts.get("url") or (urls[0] if urls else "")
    if not url:
        raise ValueError("No web address was found in that curl command.")

    split = urlsplit(url if re.match(r"^\w+://|^\{\{", url) else "//" + url)
    base = url.split("?", 1)[0].split("#", 1)[0]
    params = [_row(k, v) for k, v in parse_qsl(split.query, keep_blank_values=True)] if "?" in url else []
    headers, auth, ctype = [], {"type": "none"}, ""
    for h in opts["header"]:
        if ":" not in h:
            notes.append(f"The header '{h}' has no colon and was ignored.")
            continue
        k, v = (x.strip() for x in h.split(":", 1))
        lk = k.lower()
        if lk == "content-type":
            ctype = v
        if lk == "authorization" and v.lower().startswith("bearer "):
            auth = {"type": "bearer", "token": v[7:].strip()}
        elif lk == "authorization" and v.lower().startswith("basic "):
            import base64
            try:
                u, _, p = base64.b64decode(v[6:].strip()).decode().partition(":")
                auth = {"type": "basic", "user": u, "password": p}
            except Exception:  # noqa
                headers.append(_row(k, v))
        else:
            headers.append(_row(k, v))
    if opts.get("user"):
        u, _, p = opts["user"].partition(":")
        auth = {"type": "basic", "user": u, "password": p}
    if opts.get("cookie"):
        headers.append(_row("Cookie", opts["cookie"]))
    if opts.get("agent"):
        headers.append(_row("User-Agent", opts["agent"]))

    body = {"type": "none"}
    data_parts = list(opts["data"]) + [d if "=" not in d else d for d in opts["dataenc"]]
    if opts["form"]:
        rows = []
        for f in opts["form"]:
            k, _, v = f.partition("=")
            if v.startswith("@"):
                rows.append(_row(k, "", True, kind="file", file=None, fileName=v[1:].split(";")[0]))
                notes.append(f"The form field '{k}' uploads {v[1:].split(';')[0]}. Choose that file again in the Body tab.")
            else:
                rows.append(_row(k, v, True, kind="text", file=None))
        body = {"type": "form", "rows": rows}
    elif data_parts:
        joined = "&".join(data_parts)
        if joined.startswith("@"):
            notes.append(f"The body comes from the file {joined[1:]}. Paste its contents into the Body tab.")
        elif "G" in flags:
            params += [_row(k, v) for k, v in parse_qsl(joined, keep_blank_values=True)]
        else:
            lowtype = ctype.lower()
            stripped = joined.strip()
            if "json" in lowtype or (not lowtype and stripped[:1] in "{["):
                try:
                    body = {"type": "json", "json": json.dumps(json.loads(stripped), indent=2, ensure_ascii=False)}
                except ValueError:
                    body = {"type": "raw", "raw": joined, "rawType": ctype.split(";")[0] or "application/json"}
            elif ("urlencoded" in lowtype or not lowtype) and re.match(r"^[^=&\s]+=[^&]*(&[^=&]+=[^&]*)*$", stripped):
                body = {"type": "urlencoded", "rows": [_row(k, v) for k, v in
                                                       ((unquote_plus(a), unquote_plus(b)) for a, _, b in (p.partition("=") for p in joined.split("&")))]}
            else:
                body = {"type": "raw", "raw": joined, "rawType": ctype.split(";")[0] or "text/plain"}
    if body["type"] in ("json", "urlencoded", "form"):
        headers = [h for h in headers if h["k"].lower() != "content-type"]
    elif body["type"] == "raw":
        headers = [h for h in headers if h["k"].lower() != "content-type"]

    method = (opts.get("method") or ("head" if "I" in flags else ("post" if (data_parts or opts["form"]) and "G" not in flags else "get"))).lower()
    if method not in ("get", "post", "put", "patch", "delete", "head", "options"):
        notes.append(f"The method {method.upper()} is not supported. GET was used.")
        method = "get"
    req = blank_request(method=method, url=base, params=params, headers=headers, auth=auth, body=body)
    if "k" in flags:
        req["verify"] = False
        notes.append("curl -k: SSL checking is turned off for this request.")
    if "L" not in flags:
        req["redirects"] = False
    if opts.get("timeout"):
        req["timeout"] = str(opts["timeout"])
    if opts.get("proxy"):
        notes.append("A proxy was set in the curl command. Set it in Settings if you need it.")
    return {"req": req, "notes": notes}


# ---------------------------------------------------------------------------------------
# Postman collections v2.x
# ---------------------------------------------------------------------------------------

def _pm_auth(auth, notes, where):
    """Postman auth block -> (our auth dict, extra query rows)."""
    if not isinstance(auth, dict):
        return None, []
    kind = auth.get("type")

    def vals(name):
        lst = auth.get(name) or []
        return {x.get("key"): x.get("value") for x in lst if isinstance(x, dict)} if isinstance(lst, list) else {}
    if kind == "noauth":
        return {"type": "none"}, []
    if kind == "bearer":
        return {"type": "bearer", "token": str(vals("bearer").get("token", ""))}, []
    if kind == "basic":
        v = vals("basic")
        return {"type": "basic", "user": str(v.get("username", "")), "password": str(v.get("password", ""))}, []
    if kind == "apikey":
        v = vals("apikey")
        if v.get("in") == "query":
            return {"type": "none"}, [_row(v.get("key", ""), v.get("value", ""))]
        return {"type": "header", "name": str(v.get("key", "")), "value": str(v.get("value", ""))}, []
    notes.append(f"{where}: auth type '{kind}' is not supported. Set the login by hand.")
    return {"type": "none"}, []


def parse_postman_collection(data):
    notes, requests, scripts = [], [], [0]
    info = data.get("info") or {}
    name = str(info.get("name") or "Imported collection")
    top_auth = data.get("auth")

    def walk(items, folder, inherited):
        for it in items or []:
            if not isinstance(it, dict):
                continue
            if it.get("event"):
                scripts[0] += len(it["event"])
            if "item" in it:
                sub = f"{folder}/{it.get('name', 'folder')}" if folder else str(it.get("name", "folder"))
                walk(it["item"], sub, it.get("auth") or inherited)
            elif "request" in it:
                requests.append({"name": str(it.get("name") or "request"), "folder": folder,
                                 "req": _pm_request(it["request"], it.get("auth") or inherited, notes, str(it.get("name") or "request"))})
    walk(data.get("item"), "", top_auth)
    if data.get("event"):
        scripts[0] += len(data["event"])
    if scripts[0]:
        notes.append(f"{scripts[0]} Postman script(s) (pre-request or test) were not imported. Use the Checks and Save-to-variable tabs instead.")
    variables = [{"k": v.get("key", ""), "v": v.get("value", ""), "on": not v.get("disabled", False), "secret": _is_secret(v.get("key", ""))}
                 for v in data.get("variable", []) if isinstance(v, dict) and v.get("key")]
    return {"name": name, "requests": requests, "variables": variables, "notes": list(dict.fromkeys(notes))}


def _pm_request(r, inherited_auth, notes, label):
    if isinstance(r, str):
        return blank_request(url=r)
    url = r.get("url")
    params, raw = [], ""
    if isinstance(url, str):
        raw = url
    elif isinstance(url, dict):
        raw = str(url.get("raw") or "")
        if not raw and url.get("host"):
            host = ".".join(url["host"]) if isinstance(url["host"], list) else str(url["host"])
            path = "/".join(url.get("path", [])) if isinstance(url.get("path"), list) else str(url.get("path", ""))
            raw = f"{url.get('protocol', 'https')}://{host}/{path}"
        for q in url.get("query") or []:
            if isinstance(q, dict) and q.get("key") is not None:
                params.append(_row(q["key"], q.get("value", ""), not q.get("disabled", False)))
        for pv in url.get("variable") or []:
            if isinstance(pv, dict) and pv.get("key") and pv.get("value") not in (None, ""):
                raw = raw.replace(":" + pv["key"], str(pv["value"]))
    if "?" in raw:
        base, _, qs = raw.partition("?")
        if not params:
            params = [_row(k, v) for k, v in parse_qsl(qs, keep_blank_values=True)]
        raw = base
    headers = [_row(h.get("key", ""), h.get("value", ""), not h.get("disabled", False))
               for h in r.get("header") or [] if isinstance(h, dict) and h.get("key")]
    auth, extra = _pm_auth(r.get("auth") or inherited_auth, notes, label)
    params += extra
    body = {"type": "none"}
    b = r.get("body")
    if isinstance(b, dict):
        mode = b.get("mode")
        if mode == "raw":
            lang = ((b.get("options") or {}).get("raw") or {}).get("language", "")
            text = str(b.get("raw", ""))
            if lang == "json" or (not lang and text.strip()[:1] in "{["):
                body = {"type": "json", "json": text}
            else:
                body = {"type": "raw", "raw": text, "rawType": {"xml": "application/xml", "html": "text/html"}.get(lang, "text/plain")}
        elif mode == "urlencoded":
            body = {"type": "urlencoded", "rows": [_row(x.get("key", ""), x.get("value", ""), not x.get("disabled", False))
                                                    for x in b.get("urlencoded") or [] if isinstance(x, dict)]}
        elif mode == "formdata":
            rows = []
            for x in b.get("formdata") or []:
                if not isinstance(x, dict):
                    continue
                if x.get("type") == "file":
                    rows.append(_row(x.get("key", ""), "", not x.get("disabled", False), kind="file", file=None, fileName=str(x.get("src") or "")))
                else:
                    rows.append(_row(x.get("key", ""), x.get("value", ""), not x.get("disabled", False), kind="text", file=None))
            body = {"type": "form", "rows": rows}
        elif mode == "graphql":
            g = b.get("graphql") or {}
            payload = {"query": g.get("query", "")}
            try:
                if g.get("variables"):
                    payload["variables"] = json.loads(g["variables"])
            except ValueError:
                notes.append(f"{label}: GraphQL variables were not valid JSON and were left out.")
            body = {"type": "json", "json": json.dumps(payload, indent=2)}
        elif mode in ("file", "binary"):
            notes.append(f"{label}: a binary file body is not supported. Use form-data with a File row.")
    if body["type"] in ("json", "urlencoded", "form", "raw"):
        headers = [h for h in headers if h["k"].lower() != "content-type"]
    return blank_request(method=str(r.get("method", "GET")).lower(), url=raw, params=params, headers=headers, auth=auth or {"type": "none"}, body=body)


def to_postman_collection(coll):
    """Our collection -> Postman v2.1 JSON, so it can be opened in Postman or shared."""
    root, folders = [], {}

    def folder_items(path):
        items, cur = root, ""
        for part in [p for p in path.split("/") if p]:
            cur = f"{cur}/{part}" if cur else part
            if cur not in folders:
                node = {"name": part, "item": []}
                items.append(node)
                folders[cur] = node["item"]
            items = folders[cur]
        return items

    for entry in coll.get("requests", []):
        req = entry["req"]
        headers = [{"key": h["k"], "value": h["v"], "disabled": not h.get("on", True)} for h in req.get("headers") or [] if h.get("k")]
        query = [{"key": p["k"], "value": p["v"], "disabled": not p.get("on", True)} for p in req.get("params") or [] if p.get("k")]
        raw_url = req.get("url", "")
        enabled_q = "&".join(f"{q['key']}={q['value']}" for q in query if not q["disabled"])
        pm = {"method": str(req.get("method", "get")).upper(), "header": headers,
              "url": {"raw": raw_url + (("?" + enabled_q) if enabled_q else ""), "query": query}}
        b = req.get("body") or {}
        t = b.get("type")
        if t == "json" and str(b.get("json", "")).strip():
            pm["body"] = {"mode": "raw", "raw": b["json"], "options": {"raw": {"language": "json"}}}
        elif t == "raw" and b.get("raw"):
            pm["body"] = {"mode": "raw", "raw": b["raw"]}
        elif t == "urlencoded":
            pm["body"] = {"mode": "urlencoded", "urlencoded": [{"key": r["k"], "value": r["v"], "disabled": not r.get("on", True)} for r in b.get("rows") or [] if r.get("k")]}
        elif t == "form":
            pm["body"] = {"mode": "formdata", "formdata": [
                ({"key": r["k"], "type": "file", "src": r.get("fileName") or "", "disabled": not r.get("on", True)} if r.get("kind") == "file"
                 else {"key": r["k"], "value": r["v"], "type": "text", "disabled": not r.get("on", True)}) for r in b.get("rows") or [] if r.get("k")]}
        a = req.get("auth") or {}
        if a.get("type") == "bearer":
            pm["auth"] = {"type": "bearer", "bearer": [{"key": "token", "value": a.get("token", ""), "type": "string"}]}
        elif a.get("type") == "basic":
            pm["auth"] = {"type": "basic", "basic": [{"key": "username", "value": a.get("user", "")}, {"key": "password", "value": a.get("password", "")}]}
        elif a.get("type") == "header":
            pm["auth"] = {"type": "apikey", "apikey": [{"key": "key", "value": a.get("name", "")}, {"key": "value", "value": a.get("value", "")}, {"key": "in", "value": "header"}]}
        folder_items(entry.get("folder", "")).append({"name": entry["name"], "request": pm})
    return {"info": {"_postman_id": new_id(), "name": coll["name"],
                     "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"}, "item": root}