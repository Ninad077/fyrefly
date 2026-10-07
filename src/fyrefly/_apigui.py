"""The Fyrefly API window: a small Postman-like page that runs on your own computer.

api.gui() starts a tiny web server that listens on 127.0.0.1 only (your computer, nobody else),
opens the page in your browser, and sends each request through the engine, so you get a plain-English report and
HOW TO FIX IT advice. Nothing here needs an install: it is the standard
library plus the requests package Fyrefly already uses.
"""
import base64
import contextlib
import io
import re
import json
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import _apistore
from .api import (APIError, _MISSING, _VAR, _call_text, _dig, _fill_vars, _is_secret, _parse_headers, _parse_send)
from ._apipage import PAGE as _PAGE

MAX_REQUEST = 80 * 1024 * 1024     # biggest request body the window accepts (file uploads included)
MAX_SHOWN = 5 * 1024 * 1024        # biggest response body shown in the window
_LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]")


# ---------------------------------------------------------------------------------------
# page request  ->  api.test(...) call
# ---------------------------------------------------------------------------------------

def _rows(rows, join=False):
    """Switched-on rows with a name, as a dict. A name used twice becomes a list (or a joined string)."""
    out = {}
    for r in rows or []:
        k = str(r.get("k", "")).strip()
        if not r.get("on", True) or not k:
            continue
        v = str(r.get("v", ""))
        if k in out:
            if join:
                out[k] = f"{out[k]}, {v}"
            else:
                out[k] = (out[k] if isinstance(out[k], list) else [out[k]]) + [v]
        else:
            out[k] = v
    return out


def _soft_fill(text, variables):
    return _fill_vars(text, variables, strict=False)


def build_call(payload, known_vars):
    """Turn what the page sent into (kwargs for api.test, python text, variables). Raises ValueError with a friendly message."""
    p = payload or {}
    url = str(p.get("url") or "").strip()
    if not url:
        raise ValueError("Type a web address first, for example https://api.example.com/users")
    variables = {**known_vars, **{k: v for k, v in _rows(p.get("variables")).items()}}
    method = str(p.get("method") or "get").lower()

    kw = {"url": url, "method": method}
    file_names = []
    params = _rows(p.get("params"))
    headers = _rows(p.get("headers"), join=True)
    if params:
        kw["params"] = params
    if headers:
        kw["headers"] = headers

    auth = p.get("auth") or {}
    kind = None
    t = auth.get("type")
    if t == "bearer" and auth.get("token"):
        kw["token"], kind = auth["token"], "token"
    elif t == "basic" and (auth.get("user") or auth.get("password")):
        kw["user"], kw["password"], kind = auth.get("user", ""), auth.get("password", ""), "basic"
    elif t == "header" and auth.get("name") and auth.get("value"):
        kw["key"], kind = (auth["name"].strip(), auth["value"]), "key"

    body = p.get("body") or {}
    bt = body.get("type", "none")
    text_body, form_flag, extra = None, False, []
    if bt == "json" and str(body.get("json", "")).strip():
        raw = _soft_fill(body["json"], variables)
        try:
            kw["send"] = text_body = json.loads(raw)
        except ValueError as e:
            hint = " A {{variable}} with no value inside the JSON can cause this." if "{{" in raw else ""
            raise ValueError(f"The JSON in the Body tab is not valid ({e}). Check the brackets, quotes and commas.{hint}")
    elif bt == "urlencoded":
        fields = _rows(body.get("rows"), join=True)
        if fields:
            kw["send"], text_body, form_flag = fields, fields, True
            kw["form"] = True
    elif bt == "form":
        parts, fields = [], {}
        for r in body.get("rows") or []:
            k = str(r.get("k", "")).strip()
            if not r.get("on", True) or not k:
                continue
            if r.get("kind") == "file":
                f = r.get("file")
                if not f:
                    raise ValueError(f"The form-data row '{k}' is set to File, but no file was chosen.")
                try:
                    content = base64.b64decode(f.get("b64", ""), validate=True)
                except ValueError:
                    raise ValueError(f"The file for '{k}' could not be read. Choose it again.")
                parts.append((k, (f.get("name") or "file", content, f.get("type") or None)))
                file_names.append(k)
            else:
                parts.append((k, (None, str(r.get("v", "")))))
                fields[k] = str(r.get("v", ""))
        if parts:
            kw["files"] = parts
            text_body, form_flag = fields or None, bool(fields) and not file_names
            if fields and not file_names:
                form_flag = True
    elif bt == "raw" and str(body.get("raw", "")) != "":
        kw["send"] = _soft_fill(body["raw"], variables).encode("utf-8")
        ctype = body.get("rawType") or "text/plain"
        if not any(k.lower() == "content-type" for k in kw.get("headers", {})):
            kw["headers"] = {**kw.get("headers", {}), "Content-Type": ctype}
        text_body = None
        extra.append('send="YOUR_TEXT".encode()')

    expect = str(p.get("expect") or "").strip()
    if expect:
        kw["expect"] = int(expect) if expect.isdigit() else expect
    look = [x.strip() for x in str(p.get("look_for") or "").split(",") if x.strip()]
    if look:
        kw["look_for"] = look[0] if len(look) == 1 else look
    try:
        times = int(p.get("times") or 1)
    except (TypeError, ValueError):
        times = 1
    if times > 1:
        kw["times"] = min(times, 50)
    wait = str(p.get("timeout") or "").strip()
    if wait:
        try:
            kw["wait"] = float(wait) if "." in wait else int(wait)
        except ValueError:
            raise ValueError("Timeout must be a number of seconds, such as 30.")

    # the Python you could paste to repeat this without the window (secrets are always placeholders)
    visible_headers = dict(kw.get("headers") or {})
    code_lines = []
    used = list(dict.fromkeys(_VAR.findall(json.dumps({k: v for k, v in p.items() if k != "variables"}, default=str))))
    if used:
        pairs = ", ".join(f'{n}="{"YOUR_VALUE" if _is_secret(n) else variables.get(n, "")}"' for n in used if n.isidentifier())
        if pairs:
            code_lines.append(f"api.vars({pairs})")
    code_lines.append(_call_text(url, method, text_body if isinstance(text_body, dict) else None, visible_headers or None,
                                 params or None, auth=kind, form=form_flag, extra=extra, files=file_names or None,
                                 look_for=kw.get("look_for"), expect=kw.get("expect")))
    return kw, "\n".join(code_lines), variables


# ---------------------------------------------------------------------------------------
# running it, and describing the answer for the page
# ---------------------------------------------------------------------------------------

def _describe(r):
    """Everything the page needs to show about a Result."""
    raw = r.raw.content or b""
    ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    out = {"connected": True, "status": r.status, "reason": r.reason, "ms": round(r.ms), "size": r.size,
           "content_type": ctype, "headers": [[k, v] for k, v in r.headers.items()],
           "request_headers": [[k, "***" if _is_secret(k) else v] for k, v in r.request["headers"].items()],
           "kind": "empty", "body": "", "pretty": None, "image": None, "table": None, "truncated": False,
           "redirects": [[h.status_code, h.url] for h in r.raw.history], "cookies": sorted(r.raw.cookies.keys())}
    data = r.json
    if not raw:
        pass
    elif ctype.startswith("image/") and len(raw) <= MAX_SHOWN:
        out["kind"], out["image"] = "image", f"data:{ctype};base64,{base64.b64encode(raw).decode()}"
    elif data is not None:
        out["kind"] = "json"
        out["pretty"] = json.dumps(data, indent=2, ensure_ascii=False)
        out["body"] = out["pretty"]
    else:
        try:
            text = r.text
        except Exception:  # noqa
            text = ""
        if text and "\x00" not in text[:2000]:
            out["kind"] = "html" if "html" in ctype else "text"
            out["body"] = text
        else:
            out["kind"] = "binary"
            out["body"] = f"({r.size} bytes of binary data, content type {ctype or 'unknown'})"
    if len(out["body"]) > MAX_SHOWN:
        out["body"], out["truncated"] = out["body"][:MAX_SHOWN], True
        out["pretty"] = out["body"] if out["pretty"] else None
    if data is not None:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                frame = r.df(quiet=True)
            small = frame.iloc[:200, :40]
            out["table"] = json.loads(small.to_json(orient="split", date_format="iso", default_handler=str,
                                                    index=False))
            out["table"]["total"] = len(frame)
        except Exception:  # noqa
            out["table"] = None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            out["curl"] = r.curl(mask=True)
    except Exception:  # noqa
        out["curl"] = ""
    return out


def _extract(r, path):
    """One value out of a response: a dotted JSON path, header:Name, status, or body."""
    path = str(path).strip()
    low = path.lower()
    if low.startswith("header:"):
        return r.headers.get(path[7:].strip())
    if low == "status":
        return r.status
    if low == "body":
        return r.text
    value = _dig(r.json, path) if r.json is not None else _MISSING
    return None if value is _MISSING else value


def apply_saves(r, rules, ws, env):
    """Save values from the response into variables ("save to variable"). Returns what happened, for the page."""
    done = []
    for rule in rules or []:
        name, path = str(rule.get("var", "")).strip().lstrip("{").rstrip("}").strip(), str(rule.get("path", "")).strip()
        if not name or not path:
            continue
        value = _extract(r, path)
        if value is None:
            done.append({"k": name, "path": path, "error": f"'{path}' was not found in the answer, so {{{{{name}}}}} was not changed."})
            continue
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        where, secret = ws.set_var(env, name, text)
        done.append({"k": name, "path": path, "env": where, "secret": secret,
                     "value": "" if secret else (text if len(text) <= 80 else text[:77] + "...")})
    return done


# ---- the window talks in tabs, not in Python: only api.gui() is public --------------------------------
_WHERE = [
    (r"^user= and password=.*", "the Authorization tab: choose Basic, then fill in the user and password"),
    (r"^key=.*", "the Authorization tab: choose API key. If the docs name a different header, add it in the Headers tab instead"),
    (r"^token=.*", "the Authorization tab: choose Bearer token and paste the token"),
    (r"^method=.*", "the method box, next to the address"),
    (r"^the values in send=.*", "the values in the Body tab"),
    (r"^form= \(remove it.*", "the Body tab: choose JSON instead of the web form"),
    (r"^form= or headers=.*", "the Body tab (web form or JSON) or the Headers tab"),
    (r"^files=.*", "the Body tab: choose form-data, then add a row with the field name and choose the file"),
    (r"^the body\. Use send=.*", "the Body tab"),
    (r"^the address, send=, headers=, or params=.*", "the address, or the Body, Headers or Params tab"),
    (r"^headers=.*", "the Headers tab"),
    (r"^api\.vars\(.*", "the Variables tab, or the active environment"),
    (r"^api\.verify\(False\).*", "the Settings tab: turn off the SSL certificate check"),
    (r"^wait=.*", "the Settings tab: timeout"),
    (r"^expect=.*", "the Checks tab: expected status"),
    (r"^look_for=.*", "the Checks tab: fields to look for"),
    (r"^times=.*", "the Checks tab: how many times"),
]
_PHRASES = [
    (re.compile(r"Give each one a value with api\.vars\([^)]*\)\."), "Give each one a value in the Variables tab, or in the active environment."),
    (re.compile(r"Pass a full URL, or call api\.base\([^)]*\) first\."), "Type the full address, starting with https://."),
    (re.compile(r"Raise it with timeout=\.\.\. or api\.timeout\(\.\.\.\)\."), "Raise it in the Settings tab (timeout)."),
    (re.compile(r"you can skip the check with api\.verify\(False\)\."), "you can turn the check off in the Settings tab."),
]


def window_text(text):
    """Rewrite a report or error so it points at the window's tabs, and drop the Python 'Try:' lines."""
    out = []
    for ln in str(text or "").splitlines():
        m = re.match(r"^(\s+)(Where|Try|Note):\s+(.*)$", ln)
        if m and (m.group(2) == "Try" or (m.group(2) == "Note" and m.group(3).startswith("Replace each YOUR_"))):
            continue
        if m and m.group(2) == "Where":
            val = m.group(3)
            for pat, repl in _WHERE:
                if re.match(pat, val):
                    val = repl
                    break
            ln = f"{m.group(1)}Where:  {val}"
        for pat, repl in _PHRASES:
            ln = pat.sub(repl, ln)
        out.append(ln)
    return "\n".join(out) + ("\n" if str(text or "").endswith("\n") else "")



def run_payload(api, lock, payload, ws=None, bodies=None):
    """Send what the page asked for through api.test() and describe the result."""
    ws = ws or _apistore.Workspace(None)
    try:
        with lock:
            env = payload.get("env") or ws.settings.get("active_env")
            known = {**api._vars, **ws.resolved(env)}
            kw, python, variables = build_call(payload, known)
            st = ws.settings
            if "wait" not in kw and str(st.get("timeout") or "").strip():
                try:
                    kw["wait"] = float(st["timeout"])
                except ValueError:
                    pass
            keep = (api._vars, api._verify, api._proxy, api._redirects)
            api._vars = {**api._vars, **variables}
            api._verify = st["verify"] if payload.get("verify") is None else bool(payload["verify"])
            api._redirects = st["redirects"] if payload.get("redirects") is None else bool(payload["redirects"])
            api._proxy = (st.get("proxy") or "").strip() or None
            api._last = None
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    r = api.test(**kw)
            finally:
                api._vars, api._verify, api._proxy, api._redirects = keep
            report = window_text(buf.getvalue())
            reply = _describe(r) if r is not None else {"connected": False}
            reply.update(report=report, python=python, error=None, saved=[], env=env)
            if r is not None:
                if payload.get("saves"):
                    reply["saved"] = apply_saves(r, payload["saves"], ws, env)
                if bodies is not None:
                    rid = _apistore.new_id()
                    bodies[rid] = (r.raw.content or b"", reply["content_type"])
                    while len(bodies) > 6:
                        bodies.pop(next(iter(bodies)))
                    reply["rid"] = rid
                ws.add_history({k: v for k, v in payload.items() if k not in ("variables", "env")}, r.status, reply["ms"])
            return reply
    except (ValueError, APIError) as e:
        return {"connected": False, "report": "", "python": "", "error": window_text(str(e)), "saved": []}


# ---------------------------------------------------------------------------------------
# what the window shows when it opens
# ---------------------------------------------------------------------------------------

def make_preset(url=None, method="get", send=None, headers=None, token=None, user=None, password=None, key=None,
                params=None, expect=None, look_for=None, times=1, form=False, wait=None, variables=None):
    """Fill the page with the arguments given to api.test(..., gui=True)."""
    def rows(d):
        return [{"on": True, "k": str(k), "v": "" if v is None else str(v)} for k, v in (d or {}).items()]

    p = {"method": str(method or "get").lower(), "url": url or "", "params": rows(_parse_send(params) if not isinstance(params, dict) else params),
         "headers": rows(_parse_headers(headers)), "variables": rows(variables), "expect": "" if expect is None else str(expect),
         "look_for": ", ".join([look_for] if isinstance(look_for, str) else (look_for or [])),
         "times": times or 1, "timeout": "" if wait is None else str(wait), "auth": {"type": "none"},
         "body": {"type": "none"}}
    body = _parse_send(send)
    if isinstance(body, bytes):
        p["body"] = {"type": "raw", "raw": body.decode("utf-8", "replace"), "rawType": "text/plain"}
    elif isinstance(body, dict) and form:
        p["body"] = {"type": "urlencoded", "rows": rows(body)}
    elif body is not None:
        p["body"] = {"type": "json", "json": json.dumps(body, indent=2, ensure_ascii=False)}
    if token:
        p["auth"] = {"type": "bearer", "token": str(token)}
    elif user is not None:
        p["auth"] = {"type": "basic", "user": str(user), "password": str(password or "")}
    elif key:
        name, value = key if isinstance(key, tuple) else ("X-API-Key", key)
        p["auth"] = {"type": "header", "name": name, "value": str(value)}
    return p


# ---------------------------------------------------------------------------------------
# the server
# ---------------------------------------------------------------------------------------

class GuiServer:
    """A running window. .url is its address; .stop() closes it."""

    def __init__(self, api, preset, port=0, workspace=None):
        self.api = api
        self.ws = workspace if workspace is not None else _apistore.Workspace(None)
        self.bodies = {}
        self.token = secrets.token_urlsafe(24)
        self.lock = threading.Lock()
        self._page = _PAGE.replace("__TOKEN__", self.token).replace(
            "__PRESET__", json.dumps(preset).replace("</", "<\\/"))
        outer = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "FyreflyWindow"

            def log_message(self, *args):
                pass

            # -- safety: only this computer, only this page, only with the secret in the address
            def _allowed(self):
                host = (self.headers.get("Host") or "").rsplit(":", 1)[0].lower()
                if host not in _LOCAL_HOSTS:
                    return False
                origin = self.headers.get("Origin")
                if origin and urlparse(origin).hostname not in ("127.0.0.1", "localhost", "::1"):
                    return False
                return True

            def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
                data = body if isinstance(body, bytes) else body.encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                if not self._allowed():
                    return self._send(403, "Forbidden", "text/plain")
                u = urlparse(self.path)
                if u.path == "/" and parse_qs(u.query).get("t", [""])[0] == outer.token:
                    return self._send(200, outer._page, "text/html; charset=utf-8", {
                        "Content-Security-Policy": "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                                                   "img-src data:; connect-src 'self'; frame-src about:; base-uri 'none'; form-action 'none'"})
                if u.path == "/favicon.ico":
                    return self._send(204, "", "text/plain")
                self._send(403, "Open the address that api.gui() printed.", "text/plain")

            def do_POST(self):
                if not self._allowed() or self.headers.get("X-Fyrefly-Token") != outer.token:
                    return self._send(403, json.dumps({"error": "Forbidden"}))
                path = urlparse(self.path).path
                if path == "/quit":
                    self._send(200, json.dumps({"ok": True}))
                    threading.Thread(target=outer.stop, daemon=True).start()
                    return
                if path not in ("/send", "/op"):
                    return self._send(404, json.dumps({"error": "Not found"}))
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                except ValueError:
                    n = 0
                if n <= 0 or n > MAX_REQUEST:
                    return self._send(413, json.dumps({"connected": False, "report": "", "python": "",
                                                       "error": f"That request is too large (limit {MAX_REQUEST // 1024 // 1024} MB). Use a smaller file."}))
                try:
                    payload = json.loads(self.rfile.read(n).decode("utf-8"))
                except ValueError:
                    return self._send(400, json.dumps({"connected": False, "report": "", "python": "", "error": "The window sent something unreadable."}))
                if path == "/op":
                    return self._send(200, json.dumps(handle_op(outer, payload), default=str))
                reply = run_payload(outer.api, outer.lock, payload, outer.ws, outer.bodies)
                self._send(200, json.dumps(reply, default=str))

        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/?t={self.token}"
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._stopped = threading.Event()

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        if not self._stopped.is_set():
            self._stopped.set()
            self.httpd.shutdown()
            self.httpd.server_close()

    def wait(self):
        """Block until the window is closed (Quit button) or Ctrl+C."""
        try:
            while not self._stopped.wait(0.3):
                pass
        except KeyboardInterrupt:
            self.stop()

    def __repr__(self):
        return f"<Fyrefly API window at {self.url}>"


def handle_op(server, d):
    """Everything the page does besides sending: save, environments, import/export, settings."""
    ws, op = server.ws, str((d or {}).get("op", ""))
    try:
        if op == "state":
            return {"ok": True, "state": ws.state()}
        if op == "env_save":
            ws.save_env(d.get("name"), d.get("rows"))
        elif op == "env_new":
            ws.new_env(d.get("name"))
        elif op == "env_duplicate":
            ws.duplicate_env(d.get("name"), d.get("new_name"))
        elif op == "env_delete":
            ws.delete_env(d.get("name"))
        elif op == "set_var":
            ws.set_var(d.get("env"), d.get("k"), d.get("v", ""))
        elif op == "coll_new":
            ws.new_collection(d.get("name"))
        elif op == "coll_rename":
            ws.rename_collection(d.get("name"), d.get("new_name"))
        elif op == "coll_delete":
            ws.delete_collection(d.get("name"))
        elif op == "req_save":
            rid, n = ws.save_request(d.get("collection"), d.get("req") or {}, d.get("name"), d.get("folder"), d.get("rid"))
            return {"ok": True, "state": ws.state(), "rid": rid, "stripped": n}
        elif op == "req_delete":
            ws.delete_request(d.get("collection"), d.get("rid"))
        elif op == "req_duplicate":
            ws.duplicate_request(d.get("collection"), d.get("rid"))
        elif op == "history_clear":
            ws.clear_history()
        elif op == "settings":
            ws.update_settings(d.get("settings") or {})
        elif op == "cookies_clear":
            server.api.cookies(clear=True)
        elif op == "import":
            out = ws.import_text(d.get("text"), d.get("collection"))
            return {"ok": True, "state": ws.state(), "result": out}
        elif op == "export_coll":
            return {"ok": True, "data": ws.export_collection(d.get("name"))}
        elif op == "export_env":
            return {"ok": True, "data": ws.export_env(d.get("name"))}
        elif op == "body":
            rid = d.get("rid")
            if rid not in server.bodies:
                return {"error": "That answer is no longer kept. Send the request again, then download."}
            data, ctype = server.bodies[rid]
            return {"ok": True, "b64": base64.b64encode(data).decode(), "content_type": ctype}
        else:
            return {"error": f"Unknown action '{op}'."}
        return {"ok": True, "state": ws.state()}
    except ValueError as e:
        return {"error": str(e)}


def _in_notebook():
    """True only inside a real Jupyter notebook kernel. Merely having ipykernel installed or imported does not count."""
    try:
        from IPython import get_ipython
        ip = get_ipython()
        return ip is not None and ip.__class__.__name__ == "ZMQInteractiveShell"
    except Exception:  # noqa
        return False


def serve(api, preset=None, port=0, open_browser=True, block=None, folder=None):
    if folder is False:
        ws = _apistore.Workspace(None)
    else:
        ws = _apistore.Workspace(folder or _apistore.default_folder())
    server = GuiServer(api, preset or make_preset(), port, ws).start()
    print("Fyrefly API window is running. It is only reachable from this computer.")
    print(f"Saved requests and environments live in: {ws.folder}" if ws.folder else "Nothing will be saved (folder=False).")
    print(f"If it does not open by itself, paste this into your browser:\n  {server.url}")
    if open_browser:
        try:
            webbrowser.open(server.url)
        except Exception:  # noqa
            pass
    if block is None:
        block = not _in_notebook()
    if block:
        print("Click Quit in the window, or press Ctrl+C here, to close it.")
        server.wait()
        print("Window closed.")
        return None
    print("Run  window.stop()  to close it.")
    return server