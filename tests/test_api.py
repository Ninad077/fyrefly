import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import pandas as pd
import pytest

from fyrefly import sql
from fyrefly.api import _engine as api, APIError, api as public_api

USERS = [{"id": 1, "name": "Asha", "tags": ["admin"]}, {"id": 2, "name": "Bilal", "tags": []}]
STATE = {"flaky": 0}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body=None, ctype="application/json", extra=None):
        payload = b"" if body is None else (body if isinstance(body, bytes) else (json.dumps(body) if ctype == "application/json" else body).encode())
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        ctype = self.headers.get("Content-Type", "")
        if "json" in ctype and raw:
            return json.loads(raw)
        return raw.decode()

    def _authorized(self):
        h = self.headers
        return (h.get("Authorization") in ("Bearer secret", "Bearer tok123", "Basic dTpw")  # dTpw = u:p
                or h.get("X-API-Key") == "k123")

    def route(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p, m = u.path, self.command
        if p == "/users" and m == "GET":
            return self._send(200, {"users": USERS})
        if p == "/list" and m == "GET":
            return self._send(200, USERS)
        if p.startswith("/users/") and m == "GET":
            uid = p.split("/")[-1]
            for usr in USERS:
                if str(usr["id"]) == uid:
                    return self._send(200, usr)
            return self._send(404, {"error": "not found"})
        if p == "/users" and m == "POST":
            return self._send(201, {"id": 3, **self._body()})
        if p == "/users/1" and m in ("PUT", "PATCH"):
            return self._send(200, {"id": 1, "method": m, **self._body()})
        if p == "/users/1" and m == "DELETE":
            return self._send(204)
        if p == "/users/1" and m == "HEAD":
            return self._send(200, USERS[0])
        if p == "/users" and m == "OPTIONS":
            return self._send(204, extra={"Allow": "GET, POST, OPTIONS"})
        if p == "/echo":
            return self._send(200, {"method": m, "query": q, "headers": {k.lower(): v for k, v in self.headers.items()},
                                    "body": self._body()})
        if p == "/validate" and m == "POST":
            b = self._body()
            need = [f for f in ("name", "email") if not (isinstance(b, dict) and f in b)]
            if need:
                return self._send(422, {"detail": [{"loc": ["body", f], "msg": "field required", "type": "missing"} for f in need]})
            return self._send(201, b)
        if p == "/rails" and m == "POST":
            return self._send(422, {"errors": {"email": ["can't be blank"], "age": ["must be a number"]}})
        if p == "/needheader":
            return self._send(200, {"ok": 1}) if self.headers.get("X-Tenant-Id") else self._send(400, {"error": "Missing required header X-Tenant-Id"})
        if p == "/basic":
            return self._send(200, {"ok": 1}) if self._authorized() else self._send(401, {"error": "no"}, extra={"WWW-Authenticate": 'Basic realm="x"'})
        if p == "/apikey":
            return self._send(200, {"ok": 1}) if self.headers.get("X-API-Key") == "k123" else self._send(401, {"error": "Invalid api key"})
        if p == "/ratelimit":
            return self._send(429, {"error": "slow down"}, extra={"Retry-After": "7"})
        if p == "/getonly":
            return self._send(200, {"ok": 1}) if m == "GET" else self._send(405, {"error": "nope"}, extra={"Allow": "GET, HEAD"})
        if p == "/conflict" and m == "POST":
            return self._send(409, {"error": "email already exists"})
        if p == "/formonly" and m == "POST":
            return self._send(415, {"error": "unsupported media type"}) if "json" in self.headers.get("Content-Type", "") else self._send(200, {"ok": 1})
        if p == "/upload" and m == "POST":
            from email.parser import BytesParser
            from email.policy import default
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n)
            ct = self.headers.get("Content-Type", "")
            if not ct.startswith("multipart/form-data"):
                return self._send(415, {"error": "send multipart/form-data"})
            msg = BytesParser(policy=default).parsebytes(b"Content-Type: " + ct.encode() + b"\r\n\r\n" + raw)
            fields, files = {}, {}
            for part in msg.iter_parts():
                name, fn = part.get_param("name", header="content-disposition"), part.get_filename()
                body = part.get_payload(decode=True) or b""
                if fn:
                    files[name] = {"filename": fn, "size": len(body), "type": part.get_content_type()}
                else:
                    fields[name] = body.decode()
            if "file" not in files:
                return self._send(422, {"detail": [{"loc": ["body", "file"], "msg": "field required"}]})
            return self._send(200, {"fields": fields, "files": files})
        if p == "/redir":
            return self._send(302, None, extra={"Location": "/users/1"})
        if p == "/setcookie":
            return self._send(200, {"ok": True}, extra={"Set-Cookie": "sid=abc123; Path=/"})
        if p == "/cookie":
            return self._send(200, {"cookie": self.headers.get("Cookie", "")})
        if p == "/tokhdr":
            if self.headers.get("token") != "abc123":
                return self._send(401, {"error": "token header missing"})
            return self._send(200, {"ok": True})
        if p == "/html":
            return self._send(200, "<h1>Hello</h1><script>1</script>", ctype="text/html")
        if p == "/image":
            import base64
            png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==")
            return self._send(200, png, ctype="image/png")
        if p == "/boom":
            return self._send(500, {"error": "kaboom"})
        if p == "/big":
            return self._send(200, [{"id": i} for i in range(40)])
        if p == "/multi":
            return self._send(200, {"a": [{"x": 1}], "b": [{"y": 2}]})
        if p == "/secure":
            return self._send(200, {"ok": True}) if self._authorized() else self._send(401, {"error": "no"})
        if p == "/slow":
            time.sleep(float(q.get("s", "0.2")))
            return self._send(200, {"slept": True})
        if p.startswith("/status/"):
            return self._send(int(p.split("/")[-1]), {"status": p.split("/")[-1]})
        if p == "/text":
            return self._send(200, "hello world", ctype="text/plain")
        if p == "/flaky":
            STATE["flaky"] += 1
            return self._send(503, {"try": STATE["flaky"]}) if STATE["flaky"] <= 2 else self._send(200, {"try": STATE["flaky"]})
        if p == "/login" and m == "POST":
            return self._send(200, {"access_token": "tok123", "user": {"id": 7}})
        if p == "/me":
            return self._send(200, {"id": 7}) if self.headers.get("Authorization") == "Bearer tok123" else self._send(401, {"error": "no"})
        return self._send(404, {"error": "no route"})

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = route


@pytest.fixture(scope="module")
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture(autouse=True)
def clean(monkeypatch, server, tmp_path):
    monkeypatch.setenv("FYREFLY_API_HOME", str(tmp_path / "fyrefly_api"))
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    for k in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(k, raising=False)
    api.reset()
    STATE["flaky"] = 0
    yield
    api.reset()


# ---- methods ---------------------------------------------------------------------------

def test_get_returns_status_and_json(server, capsys):
    r = api.get(server + "/users/1")
    assert r.status == 200 and r.ok and r.json["name"] == "Asha"
    out = capsys.readouterr().out
    assert "GET" in out and "200 OK" in out and "Asha" in out


def test_every_method_works(server):
    assert api.post(server + "/users", json={"name": "Chen"}, quiet=True).status == 201
    assert api.put(server + "/users/1", json={"name": "A"}, quiet=True).json["method"] == "PUT"
    assert api.patch(server + "/users/1", json={"name": "A"}, quiet=True).json["method"] == "PATCH"
    assert api.delete(server + "/users/1", quiet=True).status == 204
    h = api.head(server + "/users/1", quiet=True)
    assert h.status == 200 and h.text == ""
    assert "GET" in api.options(server + "/users", quiet=True).headers["Allow"]


def test_request_by_name_and_unknown_method(server):
    assert api.request("GET", server + "/users/1", quiet=True).status == 200
    with pytest.raises(ValueError, match="Unknown method"):
        api.request("YEET", server + "/users/1")


def test_call_shortcut_is_get(server):
    assert api(server + "/users/2", quiet=True).json["name"] == "Bilal"


def test_error_statuses_do_not_raise(server):
    r = api.get(server + "/users/99", quiet=True)
    assert r.status == 404 and not r.ok and r.json == {"error": "not found"}


def test_non_json_body(server, capsys):
    r = api.get(server + "/text")
    assert r.json is None and r.text == "hello world"
    assert "hello world" in capsys.readouterr().out


def test_params_and_json_body_are_sent(server):
    r = api.post(server + "/echo", params={"page": 2}, json={"a": 1}, quiet=True)
    assert r.json["query"] == {"page": "2"} and r.json["body"] == {"a": 1}


def test_form_data_is_sent(server):
    r = api.post(server + "/echo", data={"x": "1"}, quiet=True)
    assert r.json["body"] == "x=1"


def test_body_preview_is_truncated(server, capsys):
    api.get(server + "/big")
    long = capsys.readouterr().out
    assert "more lines" in long


# ---- base, headers, auth ---------------------------------------------------------------

def test_base_allows_short_paths(server):
    api.base(server + "/")
    assert api.base() == server
    assert api.get("/users/1", quiet=True).status == 200
    assert api.get("users/1", quiet=True).status == 200


def test_relative_path_without_base_is_a_clear_error():
    with pytest.raises(ValueError, match="api.base"):
        api.get("/users")


def test_default_and_per_call_headers(server):
    api.headers(X_Team="blue")
    r = api.get(server + "/echo", headers={"X-Other": "1"}, quiet=True)
    assert r.json["headers"]["x-team"] == "blue" and r.json["headers"]["x-other"] == "1"


def test_bearer_token_auth(server):
    assert api.get(server + "/secure", quiet=True).status == 401
    assert api.get(server + "/secure", auth="secret", quiet=True).status == 200
    api.auth("secret")
    assert api.get(server + "/secure", quiet=True).status == 200


def test_basic_auth(server):
    assert api.get(server + "/secure", auth=("u", "p"), quiet=True).status == 200
    assert api.get(server + "/secure", auth=("u", "wrong"), quiet=True).status == 401


def test_api_key_header(server):
    assert api.get(server + "/secure", key="k123", quiet=True).status == 200
    api.key("k123")
    assert api.get(server + "/secure", quiet=True).status == 200
    api.key("k123", header="X-Custom")
    assert api.get(server + "/echo", quiet=True).json["headers"]["x-custom"] == "k123"


def test_bad_auth_type_is_rejected(server):
    with pytest.raises(ValueError, match="auth must be"):
        api.get(server + "/secure", auth=123, quiet=True)


def test_reset_clears_everything(server):
    api.base(server); api.auth("secret"); api.headers(A="1")
    api.reset()
    assert api.base() is None and api.auth() is None and api.headers() == {}


def test_last_is_the_latest_result(server):
    api.get(server + "/users/1", quiet=True)
    assert api.last.json["id"] == 1


# ---- errors ----------------------------------------------------------------------------

def test_connection_failure_is_an_apierror():
    with pytest.raises(APIError, match="could not connect"):
        api.get("http://127.0.0.1:1/x", quiet=True)


def test_timeout_is_an_apierror(server):
    with pytest.raises(APIError, match="timed out"):
        api.get(server + "/slow?s=1", timeout=0.1, quiet=True)


def test_retries_recover_from_503(server):
    r = api.get(server + "/flaky", retries=3, quiet=True)
    assert r.status == 200 and r.json["try"] == 3


def test_no_retries_by_default(server):
    assert api.get(server + "/flaky", quiet=True).status == 503


# ---- check -----------------------------------------------------------------------------

def test_check_passes_and_prints(server, capsys):
    r = api.get(server + "/users/1", quiet=True)
    out = r.check(status=200, has=["id", "name"], equals={"name": "Asha"}, header={"content-type": "json"}, max_ms=5000)
    assert out is r and r.passed is True
    text = capsys.readouterr().out
    assert text.count("[PASS]") == 6 and "[FAIL]" not in text


def test_check_reports_failures(server, capsys):
    r = api.get(server + "/users/99", quiet=True)
    r.check(status=200, has="id", equals={"error": "x"}, contains="zzz")
    text = capsys.readouterr().out
    assert r.passed is False
    assert "status is 404, expected 200" in text and "missing 'id'" in text and "expected 'x'" in text and "does not contain" in text


def test_check_status_forms(server):
    r = api.get(server + "/users/1", quiet=True)
    assert r.check(status="2xx", quiet=True).passed
    assert r.check(status=[200, 201], quiet=True).passed
    assert not r.check(status="4xx", quiet=True).passed


def test_check_dotted_paths_and_list_index(server):
    r = api.get(server + "/users", quiet=True)
    assert r.check(has="users.0.name", equals={"users.1.id": 2}, quiet=True).passed
    assert not r.check(has="users.5.name", quiet=True).passed


def test_check_max_ms_fails_when_slow(server):
    r = api.get(server + "/slow?s=0.2", quiet=True)
    assert not r.check(max_ms=50, quiet=True).passed


def test_strict_raises_assertion_error(server):
    r = api.get(server + "/users/99", quiet=True)
    with pytest.raises(AssertionError, match="status is 404"):
        r.check(status=200, strict=True, quiet=True)


def test_check_on_non_json_body_fails_has(server):
    r = api.get(server + "/text", quiet=True)
    assert not r.check(has="x", quiet=True).passed
    assert r.check(contains="hello", quiet=True).passed


def test_get_and_getitem(server):
    r = api.get(server + "/users", quiet=True)
    assert r.get("users.0.name") == "Asha" and r.get("nope", "d") == "d"
    assert len(r["users"]) == 2


# ---- schema ----------------------------------------------------------------------------

def test_schema_valid(server):
    r = api.get(server + "/users/1", quiet=True)
    assert r.schema({"id": int, "name": str, "tags": [str]}, quiet=True) == []


def test_schema_problems_are_specific(server):
    r = api.get(server + "/users/1", quiet=True)
    probs = r.schema({"id": str, "email": str, "tags": [int]}, quiet=True)
    assert "id: expected str, got int" in probs and "email: missing" in probs and "tags[0]: expected int, got str" in probs


def test_schema_optional_nested_and_string_types(server):
    r = api.post(server + "/login", quiet=True)
    assert r.schema({"access_token": "str", "?nickname": str, "user": {"id": "int"}}, quiet=True) == []


def test_schema_bool_is_not_int():
    from fyrefly.api import _validate
    assert _validate(True, int) and not _validate(True, bool)
    assert not _validate(1.5, (int, float)) and not _validate(None, None)


def test_schema_list_of_objects(server):
    r = api.get(server + "/list", quiet=True)
    assert r.schema([{"id": int, "name": str}], quiet=True) == []


def test_schema_on_non_json(server):
    r = api.get(server + "/text", quiet=True)
    assert r.schema({"a": int}, quiet=True) == ["response body is not JSON"]


def test_check_with_schema(server, capsys):
    r = api.get(server + "/users/1", quiet=True)
    assert r.check(schema={"id": int, "name": int}, quiet=True).passed is False


# ---- df --------------------------------------------------------------------------------

def test_df_from_list_of_records(server, capsys):
    frame = api.df(server + "/list")
    assert list(frame.columns) == ["id", "name", "tags"] and len(frame) == 2
    assert "Fetched 2 rows" in capsys.readouterr().out


def test_df_finds_the_only_list_in_an_object(server):
    assert len(api.get(server + "/users", quiet=True).df(quiet=True)) == 2


def test_df_with_path(server):
    assert len(api.df(server + "/users", path="users")) == 2


def test_df_ambiguous_object_gives_hint(server):
    with pytest.raises(ValueError, match="path=.*Lists found at: a, b"):
        api.get(server + "/multi", quiet=True).df(quiet=True)


def test_df_single_object_is_one_row(server):
    frame = api.get(server + "/users/1", quiet=True).df(quiet=True)
    assert len(frame) == 1 and frame["name"].tolist() == ["Asha"]


def test_df_bad_status_raises(server):
    with pytest.raises(APIError, match="404"):
        api.df(server + "/users/99")


def test_df_result_is_queryable_with_sql(server):
    people = api.df(server + "/list")
    out = sql("select name from people where id = 2")
    assert out["name"].tolist() == ["Bilal"]


# ---- curl ------------------------------------------------------------------------------

def test_curl_masks_secrets(server, capsys):
    r = api.post(server + "/users", json={"name": "Z"}, auth="supersecret", quiet=True)
    cmd = r.curl()
    assert "curl -X POST" in cmd and "supersecret" not in cmd and "Authorization: ***" in cmd and '"name": "Z"' in cmd
    assert "supersecret" in r.curl(mask=False)
    assert "User-Agent" not in cmd and "Content-Length" not in cmd and "Content-Type: application/json" in cmd


def test_curl_escapes_single_quotes(server):
    r = api.post(server + "/users", json={"name": "O'Neil"}, quiet=True)
    assert "O'\\''Neil" in r.curl()


# ---- bench -----------------------------------------------------------------------------

def test_bench_reports_stats(server, capsys):
    s = api.bench(server + "/users/1", n=10)
    assert s["n"] == 10 and s["errors"] == 0
    assert s["min"] <= s["median"] <= s["p95"] <= s["max"] and s["rps"] > 0
    assert "p95" in capsys.readouterr().out


def test_bench_counts_errors(server):
    assert api.bench(server + "/users/99", n=5)["errors"] == 5


def test_bench_parallel(server):
    s = api.bench(server + "/slow?s=0.1", n=8, workers=4)
    assert s["errors"] == 0 and s["rps"] > 10  # serial would be ~10 rps; 4 workers is clearly faster


def test_bench_bad_inputs(server):
    with pytest.raises(ValueError):
        api.bench(server, n=0)
    with pytest.raises(APIError):
        api.bench("http://127.0.0.1:1/x", n=2)


def test_bench_with_post_and_options(server):
    assert api.bench(server + "/users", n=3, method="post", json={"name": "x"})["errors"] == 0


# ---- run (test suites) ----------------------------------------------------------------

def test_run_suite_passes_and_chains_saved_values(server, capsys):
    tests = [
        {"name": "login", "method": "post", "url": server + "/login", "expect": {"status": 200, "has": "access_token"},
         "save": {"token": "access_token", "uid": "user.id"}},
        {"name": "me", "url": server + "/me", "headers": {"Authorization": "Bearer {token}"},
         "expect": {"status": 200, "equals": {"id": 7}}},
        {"name": "user", "url": server + "/users/1", "expect": {"schema": {"id": "int", "name": "str"}}},
    ]
    res = api.run(tests)
    assert res["passed"] == 3 and res["failed"] == 0
    out = capsys.readouterr().out
    assert "3 passed, 0 failed" in out and "[PASS] login" in out


def test_run_reports_failures_with_reason(server, capsys):
    res = api.run([{"name": "bad", "url": server + "/users/99", "expect": {"status": 200}}])
    assert res["failed"] == 1 and "status is 404, expected 200" in res["results"][0]["note"]
    assert "[FAIL] bad" in capsys.readouterr().out


def test_run_strict_raises(server):
    with pytest.raises(AssertionError, match="bad"):
        api.run([{"name": "bad", "url": server + "/users/99", "expect": {"status": 200}}], strict=True)


def test_run_survives_a_connection_failure(server):
    res = api.run([{"name": "down", "url": "http://127.0.0.1:1/x"},
                   {"name": "up", "url": server + "/users/1", "expect": {"status": 200}}])
    assert res["passed"] == 1 and res["failed"] == 1


def test_run_missing_saved_value_fails_the_test(server):
    res = api.run([{"name": "x", "url": server + "/users/1", "save": {"t": "nope"}}])
    assert res["failed"] == 1 and "could not save" in res["results"][0]["note"]


def test_run_from_json_file(server, tmp_path):
    f = tmp_path / "t.json"
    f.write_text(json.dumps([{"name": "one", "url": server + "/users/1", "expect": {"status": 200}}]))
    assert api.run(str(f))["passed"] == 1


def test_run_validates_input(server):
    with pytest.raises(ValueError, match="list of dicts"):
        api.run({"url": "x"})
    with pytest.raises(ValueError, match="no 'url'"):
        api.run([{"name": "nourl"}])


def test_run_uses_base(server):
    api.base(server)
    assert api.run([{"name": "short", "url": "/users/1", "expect": {"status": 200}}])["passed"] == 1


def test_run_with_no_expectations_passes_when_it_connects(server):
    assert api.run([{"name": "just call", "url": server + "/users/99"}])["passed"] == 1


# ---- api.test(): the plain-English way --------------------------------------------------

def test_simple_test_working(server, capsys):
    r = api.test(server + "/users/1", look_for=["name", "tags"])
    out = capsys.readouterr().out
    assert r.status == 200
    assert "Testing:  GET" in out and "Status 200. OK. It worked." in out and "Speed:" in out
    assert "data with 3 field(s): id, name, tags" in out
    assert "Found everything you looked for: name, tags" in out and "RESULT: WORKING" in out


def test_simple_test_explains_a_404(server, capsys):
    api.test(server + "/users/99")
    out = capsys.readouterr().out
    assert "[FAIL] Status 404. Not found." in out and "RESULT: PROBLEM (1 issue)" in out


def test_simple_test_401_tells_you_what_to_add(server, capsys):
    api.test(server + "/secure")
    assert 'Add token="..."' in capsys.readouterr().out
    api.test(server + "/secure", token="secret")
    assert "RESULT: WORKING" in capsys.readouterr().out


def test_simple_test_user_and_password_and_key(server, capsys):
    api.test(server + "/secure", user="u", password="p")
    assert "RESULT: WORKING" in capsys.readouterr().out
    api.test(server + "/secure", key="k123")
    assert "RESULT: WORKING" in capsys.readouterr().out


def test_simple_test_post_with_plain_send(server, capsys):
    r = api.test(server + "/users", method="post", send="name=Asha, age=30, admin=yes", expect=201)
    out = capsys.readouterr().out
    assert r.json == {"id": 3, "name": "Asha", "age": 30, "admin": True}
    assert 'Sending:  {"name": "Asha", "age": 30, "admin": true}' in out and "RESULT: WORKING" in out


def test_simple_test_send_accepts_dict_and_json_text(server):
    assert api.test(server + "/users", method="post", send={"a": 1}).json["a"] == 1
    assert api.test(server + "/users", method="post", send='{"b": 2}').json["b"] == 2


def test_simple_test_bad_send_is_explained(server, capsys):
    assert api.test(server + "/users", method="post", send="oops") is None
    assert "needs an equals sign" in capsys.readouterr().out
    assert api.test(server + "/users", method="post", send="{broken") is None
    assert "not valid" in capsys.readouterr().out


def test_simple_test_wrong_expectation(server, capsys):
    api.test(server + "/users/1", expect=201)
    assert "You expected status 201 but got 200" in capsys.readouterr().out


def test_simple_test_missing_field(server, capsys):
    api.test(server + "/users/1", look_for="email")
    assert "Could not find: email" in capsys.readouterr().out


def test_simple_test_list_and_text_summaries(server, capsys):
    api.test(server + "/list")
    assert "list of 2 item(s), each with: id, name, tags" in capsys.readouterr().out
    api.test(server + "/text")
    assert "It sent back text: hello world" in capsys.readouterr().out


def test_simple_test_speed_repeat(server, capsys):
    api.test(server + "/users/1", times=5)
    out = capsys.readouterr().out
    assert "Asked 5 times: average" in out and "0 failure(s)" in out


def test_simple_test_method_inside_the_text(server, capsys):
    r = api.test("DELETE " + server + "/users/1")
    assert r.status == 204 and "Testing:  DELETE" in capsys.readouterr().out


def test_simple_test_unknown_method(server, capsys):
    assert api.test(server + "/users/1", method="fetch") is None
    assert "not a known action" in capsys.readouterr().out


def test_simple_test_adds_https_and_reports_no_answer(capsys):
    assert api.test("127.0.0.1:1/nothing") is None
    out = capsys.readouterr().out
    assert "added https:// for you" in out and "RESULT: PROBLEM" in out and "no answer" in out.lower()


def test_simple_test_uses_base_for_short_paths(server, capsys):
    api.base(server)
    assert api.test("/users/1").status == 200


def test_simple_test_interactive_questions(server, monkeypatch, capsys):
    # questions: url, method, send, (token via getpass), user, look_for, expect, times
    answers = iter([server + "/users", "post", "", "name=Chen", "X-Team: blue", "", "name", "201", "1"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "")
    r = api.test()
    out = capsys.readouterr().out
    assert r.status == 201 and "Let's test an API" in out and "RESULT: WORKING" in out


def test_simple_test_interactive_with_token(server, monkeypatch, capsys):
    answers = iter([server + "/secure", "", "", "", "", "", ""])  # url, method, params, headers, look_for, expect, times
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "secret")
    assert api.test().status == 200
    assert "secret" not in capsys.readouterr().out


def test_simple_test_never_prints_the_token(server, capsys):
    api.test(server + "/secure", token="supersecret")
    assert "supersecret" not in capsys.readouterr().out


def test_simple_test_headers_typed_simply(server, capsys):
    r = api.test(server + "/echo", headers="Accept: application/json; X-Team: blue")
    out = capsys.readouterr().out
    assert r.json["headers"]["x-team"] == "blue" and r.json["headers"]["accept"] == "application/json"
    assert "Headers:  Accept: application/json, X-Team: blue" in out


def test_simple_test_headers_as_dict_and_secrets_hidden(server, capsys):
    api.test(server + "/echo", headers={"X-Api-Key": "topsecret"})
    out = capsys.readouterr().out
    assert "topsecret" not in out and "X-Api-Key: ***" in out


def test_simple_test_bad_headers_explained(server, capsys):
    assert api.test(server + "/echo", headers="oops") is None
    assert "needs a colon" in capsys.readouterr().out


def test_simple_test_header_value_may_contain_commas(server):
    r = api.test(server + "/echo", headers="Accept: text/html, application/json")
    assert r.json["headers"]["accept"] == "text/html, application/json"


def test_simple_test_body_as_web_form(server, capsys):
    r = api.test(server + "/echo", method="post", send="x=1, y=2", form=True)
    assert r.json["body"] in ("x=1&y=2",) and "as a web form" in capsys.readouterr().out


def test_simple_test_headers_and_body_and_token_together(server):
    r = api.test(server + "/echo", method="post", send="a=1", headers="X-Team: blue", token="secret")
    h = r.json["headers"]
    assert r.json["body"] == {"a": 1} and h["x-team"] == "blue" and h["authorization"] == "Bearer secret"


def test_send_keeps_codes_with_leading_zeros_as_text(server):
    r = api.test(server + "/echo", method="post", send="zip=0123, phone=+9199, n=42, price=9.5, pin=\"1234\"")
    assert r.json["body"] == {"zip": "0123", "phone": "+9199", "n": 42, "price": 9.5, "pin": "1234"}


# ---- api.test(): when it fails, it says what to pass, where, and how ---------------------

def fix_text(capsys):
    return capsys.readouterr().out


def test_fix_401_says_token_and_where_it_goes(server, capsys):
    api.test(server + "/secure")
    out = fix_text(capsys)
    assert "HOW TO FIX IT" in out and "needs a login" in out
    assert "Authorization header" in out and 'token="YOUR_TOKEN"' in out
    assert f'api.test("{server}/secure", token="YOUR_TOKEN")' in out


def test_fix_401_basic_scheme_suggests_user_and_password(server, capsys):
    api.test(server + "/basic")
    out = fix_text(capsys)
    assert 'user="YOUR_USERNAME", password="YOUR_PASSWORD"' in out


def test_fix_401_api_key_hint(server, capsys):
    api.test(server + "/apikey")
    out = fix_text(capsys)
    assert 'key="YOUR_API_KEY"' in out and "X-API-Key header" in out


def test_fix_rejected_token_says_it_was_rejected(server, capsys):
    api.test(server + "/secure", token="zzzbadtoken")
    out = fix_text(capsys)
    assert "was rejected" in out and "token=" in out and "zzzbadtoken" not in out


def test_fix_missing_fields_fastapi_style(server, capsys):
    api.test(server + "/validate", method="post", send="name=Asha")
    out = fix_text(capsys)
    assert "missing or not accepted: email" in out and "Where:  the body. Use send=" in out
    assert 'send="name=Asha, email=YOUR_EMAIL"' in out and "Replace each YOUR_..." in out


def test_fix_missing_fields_when_nothing_was_sent(server, capsys):
    api.test(server + "/validate", method="post")
    out = fix_text(capsys)
    assert "name, email" in out and 'send="name=YOUR_NAME, email=YOUR_EMAIL"' in out


def test_fix_rails_style_field_errors(server, capsys):
    api.test(server + "/rails", method="post", send="name=Asha")
    out = fix_text(capsys)
    assert "email, age" in out and "can't be blank" in out


def test_fix_values_not_accepted_when_field_was_sent(server, capsys):
    api.test(server + "/rails", method="post", send="email=bad, age=x")
    out = fix_text(capsys)
    assert "did not accept the value(s) for: email, age" in out and "NEW_EMAIL" in out


def test_fix_missing_header_named(server, capsys):
    api.test(server + "/needheader")
    out = fix_text(capsys)
    assert "asks for a header: X-Tenant-Id" in out and 'headers="X-Tenant-Id: YOUR_VALUE"' in out
    r = api.test(server + "/needheader", headers="X-Tenant-Id: 5")
    assert r.status == 200


def test_fix_404_lists_what_to_check(server, capsys):
    api.test(server + "/nothing-here")
    out = fix_text(capsys)
    assert "Nothing exists at this address" in out and "prefix such as /api or /v1" in out


def test_fix_405_names_the_allowed_methods(server, capsys):
    api.test(server + "/getonly", method="post")
    out = fix_text(capsys)
    assert "accepts: GET, HEAD" in out and 'method="get"' in out


def test_fix_409_and_429_and_500(server, capsys):
    api.test(server + "/conflict", method="post", send="email=a@b.c")
    assert "already exists" in fix_text(capsys)
    api.test(server + "/ratelimit")
    assert "wait 7 second(s)" in fix_text(capsys)
    api.test(server + "/boom")
    out = fix_text(capsys)
    assert "Nothing you pass can fix a server error" in out and 'The server says: "kaboom"' in out


def test_fix_415_toggles_form(server, capsys):
    api.test(server + "/formonly", method="post", send="a=1")
    assert "form=True" in fix_text(capsys)
    assert api.test(server + "/formonly", method="post", send="a=1", form=True).status == 200


def test_fix_connection_failure_explains_and_suggests_http_for_local(capsys):
    api.test("localhost:1/x")
    out = fix_text(capsys)
    assert "Could not reach the address" in out and "http:// instead of https://" in out and 'api.test("http://localhost:1/x")' in out and "HOW TO FIX IT" in out


def test_fix_timeout_suggests_wait(server, capsys):
    api.test(server + "/slow?s=1", wait=0.1)
    out = fix_text(capsys)
    assert "did not answer in time" in out and "wait=60" in out


def test_fix_wrong_expectation_suggests_expect(server, capsys):
    api.test(server + "/users/1", expect=201)
    out = fix_text(capsys)
    assert "You expected 201 but got 200" in out and "expect=200" in out


def test_fix_look_for_lists_real_field_names(server, capsys):
    api.test(server + "/users/1", look_for="email")
    out = fix_text(capsys)
    assert "The answer has these fields: id, name, tags" in out and 'look_for="id"' in out


def test_fix_examples_never_contain_real_secrets(server, capsys):
    api.test(server + "/validate", method="post", send="name=A", headers="X-Api-Key: topsecret", token="supersecret")
    out = fix_text(capsys)
    assert "topsecret" not in out and "supersecret" not in out


def test_fix_params_are_sent_and_shown(server, capsys):
    r = api.test(server + "/echo", params="page=2, limit=10")
    assert r.json["query"] == {"page": "2", "limit": "10"}
    assert "Address extras:  page=2, limit=10" in capsys.readouterr().out


def test_working_run_has_no_fix_section(server, capsys):
    api.test(server + "/users/1")
    assert "HOW TO FIX IT" not in capsys.readouterr().out


def test_fix_example_calls_are_valid_python(server, capsys):
    api.test(server + "/validate", method="post", send="name=Asha", headers="X-Team: blue")
    out = fix_text(capsys)
    import ast
    calls = [ln.split("Try:", 1)[1].strip() for ln in out.splitlines() if "Try:" in ln]
    assert calls
    for c in calls:
        ast.parse(c)


# ======================================================================================
# v0.9: variables, file upload, custom auth header, and the browser window (api.gui)
# ======================================================================================

import base64
import urllib.request
import urllib.error

from fyrefly import _apigui


def _b64(data):
    return base64.b64encode(data).decode()


# ---- variables ---------------------------------------------------------------------------

def test_vars_set_and_read():
    assert api.vars() == {}
    api.vars(HOST="x", N=2)
    api.vars({"A-B": "y"})
    assert api.vars() == {"HOST": "x", "N": 2, "A-B": "y"}
    api.reset()
    assert api.vars() == {}


def test_vars_fill_url_params_headers_body_and_auth(server):
    api.vars(HOST=server, WHO="Asha", TOK="secret", PAGE=3)
    r = api.post("{{HOST}}/echo", params={"page": "{{PAGE}}"}, json={"name": "{{WHO}}", "n": ["{{ WHO }}"]},
                 headers={"X-Who": "{{WHO}}"}, auth="{{TOK}}", quiet=True)
    body = r.json
    assert body["query"] == {"page": "3"}
    assert body["body"] == {"name": "Asha", "n": ["Asha"]}
    assert body["headers"]["x-who"] == "Asha" and body["headers"]["authorization"] == "Bearer secret"


def test_unresolved_variable_raises_with_name(server):
    with pytest.raises(APIError) as e:
        api.get("{{MISSING}}/x", quiet=True)
    assert "{{MISSING}}" in str(e.value) and "api.vars" in str(e.value)


def test_unresolved_variable_in_test_gives_variable_advice(server, capsys):
    assert api.test(server + "/echo", params="a={{NOPE}}") is None
    out = capsys.readouterr().out
    assert "{{NOPE}}" in out and "api.vars(" in out and "Could not reach" not in out


def test_test_accepts_variable_url_without_adding_https(server, capsys):
    api.vars(HOST=server)
    r = api.test("{{HOST}}/users/1")
    out = capsys.readouterr().out
    assert r.status == 200 and "added https://" not in out and f"GET {server}/users/1" in out


def test_variables_stay_in_advice_not_their_values(server, capsys):
    api.vars(HOST=server, SECRETISH="s3cr3t-value")
    api.test("{{HOST}}/validate", method="post", send="x={{SECRETISH}}")
    out = capsys.readouterr().out
    assert "{{HOST}}/validate" in out and "s3cr3t-value" not in out.split("HOW TO FIX IT")[-1]


# ---- file upload -------------------------------------------------------------------------

def test_upload_by_path(server, tmp_path, capsys):
    f = tmp_path / "report.txt"
    f.write_text("hello")
    r = api.test(server + "/upload", method="post", send="groupId=G-1", files=f"file={f}")
    out = capsys.readouterr().out
    assert r.status == 200 and "RESULT: WORKING" in out
    assert r.json["files"]["file"] == {"filename": "report.txt", "size": 5, "type": "text/plain"}
    assert r.json["fields"] == {"groupId": "G-1"}
    assert "file: report.txt, 5 B" in out and "multipart/form-data" in out


def test_upload_with_dict_and_bytes(server):
    r = api.post(server + "/upload", files={"file": ("a.bin", b"\x00\x01\x02")}, quiet=True)
    assert r.json["files"]["file"]["size"] == 3
    r = api.post(server + "/upload", files=[("file", ("b.png", b"xx", "image/png")), ("note", (None, "hi"))], quiet=True)
    assert r.json["files"]["file"]["type"] == "image/png" and r.json["fields"] == {"note": "hi"}


def test_upload_missing_file_is_friendly(server, capsys):
    assert api.test(server + "/upload", method="post", files="file=/no/such/file.pdf") is None
    out = capsys.readouterr().out
    assert "File not found" in out and "/no/such/file.pdf" in out


def test_files_string_needs_equals(server, capsys):
    assert api.test(server + "/upload", method="post", files="report.pdf") is None
    assert "needs an equals sign" in capsys.readouterr().out


def test_upload_advice_asks_for_the_missing_file(server, capsys):
    api.test(server + "/upload", method="post", send="groupId=G-1", files=None)
    out = capsys.readouterr().out
    assert "422" in out or "415" in out
    api.test(server + "/upload", method="post", files={"other": ("o.txt", b"1")})
    out = capsys.readouterr().out
    assert "A file is missing: file." in out and 'files="other=YOUR_FILE_PATH, file=YOUR_FILE_PATH"' in out


def test_file_sent_as_text_is_called_out(server, capsys):
    api.test(server + "/upload", method="post", files=[("file", (None, "oops")), ("groupId", (None, "G-1"))])
    out = capsys.readouterr().out
    assert "should be a file, but it was sent as plain text" in out and 'files="file=YOUR_FILE_PATH"' in out


def test_curl_for_multipart_uses_dash_f(server, tmp_path, capsys):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF")
    r = api.post(server + "/upload", files=[("file", ("doc.pdf", b"%PDF")), ("groupId", (None, "G-1"))], quiet=True)
    cmd = r.curl()
    assert "-F 'file=@doc.pdf'" in cmd and "-F 'groupId=G-1'" in cmd and "Content-Type" not in cmd and "-d " not in cmd


# ---- custom auth header and secret masking ----------------------------------------------

def test_custom_token_header_works_and_is_hidden(server, capsys):
    r = api.test(server + "/tokhdr", headers="token: abc123")
    out = capsys.readouterr().out
    assert r.status == 200 and "abc123" not in out and "token: ***" in out


def test_custom_header_via_key_tuple(server, capsys):
    r = api.test(server + "/tokhdr", key=("token", "abc123"))
    assert r.status == 200 and "abc123" not in capsys.readouterr().out


def test_wrong_custom_header_advice_never_prints_the_value(server, capsys):
    api.test(server + "/tokhdr", headers="token: WRONGVALUE")
    out = capsys.readouterr().out
    assert "WRONGVALUE" not in out and "token: YOUR_VALUE" in out


@pytest.mark.parametrize("name", ["Access-Token", "X-Secret", "Idempotency-Key", "X-Auth-Token", "Cookie", "token"])
def test_secret_header_names_are_masked_in_curl(server, name, capsys):
    r = api.get(server + "/echo", headers={name: "VALUE123"}, quiet=True)
    assert "VALUE123" not in r.curl()
    assert "VALUE123" in r.curl(mask=False)


def test_non_secret_headers_are_not_masked(server, capsys):
    r = api.get(server + "/echo", headers={"X-Team": "blue"}, quiet=True)
    assert "X-Team: blue" in r.curl()


def test_raw_text_body(server, capsys):
    r = api.test(server + "/echo", method="post", send=b"<a>1</a>", headers="Content-Type: application/xml")
    assert r.json["body"] == "<a>1</a>" and "of text" in capsys.readouterr().out


# ---- the window: turning page input into a call -----------------------------------------

def row(k, v="", on=True, **kw):
    return {"on": on, "k": k, "v": v, **kw}


def test_build_call_basics():
    kw, py, v = _apigui.build_call({"method": "post", "url": " https://x.test/u ",
                                     "params": [row("page", "2"), row("off", "1", on=False), row("")],
                                     "headers": [row("X-Team", "blue"), row("X-Team", "red")],
                                     "auth": {"type": "bearer", "token": "TOP-SECRET"},
                                     "body": {"type": "json", "json": '{"name": "Asha", "n": 1}'},
                                     "expect": "201", "look_for": "id, name", "times": 3, "timeout": "20"}, {})
    assert kw["url"] == "https://x.test/u" and kw["method"] == "post"
    assert kw["params"] == {"page": "2"} and kw["headers"] == {"X-Team": "blue, red"}
    assert kw["token"] == "TOP-SECRET" and kw["send"] == {"name": "Asha", "n": 1}
    assert kw["expect"] == 201 and kw["look_for"] == ["id", "name"] and kw["times"] == 3 and kw["wait"] == 20
    assert "TOP-SECRET" not in py and 'token="YOUR_TOKEN"' in py
    import ast
    ast.parse(py)


def test_build_call_auth_kinds():
    base = {"url": "https://x.test"}
    kw, py, _ = _apigui.build_call({**base, "auth": {"type": "basic", "user": "u", "password": "p"}}, {})
    assert (kw["user"], kw["password"]) == ("u", "p") and "p" not in py.replace("password", "").replace("YOUR_PASSWORD", "").replace("api.test", "").replace("https://x.test", "").replace("YOUR_USERNAME", "")
    kw, py, _ = _apigui.build_call({**base, "auth": {"type": "header", "name": "token", "value": "ZZZ"}}, {})
    assert kw["key"] == ("token", "ZZZ") and "ZZZ" not in py
    kw, _, _ = _apigui.build_call({**base, "auth": {"type": "none", "token": "ignored"}}, {})
    assert "token" not in kw and "key" not in kw


def test_build_call_body_kinds():
    kw, _, _ = _apigui.build_call({"url": "u", "body": {"type": "urlencoded", "rows": [row("a", "1"), row("b", "2", on=False)]}}, {})
    assert kw["send"] == {"a": "1"} and kw["form"] is True
    kw, py, _ = _apigui.build_call({"url": "u", "body": {"type": "form", "rows": [
        row("groupId", "G-1"), row("file", kind="file", file={"name": "a.pdf", "type": "application/pdf", "b64": _b64(b"PDF")})]}}, {})
    assert kw["files"] == [("groupId", (None, "G-1")), ("file", ("a.pdf", b"PDF", "application/pdf"))]
    assert 'files="file=YOUR_FILE_PATH"' in py and "groupId=G-1" in py
    kw, py, _ = _apigui.build_call({"url": "u", "method": "post", "body": {"type": "raw", "raw": "<a/>", "rawType": "application/xml"}}, {})
    assert kw["send"] == b"<a/>" and kw["headers"]["Content-Type"] == "application/xml" and "encode()" in py
    kw, _, _ = _apigui.build_call({"url": "u", "body": {"type": "none", "json": '{"a":1}'}}, {})
    assert "send" not in kw


def test_build_call_variables_in_json_text_and_python():
    kw, py, v = _apigui.build_call({"url": "{{HOST}}/x", "variables": [row("HOST", "https://h.test"), row("TOKEN", "abc"), row("N", "5")],
                                     "headers": [row("X-N", "{{N}}")], "auth": {"type": "bearer", "token": "{{TOKEN}}"},
                                     "body": {"type": "json", "json": '{"count": {{N}}}'}}, {})
    assert kw["send"] == {"count": 5} and v["HOST"] == "https://h.test"
    assert 'api.vars(HOST="https://h.test", N="5", TOKEN="YOUR_VALUE")' in py
    assert "abc" not in py


@pytest.mark.parametrize("payload,needle", [
    ({"url": ""}, "Type a web address"),
    ({"url": "u", "body": {"type": "json", "json": "{bad"}}, "not valid"),
    ({"url": "u", "body": {"type": "json", "json": '{"a": {{NOPE}}}'}}, "variable"),
    ({"url": "u", "body": {"type": "form", "rows": [row("f", kind="file")]}}, "no file was chosen"),
    ({"url": "u", "body": {"type": "form", "rows": [row("f", kind="file", file={"name": "a", "b64": "!!!"})]}}, "could not be read"),
    ({"url": "u", "timeout": "abc"}, "number of seconds"),
])
def test_build_call_friendly_errors(payload, needle):
    with pytest.raises(ValueError) as e:
        _apigui.build_call(payload, {})
    assert needle in str(e.value)


def test_make_preset():
    p = _apigui.make_preset(url="https://x.test", method="POST", send="a=1, b=two", headers="X-Team: blue", token="T0K",
                            params="page=2", expect=201, look_for=["id", "name"], times=3, wait=9)
    assert p["method"] == "post" and p["body"]["type"] == "json" and '"a": 1' in p["body"]["json"]
    assert p["headers"] == [{"on": True, "k": "X-Team", "v": "blue"}] and p["params"][0]["k"] == "page"
    assert p["auth"] == {"type": "bearer", "token": "T0K"} and p["expect"] == "201" and p["look_for"] == "id, name"
    assert p["times"] == 3 and p["timeout"] == "9"
    assert _apigui.make_preset(send="a=1", form=True)["body"]["type"] == "urlencoded"
    assert _apigui.make_preset(key=("token", "v"))["auth"] == {"type": "header", "name": "token", "value": "v"}
    assert _apigui.make_preset(user="u", password="p")["auth"]["type"] == "basic"
    assert _apigui.make_preset(send=b"<a/>")["body"]["type"] == "raw"
    assert _apigui.make_preset()["url"] == ""


# ---- the window: the running server ---------------------------------------------------------

@pytest.fixture
def window():
    w = api.gui(open_browser=False, block=False)
    yield w
    w.stop()


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def post_send(window, payload, token=None, headers=None):
    h = {"Content-Type": "application/json", "X-Fyrefly-Token": window.token if token is None else token, **(headers or {})}
    code, hdrs, body = http(f"http://127.0.0.1:{window.port}/send", json.dumps(payload).encode(), h, "POST")
    return code, json.loads(body)


def test_window_listens_on_this_computer_only(window, capsys):
    assert window.httpd.server_address[0] == "127.0.0.1"
    assert window.url.startswith("http://127.0.0.1:") and "?t=" in window.url


def test_window_page_needs_the_secret(window):
    code, hdrs, body = http(window.url)
    assert code == 200 and window.token.encode() in body
    assert http(f"http://127.0.0.1:{window.port}/")[0] == 403
    assert http(f"http://127.0.0.1:{window.port}/?t=wrong")[0] == 403
    assert hdrs["Cache-Control"] == "no-store" and "default-src 'none'" in hdrs["Content-Security-Policy"]
    assert "connect-src 'self'" in hdrs["Content-Security-Policy"]


def test_window_page_works_offline_and_escapes_preset():
    w = api.gui(url="https://x.test/</script><b>", open_browser=False, block=False)
    try:
        page = http(w.url)[2].decode()
        assert "</script><b>" not in page
        import re as _re
        external = [u for u in _re.findall(r"""(?:src|href)=["'](https?://[^"']+)""", page)]
        assert external == [] and "cdn" not in page.lower()
    finally:
        w.stop()


def test_window_rejects_wrong_host_and_foreign_origin(window):
    code, _, _ = http(window.url, headers={"Host": "evil.example"})
    assert code == 403
    code, body = post_send(window, {"url": "x"}, headers={"Origin": "https://evil.example"})
    assert code == 403
    code, body = post_send(window, {"url": "x"}, headers={"Origin": f"http://127.0.0.1:{window.port}"})
    assert code == 200


def test_window_send_needs_the_secret(window):
    assert post_send(window, {"url": "x"}, token="nope")[0] == 403
    assert post_send(window, {"url": "x"}, token="")[0] == 403


def test_window_send_returns_report_and_everything_the_page_shows(window, server):
    code, d = post_send(window, {"method": "get", "url": server + "/list", "look_for": "", "expect": "200"})
    assert code == 200 and d["connected"] and d["status"] == 200 and d["kind"] == "json"
    assert "RESULT: WORKING" in d["report"] and "Status 200" in d["report"]
    assert json.loads(d["pretty"])[0]["name"] == "Asha"
    assert d["table"]["columns"] == ["id", "name", "tags"] and len(d["table"]["data"]) == 2
    assert d["curl"].startswith("curl -X GET") and d["python"].startswith("api.test(")
    assert ["Content-Type", "application/json"] in d["headers"]
    assert d["ms"] >= 0 and d["size"] > 0


def test_window_send_failure_has_advice(window, server):
    code, d = post_send(window, {"method": "post", "url": server + "/validate", "body": {"type": "json", "json": '{"name": "Asha"}'}})
    assert d["status"] >= 400 and "HOW TO FIX IT" in d["report"] and "RESULT: PROBLEM" in d["report"]


def test_window_send_no_answer_and_friendly_errors(window):
    code, d = post_send(window, {"url": "http://127.0.0.1:1/never"})
    assert d["connected"] is False and "Could not reach" in d["report"] and "RESULT: PROBLEM" in d["report"]
    code, d = post_send(window, {"url": ""})
    assert d["connected"] is False and "Type a web address" in d["error"]
    code, d = post_send(window, {"url": "x", "body": {"type": "json", "json": "{bad"}})
    assert "not valid" in d["error"]


def test_window_upload_variables_and_custom_header(window, server):
    code, d = post_send(window, {
        "method": "post", "url": "{{HOST}}/upload", "variables": [row("HOST", server)],
        "body": {"type": "form", "rows": [row("groupId", "G-1"),
                                           row("file", kind="file", file={"name": "doc.txt", "type": "text/plain", "b64": _b64(b"hello")})]}})
    assert d["status"] == 200 and "RESULT: WORKING" in d["report"]
    assert json.loads(d["body"]) == {"fields": {"groupId": "G-1"}, "files": {"file": {"filename": "doc.txt", "size": 5, "type": "text/plain"}}}
    assert "{{HOST}}" in d["python"]
    code, d = post_send(window, {"method": "get", "url": server + "/tokhdr", "auth": {"type": "header", "name": "token", "value": "abc123"}})
    assert d["status"] == 200 and "abc123" not in json.dumps(d)
    assert ["token", "***"] in d["request_headers"]


def test_window_never_leaks_tokens(window, server):
    code, d = post_send(window, {"method": "get", "url": server + "/echo", "auth": {"type": "bearer", "token": "TOP-SECRET-1"},
                                  "headers": [row("X-Api-Key", "TOP-SECRET-2")]})
    blob = json.dumps({k: v for k, v in d.items() if k not in ("body", "pretty", "table")})
    assert "TOP-SECRET-1" not in blob and "TOP-SECRET-2" not in blob
    assert d["status"] == 200


def test_window_variables_do_not_stick(window, server):
    api.vars(KEEP="1")
    post_send(window, {"url": server + "/echo", "variables": [row("TEMP", "2")]})
    assert api.vars() == {"KEEP": "1"}


def test_window_uses_variables_set_in_python(window, server):
    api.vars(HOST=server)
    code, d = post_send(window, {"url": "{{HOST}}/users/1"})
    assert d["status"] == 200


def test_window_kinds_html_image_text(window, server):
    d = post_send(window, {"url": server + "/html"})[1]
    assert d["kind"] == "html" and "<h1>Hello</h1>" in d["body"]
    d = post_send(window, {"url": server + "/image"})[1]
    assert d["kind"] == "image" and d["image"].startswith("data:image/png;base64,")
    d = post_send(window, {"url": server + "/text"})[1]
    assert d["kind"] == "text"
    d = post_send(window, {"method": "delete", "url": server + "/users/1"})[1]
    assert d["status"] == 204 and d["kind"] == "empty"


def test_window_rejects_huge_and_garbled_requests(window):
    h = {"Content-Type": "application/json", "X-Fyrefly-Token": window.token}
    code, _, body = http(f"http://127.0.0.1:{window.port}/send", b"not json", h, "POST")
    assert code == 400 and json.loads(body)["connected"] is False
    code, _, _ = http(f"http://127.0.0.1:{window.port}/nope", b"{}", h, "POST")
    assert code == 404


def test_window_quit_stops_the_server(window):
    code, _, _ = http(f"http://127.0.0.1:{window.port}/quit", b"{}", {"X-Fyrefly-Token": window.token}, "POST")
    assert code == 200
    window._stopped.wait(3)
    with pytest.raises(Exception):
        http(window.url)


def test_window_can_run_twice_on_different_ports():
    a = api.gui(open_browser=False, block=False)
    b = api.gui(open_browser=False, block=False)
    try:
        assert a.port != b.port and a.token != b.token
    finally:
        a.stop(); b.stop()


def test_gui_prints_the_address_and_does_not_open_when_told_not_to(capsys, monkeypatch):
    opened = []
    monkeypatch.setattr(_apigui.webbrowser, "open", lambda u: opened.append(u))
    w = api.gui(open_browser=False, block=False)
    out = capsys.readouterr().out
    assert w.url in out and opened == []
    w.stop()
    w = api.gui(open_browser=True, block=False)
    assert opened == [w.url]
    w.stop()


def test_test_with_gui_true_hands_over_what_you_passed(monkeypatch):
    seen = {}
    monkeypatch.setattr(_apigui, "serve", lambda a, preset, **kw: seen.update(preset=preset, kw=kw) or "window")
    out = api.test("https://x.test/u", method="post", send="a=1", headers="X-Team: blue", token="T0K", gui=True)
    assert out == "window"
    assert seen["preset"]["url"] == "https://x.test/u" and seen["preset"]["method"] == "post"
    assert seen["preset"]["auth"]["token"] == "T0K" and seen["preset"]["body"]["type"] == "json"
    monkeypatch.setattr(api, "_vars", {"HOST": "h"})
    api.gui()
    assert seen["preset"]["variables"] == [{"on": True, "k": "HOST", "v": "h"}]


def test_gui_blocks_until_quit_in_a_script(monkeypatch, capsys):
    monkeypatch.setattr(_apigui.webbrowser, "open", lambda u: None)
    monkeypatch.setattr(_apigui.GuiServer, "wait", lambda self: self.stop())
    assert api.gui(block=True) is None
    assert "Window closed" in capsys.readouterr().out


def test_address_starting_with_unset_variable_is_not_given_https(capsys):
    assert api.test("{{HOST}}/me") is None
    out = capsys.readouterr().out
    assert "added https://" not in out and "No value for {{HOST}}" in out and "api.vars(" in out


# ======================================================================================
# v0.10: SSL/proxy/redirects/cookies, built-in variables, saved work (collections,
# environments, secrets), Postman and curl import/export, and the window's new actions
# ======================================================================================

import os
import re as _re

from fyrefly import _apistore
from fyrefly._apistore import Workspace, blank_request, parse_curl, parse_postman_collection, strip_secrets


# ---- built-in variables -----------------------------------------------------------------------

def test_builtin_guid_is_new_each_time(server):
    r1 = api.get(server + "/echo", params={"id": "{{$guid}}"}, quiet=True)
    r2 = api.get(server + "/echo", params={"id": "{{$guid}}"}, quiet=True)
    a, b = r1.json["query"]["id"], r2.json["query"]["id"]
    uuid_re = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    assert _re.match(uuid_re, a) and _re.match(uuid_re, b) and a != b


def test_builtin_timestamp_iso_and_random_int(server):
    q = api.get(server + "/echo", params={"t": "{{$timestamp}}", "i": "{{$isoTimestamp}}", "n": "{{$randomInt}}", "g": "{{$randomUUID}}"}, quiet=True).json["query"]
    assert abs(int(q["t"]) - time.time()) < 5 and q["i"].endswith("Z") and 0 <= int(q["n"]) <= 1000 and len(q["g"]) == 36


def test_unknown_builtin_is_reported():
    with pytest.raises(APIError) as e:
        api.get("http://127.0.0.1:1/{{$nope}}", quiet=True)
    assert "{{$nope}}" in str(e.value)


# ---- SSL, proxy, redirects, cookies -----------------------------------------------------------

def test_redirects_are_followed_by_default_and_can_be_turned_off(server):
    assert api.get(server + "/redir", quiet=True).status == 200
    api.redirects(False)
    r = api.get(server + "/redir", quiet=True)
    assert r.status == 302 and r.headers["Location"] == "/users/1"
    assert api.redirects() is False
    api.reset()
    assert api.redirects() is True
    assert api.get(server + "/redir", redirects=False, quiet=True).status == 302


def test_redirect_chain_is_available(server):
    r = api.get(server + "/redir", quiet=True)
    assert [h.status_code for h in r.raw.history] == [302]


def test_verify_and_proxy_reach_requests(server, monkeypatch):
    seen = {}
    real = api._session.request

    def fake(method, url, **kw):
        seen.update(kw)
        return real(method, url, **{**kw, "proxies": None})

    monkeypatch.setattr(api._session, "request", fake)
    api.get(server + "/users", quiet=True)
    assert seen["verify"] is True and seen["proxies"] is None
    api.verify(False)
    api.proxy("http://proxy.example:8080")
    api.get(server + "/users", quiet=True)
    assert seen["verify"] is False and seen["proxies"] == {"http": "http://proxy.example:8080", "https": "http://proxy.example:8080"}
    assert api.verify() is False and api.proxy() == "http://proxy.example:8080"
    api.proxy(None)
    assert api.proxy() is None


def test_ssl_error_is_explained(server, monkeypatch, capsys):
    import requests as rq

    def boom(*a, **k):
        raise rq.exceptions.SSLError("certificate verify failed")

    monkeypatch.setattr(api._session, "request", boom)
    assert api.test("https://internal.test/x") is None
    out = capsys.readouterr().out
    assert "SSL certificate" in out and "api.verify(False)" in out and "internal test server" in out
    with pytest.raises(APIError):
        api.get("https://internal.test/x", quiet=True)


def test_test_says_when_ssl_checking_is_off(server, capsys):
    api.verify(False)
    api.test(server + "/users")
    assert "SSL certificate checking is OFF" in capsys.readouterr().out
    api.verify(True)
    api.test(server + "/users")
    assert "OFF" not in capsys.readouterr().out


def test_cookies_are_kept_and_can_be_cleared(server):
    api.get(server + "/setcookie", quiet=True)
    assert api.cookies() == {"sid": "abc123"}
    assert api.get(server + "/cookie", quiet=True).json["cookie"] == "sid=abc123"
    api.cookies(clear=True)
    assert api.cookies() == {} and api.get(server + "/cookie", quiet=True).json["cookie"] == ""


# ---- strip_secrets ----------------------------------------------------------------------------

def test_strip_secrets_keeps_references_and_removes_literals():
    req = blank_request(method="post", url="{{HOST}}/x",
                        auth={"type": "bearer", "token": "LITERAL"},
                        headers=[{"on": True, "k": "X-Api-Key", "v": "LITERAL2"}, {"on": True, "k": "token", "v": "{{TOKEN}}"},
                                 {"on": True, "k": "X-Team", "v": "blue"}, {"on": True, "k": "", "v": ""}],
                        params=[{"on": True, "k": "api_key", "v": "LITERAL3"}],
                        body={"type": "form", "rows": [{"on": True, "k": "file", "v": "", "kind": "file", "file": {"name": "a", "b64": "AAAA"}},
                                                      {"on": True, "k": "password", "v": "LITERAL4", "kind": "text"}, {"on": True, "k": "", "v": ""}]},
                        saves=[{"var": "T", "path": "a"}, {"var": "", "path": ""}])
    req["variables"] = [{"k": "A", "v": "SECRET"}]
    clean, n = strip_secrets(req)
    blob = json.dumps(clean)
    assert n == 4 and not any(x in blob for x in ("LITERAL", "AAAA", "SECRET"))
    assert clean["headers"] == [{"on": True, "k": "X-Api-Key", "v": ""}, {"on": True, "k": "token", "v": "{{TOKEN}}"}, {"on": True, "k": "X-Team", "v": "blue"}]
    assert clean["body"]["rows"][0]["file"] is None and len(clean["body"]["rows"]) == 2
    assert clean["saves"] == [{"var": "T", "path": "a"}]
    assert req["auth"]["token"] == "LITERAL" and req["body"]["rows"][0]["file"]["b64"] == "AAAA"      # the original is untouched


# ---- workspace: environments and secrets ----------------------------------------------------------

def test_environment_roundtrip_and_secret_split(tmp_path):
    ws = Workspace(tmp_path)
    ws.save_env("UAT", [{"k": "HOST", "v": "https://uat.test"}, {"k": "TOKEN", "v": "s3cret-value"}, {"k": "OFF", "v": "x", "on": False}])
    env_file = (tmp_path / "environments" / "UAT.json").read_text()
    assert "https://uat.test" in env_file and "s3cret-value" not in env_file
    secrets = json.loads((tmp_path / "secrets.json").read_text())
    assert secrets == {"UAT": {"TOKEN": "s3cret-value"}}
    if os.name != "nt":
        assert (os.stat(tmp_path / "secrets.json").st_mode & 0o777) == 0o600
    assert "secrets.json" in (tmp_path / ".gitignore").read_text()
    again = Workspace(tmp_path)
    assert again.resolved("UAT") == {"HOST": "https://uat.test", "TOKEN": "s3cret-value"}   # OFF is switched off


def test_state_never_contains_secret_values(tmp_path):
    ws = Workspace(tmp_path)
    ws.save_env("UAT", [{"k": "TOKEN", "v": "s3cret-value"}, {"k": "HOST", "v": "h"}])
    st = ws.state()
    assert "s3cret-value" not in json.dumps(st)
    tok = [r for r in st["envs"]["UAT"] if r["k"] == "TOKEN"][0]
    assert tok["secret"] and tok["v"] == "" and tok["has"] and tok["keep"]


def test_keep_means_the_stored_secret_is_unchanged(tmp_path):
    ws = Workspace(tmp_path)
    ws.save_env("UAT", [{"k": "TOKEN", "v": "one"}])
    ws.save_env("UAT", [{"k": "TOKEN", "v": "", "secret": True, "keep": True}, {"k": "NEW", "v": "n"}])
    assert ws.resolved("UAT")["TOKEN"] == "one"
    ws.save_env("UAT", [{"k": "TOKEN", "v": "two", "secret": True, "keep": False}])
    assert ws.resolved("UAT")["TOKEN"] == "two"
    ws.save_env("UAT", [{"k": "TOKEN", "v": "", "secret": False}])
    assert "TOKEN" not in json.loads((tmp_path / "secrets.json").read_text()).get("UAT", {})


def test_globals_then_active_environment_on_top(tmp_path):
    ws = Workspace(tmp_path)
    ws.save_env("Globals", [{"k": "A", "v": "g"}, {"k": "B", "v": "g"}])
    ws.save_env("SIT", [{"k": "B", "v": "sit"}])
    assert ws.resolved("SIT") == {"A": "g", "B": "sit"} and ws.resolved() == {"A": "g", "B": "g"} and ws.resolved("Nope") == {"A": "g", "B": "g"}


def test_set_var_makes_token_names_secret(tmp_path):
    ws = Workspace(tmp_path)
    env, secret = ws.set_var("Nope", "ACCESS_TOKEN", "abc")
    assert env == "Globals" and secret is True
    assert "abc" not in (tmp_path / "environments" / "Globals.json").read_text()
    assert ws.set_var("Globals", "USER_ID", "7") == ("Globals", False)
    assert ws.resolved()["USER_ID"] == "7"
    with pytest.raises(ValueError):
        ws.set_var("Globals", " ", "x")


def test_environment_management(tmp_path):
    ws = Workspace(tmp_path)
    ws.new_env("UAT")
    with pytest.raises(ValueError):
        ws.new_env("UAT")
    with pytest.raises(ValueError):
        ws.new_env(" ")
    ws.save_env("UAT", [{"k": "TOKEN", "v": "t"}])
    ws.duplicate_env("UAT", "SIT")
    assert ws.resolved("SIT")["TOKEN"] == "t"
    ws.update_settings({"active_env": "SIT"})
    ws.delete_env("SIT")
    assert "SIT" not in ws.envs and ws.settings["active_env"] == "Globals"
    assert not (tmp_path / "environments" / "SIT.json").exists()
    assert "SIT" not in json.loads((tmp_path / "secrets.json").read_text())
    with pytest.raises(ValueError):
        ws.delete_env("Globals")


# ---- workspace: collections, history, settings, safety ---------------------------------------------------

def test_collections_save_overwrite_duplicate_delete_rename(tmp_path):
    ws = Workspace(tmp_path)
    req = blank_request(method="post", url="{{HOST}}/users", auth={"type": "bearer", "token": "LITERAL"})
    rid, n = ws.save_request("Shop", req, "Create user", "Users/Admin")
    assert n == 1 and "LITERAL" not in (tmp_path / "collections" / "Shop.json").read_text()
    rid2, _ = ws.save_request("Shop", {**req, "url": "{{HOST}}/v2"}, rid=rid)
    assert rid2 == rid and len(ws.collections["Shop"]["requests"]) == 1
    entry = ws.collections["Shop"]["requests"][0]
    assert entry["name"] == "Create user" and entry["folder"] == "Users/Admin" and entry["req"]["url"] == "{{HOST}}/v2"
    ws.duplicate_request("Shop", rid)
    assert [r["name"] for r in ws.collections["Shop"]["requests"]] == ["Create user", "Create user copy"]
    ws.delete_request("Shop", rid)
    assert len(ws.collections["Shop"]["requests"]) == 1
    ws.rename_collection("Shop", "Store")
    assert "Store" in ws.collections and (tmp_path / "collections" / "Store.json").exists() and not (tmp_path / "collections" / "Shop.json").exists()
    assert Workspace(tmp_path).collections["Store"]["requests"][0]["name"] == "Create user copy"
    ws.delete_collection("Store")
    assert not (tmp_path / "collections" / "Store.json").exists()
    with pytest.raises(ValueError):
        ws.save_request("", req)
    with pytest.raises(ValueError):
        ws.rename_collection("nope", "x")


def test_default_request_name():
    ws = Workspace(None)
    ws.save_request("C", blank_request(method="get", url="https://x.test/users/42?a=1"))
    ws.save_request("C", blank_request(method="post", url="{{HOST}}"))
    assert [r["name"] for r in ws.collections["C"]["requests"]] == ["GET 42", "POST {{HOST}}"]


def test_file_names_cannot_escape_the_folder(tmp_path):
    ws = Workspace(tmp_path / "w")
    ws.save_request("../../evil", blank_request(url="x"))
    ws.save_env("..\\..\\evil", [{"k": "A", "v": "1"}])
    written = [os.path.relpath(os.path.join(d, f), tmp_path) for d, _, fs in os.walk(tmp_path) for f in fs]
    assert written and all(w.startswith("w" + os.sep) for w in written)


def test_two_names_with_the_same_file_name_do_not_overwrite(tmp_path):
    ws = Workspace(tmp_path)
    ws.new_collection("a/b")
    ws.new_collection("a_b")
    ws.save_request("a/b", blank_request(url="one"))
    ws.save_request("a_b", blank_request(url="two"))
    again = Workspace(tmp_path)
    assert again.collections["a/b"]["requests"][0]["req"]["url"] == "one" and again.collections["a_b"]["requests"][0]["req"]["url"] == "two"


def test_history_is_capped_cleaned_and_clearable(tmp_path):
    ws = Workspace(tmp_path)
    for i in range(105):
        ws.add_history(blank_request(url=f"u{i}", auth={"type": "bearer", "token": "TOPSECRET"}), 200, 5)
    assert len(ws.history) == _apistore.MAX_HISTORY and ws.history[0]["req"]["url"] == "u104"
    assert "TOPSECRET" not in (tmp_path / "history.json").read_text()
    assert "history.json" in (tmp_path / ".gitignore").read_text()
    ws.clear_history()
    assert Workspace(tmp_path).history == []


def test_settings_persist_and_ignore_unknown_keys(tmp_path):
    ws = Workspace(tmp_path)
    ws.update_settings({"verify": 0, "redirects": 1, "proxy": "http://p:1", "timeout": "9", "evil": "x", "active_env": "UAT"})
    again = Workspace(tmp_path)
    assert again.settings == {"verify": False, "redirects": True, "proxy": "http://p:1", "timeout": "9", "active_env": "UAT"}
    assert "evil" not in again.settings


def test_corrupt_files_are_reported_not_fatal(tmp_path):
    (tmp_path / "collections").mkdir()
    (tmp_path / "collections" / "bad.json").write_text("{not json")
    (tmp_path / "settings.json").write_text("[]")
    ws = Workspace(tmp_path)
    assert any("bad.json" in p for p in ws.problems) and ws.collections == {}
    assert (tmp_path / "collections" / "bad.json").read_text() == "{not json"       # left untouched


def test_memory_only_workspace_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ws = Workspace(None)
    ws.save_env("UAT", [{"k": "TOKEN", "v": "t"}])
    ws.save_request("C", blank_request(url="x"))
    ws.add_history(blank_request(url="x"), 200, 1)
    ws.update_settings({"verify": False})
    assert os.listdir(tmp_path) == [] and ws.resolved("UAT") == {"TOKEN": "t"} and ws.state()["persist"] is False


def test_default_folder_uses_environment_variable(monkeypatch, tmp_path):
    monkeypatch.setenv("FYREFLY_API_HOME", str(tmp_path / "x"))
    assert _apistore.default_folder() == str(tmp_path / "x")
    monkeypatch.delenv("FYREFLY_API_HOME")
    assert _apistore.default_folder().endswith("fyrefly_api")


# ---- curl --------------------------------------------------------------------------------------------------

def test_curl_json_post():
    p = parse_curl("""curl -X POST 'https://a.test/users?x=1&y=two' \\
        -H 'Authorization: Bearer TOK' -H 'Content-Type: application/json' -H 'X-Team: blue' \\
        -d '{"name": "Asha", "age": 30}'""")
    r = p["req"]
    assert r["method"] == "post" and r["url"] == "https://a.test/users"
    assert [(x["k"], x["v"]) for x in r["params"]] == [("x", "1"), ("y", "two")]
    assert r["auth"] == {"type": "bearer", "token": "TOK"} and [(h["k"], h["v"]) for h in r["headers"]] == [("X-Team", "blue")]
    assert r["body"]["type"] == "json" and json.loads(r["body"]["json"]) == {"name": "Asha", "age": 30}


def test_curl_defaults_and_flags():
    assert parse_curl("curl https://a.test/x")["req"]["method"] == "get"
    assert parse_curl("curl https://a.test/x -d a=1")["req"]["method"] == "post"
    assert parse_curl("curl -I https://a.test/x")["req"]["method"] == "head"
    r = parse_curl("curl -sSLk https://a.test/x")
    assert r["req"]["verify"] is False and r["req"]["redirects"] is None
    assert parse_curl("curl https://a.test/x")["req"]["redirects"] is False        # curl does not follow redirects without -L
    g = parse_curl("curl -G https://a.test/x -d q=1 -d r=2")["req"]
    assert g["method"] == "get" and [(p["k"], p["v"]) for p in g["params"]] == [("q", "1"), ("r", "2")] and g["body"]["type"] == "none"
    assert parse_curl("curl --url=https://a.test/x --max-time 9")["req"]["timeout"] == "9"


def test_curl_auth_forms_and_cookie():
    r = parse_curl("curl https://a.test -u me:pw -b 'a=1; b=2' -A MyAgent")["req"]
    assert r["auth"] == {"type": "basic", "user": "me", "password": "pw"}
    assert {h["k"]: h["v"] for h in r["headers"]} == {"Cookie": "a=1; b=2", "User-Agent": "MyAgent"}
    import base64 as b64
    r = parse_curl(f"curl https://a.test -H 'Authorization: Basic {b64.b64encode(b'u:p').decode()}'")["req"]
    assert r["auth"] == {"type": "basic", "user": "u", "password": "p"}
    r = parse_curl("curl https://a.test -H 'Authorization: Token abc'")["req"]
    assert r["auth"] == {"type": "none"} and r["headers"][0]["k"] == "Authorization"


def test_curl_bodies():
    r = parse_curl("curl https://a.test -d 'a=1&b=hello%20there'")["req"]["body"]
    assert r["type"] == "urlencoded" and [(x["k"], x["v"]) for x in r["rows"]] == [("a", "1"), ("b", "hello there")]
    r = parse_curl("curl https://a.test -H 'Content-Type: application/xml' -d '<a>1</a>'")["req"]
    assert r["body"] == {"type": "raw", "raw": "<a>1</a>", "rawType": "application/xml"} and r["headers"] == []
    r = parse_curl("curl https://a.test -H 'Content-Type: application/json' -d '{bad'")["req"]["body"]
    assert r["type"] == "raw" and r["raw"] == "{bad"
    p = parse_curl("curl https://a.test -F g=1 -F 'file=@/tmp/a.pdf;type=application/pdf'")
    rows = p["req"]["body"]["rows"]
    assert p["req"]["body"]["type"] == "form" and rows[1]["kind"] == "file" and rows[1]["fileName"] == "/tmp/a.pdf" and rows[0]["v"] == "1"
    assert any("Choose that file again" in n for n in p["notes"])
    assert any("file" in n for n in parse_curl("curl https://a.test -d @body.json")["notes"])


@pytest.mark.parametrize("text,needle", [("curl", "No web address"), ("curl https://a.test -H 'x", "unclosed quote"), ("curl https://a.test -X", "needs a value")])
def test_curl_errors(text, needle):
    with pytest.raises(ValueError) as e:
        parse_curl(text)
    assert needle in str(e.value)


def test_curl_unknown_option_is_noted_not_fatal():
    assert any("--weird" in n for n in parse_curl("curl --weird https://a.test")["notes"])


def test_from_curl_prints_the_fyrefly_call(capsys):
    code = api.from_curl("curl -X POST https://a.test/u -H 'Authorization: Bearer REAL' -H 'Content-Type: application/json' -d '{\"n\": 1}' -k")
    out = capsys.readouterr().out
    assert code.startswith("api.verify(False)\napi.test(") and "REAL" not in out and 'token="YOUR_TOKEN"' in code and "turned off" in out
    import ast
    ast.parse(code)
    assert 'files="file=YOUR_FILE_PATH"' in api.from_curl("curl https://a.test/up -F file=@a.pdf")


# ---- Postman --------------------------------------------------------------------------------------------------

POSTMAN = {
    "info": {"name": "Shop API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
    "variable": [{"key": "host", "value": "https://shop.test"}, {"key": "apiToken", "value": "abc"}],
    "auth": {"type": "bearer", "bearer": [{"key": "token", "value": "{{apiToken}}"}]},
    "event": [{"listen": "prerequest", "script": {"exec": ["x"]}}],
    "item": [
        {"name": "Users", "item": [
            {"name": "List", "request": {"method": "GET", "url": {"raw": "{{host}}/users/:id?x=1", "query": [{"key": "x", "value": "1"}, {"key": "off", "value": "2", "disabled": True}],
                                                                "variable": [{"key": "id", "value": "7"}]}}},
            {"name": "Create", "event": [{"listen": "test", "script": {"exec": ["y"]}}],
             "request": {"method": "POST", "header": [{"key": "X-Team", "value": "blue"}, {"key": "Content-Type", "value": "application/json"}],
                         "body": {"mode": "raw", "raw": "{\"name\": \"Asha\"}", "options": {"raw": {"language": "json"}}}, "url": "{{host}}/users",
                         "auth": {"type": "apikey", "apikey": [{"key": "key", "value": "token"}, {"key": "value", "value": "LITERAL-KEY"}, {"key": "in", "value": "header"}]}}},
        ]},
        {"name": "Upload", "request": {"method": "POST", "auth": {"type": "noauth"},
                                       "body": {"mode": "formdata", "formdata": [{"key": "g", "value": "1", "type": "text"}, {"key": "file", "type": "file", "src": "/x/a.pdf"}]},
                                       "url": {"raw": "{{host}}/upload"}}},
        {"name": "Form", "request": {"method": "POST", "body": {"mode": "urlencoded", "urlencoded": [{"key": "a", "value": "1"}, {"key": "b", "value": "2", "disabled": True}]},
                                     "url": "{{host}}/f?k=v"}},
        {"name": "Gql", "request": {"method": "POST", "body": {"mode": "graphql", "graphql": {"query": "{ me { id } }", "variables": "{\"a\": 1}"}}, "url": "{{host}}/graphql"}},
        {"name": "Oauth", "request": {"method": "GET", "auth": {"type": "oauth2"}, "url": "{{host}}/o"}},
        {"name": "Bin", "request": {"method": "PUT", "body": {"mode": "file", "file": {"src": "x"}}, "url": "{{host}}/b"}},
        {"name": "Short", "request": "https://short.test/s"},
    ],
}


def test_postman_collection_is_parsed():
    p = parse_postman_collection(POSTMAN)
    by = {r["name"]: r for r in p["requests"]}
    assert p["name"] == "Shop API" and len(p["requests"]) == 8
    lst = by["List"]
    assert lst["folder"] == "Users" and lst["req"]["url"] == "{{host}}/users/7"                  # :id filled from the path variable
    assert [(x["k"], x["on"]) for x in lst["req"]["params"]] == [("x", True), ("off", False)]
    assert lst["req"]["auth"] == {"type": "bearer", "token": "{{apiToken}}"}                    # inherited from the collection
    cr = by["Create"]["req"]
    assert cr["body"]["type"] == "json" and [h["k"] for h in cr["headers"]] == ["X-Team"]       # Content-Type is implied by the body
    assert cr["auth"] == {"type": "header", "name": "token", "value": "LITERAL-KEY"}
    up = by["Upload"]["req"]
    assert up["auth"] == {"type": "none"} and up["body"]["rows"][1]["kind"] == "file" and up["body"]["rows"][1]["fileName"] == "/x/a.pdf"
    fm = by["Form"]["req"]
    assert fm["body"]["type"] == "urlencoded" and fm["body"]["rows"][1]["on"] is False and fm["params"][0]["k"] == "k"
    assert json.loads(by["Gql"]["req"]["body"]["json"]) == {"query": "{ me { id } }", "variables": {"a": 1}}
    assert by["Short"]["req"]["url"] == "https://short.test/s"
    notes = " ".join(p["notes"])
    assert "oauth2" in notes and "binary" in notes and "script" in notes
    assert {v["k"]: v["secret"] for v in p["variables"]} == {"host": False, "apiToken": True}


def test_postman_import_into_workspace(tmp_path):
    ws = Workspace(tmp_path)
    res = ws.import_text(json.dumps(POSTMAN))
    assert res["kind"] == "collection" and res["requests"] == 8 and res["environment"] == "Shop API variables"
    assert any("not saved to disk" in n for n in res["notes"])
    assert "LITERAL-KEY" not in (tmp_path / "collections" / "Shop API.json").read_text()
    assert ws.resolved("Shop API variables") == {"host": "https://shop.test", "apiToken": "abc"}
    assert "abc" not in (tmp_path / "environments" / "Shop API variables.json").read_text()
    assert ws.import_text(json.dumps(POSTMAN))["collection"] == "Shop API (imported)"           # never overwrites


def test_postman_environment_import_and_export(tmp_path):
    ws = Workspace(tmp_path)
    res = ws.import_text(json.dumps({"name": "UAT", "values": [
        {"key": "host", "value": "https://uat.test", "enabled": True}, {"key": "pw", "value": "hunter2", "type": "secret"},
        {"key": "off", "value": "x", "enabled": False}]}))
    assert res["kind"] == "environment" and res["variables"] == 3
    assert ws.resolved("UAT") == {"host": "https://uat.test", "pw": "hunter2"}
    exported = ws.export_env("UAT")
    assert "hunter2" not in json.dumps(exported) and [v["type"] for v in exported["values"]] == ["default", "secret", "default"]
    with pytest.raises(ValueError):
        ws.export_env("nope")


def test_collection_export_roundtrips_through_postman_format(tmp_path):
    ws = Workspace(tmp_path)
    ws.import_text(json.dumps(POSTMAN))
    out = ws.export_collection("Shop API")
    assert out["info"]["schema"].endswith("collection.json") and [i["name"] for i in out["item"]][0] == "Users"
    assert "LITERAL-KEY" not in json.dumps(out)
    ws2 = Workspace(tmp_path / "second")
    res = ws2.import_text(json.dumps(out))
    assert res["requests"] == 8
    a = {r["name"]: r["req"] for r in ws.collections["Shop API"]["requests"]}
    b = {r["name"]: r["req"] for r in ws2.collections["Shop API"]["requests"]}
    for name in ("List", "Create", "Form", "Upload"):
        assert (a[name]["method"], a[name]["url"], a[name]["body"]["type"]) == (b[name]["method"], b[name]["url"], b[name]["body"]["type"])
    with pytest.raises(ValueError):
        ws.export_collection("nope")


@pytest.mark.parametrize("text,needle", [("", "Paste something"), ("hello", "not JSON"), ("[1]", "not a Postman"), ('{"a": 1}', "not a Postman")])
def test_import_errors_are_friendly(text, needle):
    with pytest.raises(ValueError) as e:
        Workspace(None).import_text(text)
    assert needle in str(e.value)


def test_import_curl_text_returns_a_request_to_open():
    r = Workspace(None).import_text("curl https://a.test/x -H 'Authorization: Bearer T'")
    assert r["kind"] == "curl" and r["open"][0]["auth"]["token"] == "T"


def test_import_postman_from_python(tmp_path, capsys):
    f = tmp_path / "c.json"
    f.write_text(json.dumps(POSTMAN))
    res = api.import_postman(str(f), folder=tmp_path / "home")
    out = capsys.readouterr().out
    assert res["requests"] == 8 and "Imported collection 'Shop API': 8 request(s)" in out and (tmp_path / "home" / "collections" / "Shop API.json").exists()


# ---- the window: new actions ----------------------------------------------------------------------------------------

@pytest.fixture
def win(tmp_path):
    w = api.gui(open_browser=False, block=False, folder=tmp_path / "ws")
    w.home = tmp_path / "ws"
    yield w
    w.stop()


def op(w, action, /, **data):
    code, hdrs, body = http(f"http://127.0.0.1:{w.port}/op", json.dumps({"op": action, **data}).encode(),
                            {"Content-Type": "application/json", "X-Fyrefly-Token": w.token}, "POST")
    assert code == 200
    return json.loads(body)


def test_op_needs_the_secret(win):
    code, _, _ = http(f"http://127.0.0.1:{win.port}/op", b'{"op": "state"}', {"X-Fyrefly-Token": "nope"}, "POST")
    assert code == 403
    code, _, _ = http(f"http://127.0.0.1:{win.port}/op", b'{"op": "state"}', {}, "POST")
    assert code == 403


def test_gui_folder_options(tmp_path):
    w = api.gui(open_browser=False, block=False, folder=False)
    try:
        assert op(w, "state")["state"]["persist"] is False
    finally:
        w.stop()
    w = api.gui(open_browser=False, block=False)               # default: FYREFLY_API_HOME from the test fixture
    try:
        assert op(w, "state")["state"]["folder"] == str(tmp_path / "fyrefly_api") or "fyrefly_api" in op(w, "state")["state"]["folder"]
    finally:
        w.stop()


def test_op_environments_and_masking(win):
    assert op(win, "env_new", name="UAT")["state"]["envs"]["UAT"] == []
    assert "already" in op(win, "env_new", name="UAT")["error"]
    st = op(win, "env_save", name="UAT", rows=[{"k": "HOST", "v": "h"}, {"k": "TOKEN", "v": "tok-secret"}])["state"]
    assert "tok-secret" not in json.dumps(st)
    assert "Globals cannot be deleted" in op(win, "env_delete", name="Globals")["error"]
    assert "UAT" not in op(win, "env_delete", name="UAT")["state"]["envs"]
    assert "Unknown action" in op(win, "dance")["error"]


def test_op_save_open_and_secret_warning(win):
    req = blank_request(method="post", url="{{HOST}}/x", auth={"type": "bearer", "token": "LITERAL"})
    d = op(win, "req_save", collection="Shop", name="Create", folder="A/B", req=req)
    assert d["stripped"] == 1 and d["rid"]
    c = d["state"]["collections"][0]
    assert c["name"] == "Shop" and c["requests"][0]["folder"] == "A/B" and c["requests"][0]["req"]["auth"]["token"] == ""
    assert "LITERAL" not in (win.home / "collections" / "Shop.json").read_text()
    assert "required" in op(win, "req_save", collection="", req=req)["error"] or "Choose" in op(win, "req_save", collection="", req=req)["error"]
    st = op(win, "req_delete", collection="Shop", rid=d["rid"])["state"]
    assert st["collections"][0]["requests"] == []
    assert op(win, "coll_rename", name="Shop", new_name="Store")["state"]["collections"][0]["name"] == "Store"
    assert op(win, "coll_delete", name="Store")["state"]["collections"] == []


def test_op_import_export(win):
    d = op(win, "import", text=json.dumps(POSTMAN))
    assert d["result"]["requests"] == 8 and d["state"]["collections"][0]["name"] == "Shop API"
    assert op(win, "export_coll", name="Shop API")["data"]["info"]["name"] == "Shop API"
    assert op(win, "export_env", name="Shop API variables")["data"]["values"][0]["key"] == "host"
    assert op(win, "import", text="curl https://a.test")["result"]["open"][0]["url"] == "https://a.test"
    assert "not JSON" in op(win, "import", text="nope")["error"]
    assert "does not exist" in op(win, "export_coll", name="zzz")["error"]


def test_save_to_variable_logs_in_and_the_next_call_uses_it(win, server):
    login = blank_request(method="post", url=server + "/login", saves=[{"var": "ACCESS_TOKEN", "path": "access_token"}, {"var": "UID", "path": "user.id"},
                                                                         {"var": "NOPE", "path": "missing.path"}])
    op(win, "env_new", name="UAT")
    code, d = post_send(win, {**login, "env": "UAT"})
    assert code == 200 and d["status"] == 200
    by = {x["k"]: x for x in d["saved"]}
    assert by["ACCESS_TOKEN"]["secret"] is True and by["ACCESS_TOKEN"]["value"] == "" and by["UID"]["value"] == "7" and by["UID"]["env"] == "UAT"
    assert "was not found" in by["NOPE"]["error"]
    assert "tok123" not in json.dumps(d["saved"]) and "tok123" not in d["report"]       # the answer itself shows it; the "saved" notice does not
    assert "tok123" not in (win.home / "environments" / "UAT.json").read_text()
    assert json.loads((win.home / "secrets.json").read_text())["UAT"]["ACCESS_TOKEN"] == "tok123"
    code, d = post_send(win, {"method": "get", "url": server + "/me", "auth": {"type": "bearer", "token": "{{ACCESS_TOKEN}}"}, "env": "UAT"})
    assert d["status"] == 200 and "RESULT: WORKING" in d["report"] and "tok123" not in json.dumps(d)
    code, d = post_send(win, {"method": "get", "url": server + "/me", "auth": {"type": "bearer", "token": "{{ACCESS_TOKEN}}"}, "env": "Globals"})
    assert "status" not in d and "No value for {{ACCESS_TOKEN}}" in (d.get("report") or "") + (d.get("error") or "")


def test_save_from_header_status_and_body(win, server):
    code, d = post_send(win, {"url": server + "/redir", "redirects": False,
                              "saves": [{"var": "WHERE", "path": "header:Location"}, {"var": "CODE", "path": "status"}]})
    assert d["status"] == 302 and {x["k"]: x["value"] for x in d["saved"]} == {"WHERE": "/users/1", "CODE": "302"}
    code, d = post_send(win, {"url": server + "/text", "saves": [{"var": "ALL", "path": "body"}]})
    assert d["saved"][0]["k"] == "ALL" and d["saved"][0]["value"]


def test_environment_variables_are_used_without_being_sent_by_the_page(win, server):
    op(win, "env_save", name="SIT", rows=[{"k": "HOST", "v": server}])
    code, d = post_send(win, {"url": "{{HOST}}/users/1", "env": "SIT"})
    assert d["status"] == 200 and d["env"] == "SIT"
    op(win, "settings", settings={"active_env": "SIT"})
    code, d = post_send(win, {"url": "{{HOST}}/users/1"})                          # no env sent: the saved active one is used
    assert d["status"] == 200


def test_settings_apply_to_the_send_and_are_put_back(win, server):
    op(win, "settings", settings={"verify": False, "redirects": False, "timeout": "7"})
    code, d = post_send(win, {"url": server + "/redir"})
    assert d["status"] == 302 and "SSL certificate checking is OFF" in d["report"] and d["redirects"] == []
    assert api.verify() is True and api.redirects() is True and api.proxy() is None               # the window never changes your session
    code, d = post_send(win, {"url": server + "/redir", "redirects": True, "verify": True})
    assert d["status"] == 200 and "OFF" not in d["report"] and d["redirects"] == [[302, server + "/redir"]]


def test_history_is_recorded_without_secrets(win, server):
    post_send(win, {"url": server + "/me", "auth": {"type": "bearer", "token": "LITERAL-TOKEN"}})
    st = op(win, "state")["state"]
    assert st["history"][0]["status"] == 401 and st["history"][0]["req"]["url"].endswith("/me")
    assert "LITERAL-TOKEN" not in json.dumps(st) and "LITERAL-TOKEN" not in (win.home / "history.json").read_text()
    assert op(win, "history_clear")["state"]["history"] == []


def test_download_returns_the_exact_bytes(win, server):
    code, d = post_send(win, {"url": server + "/image"})
    got = op(win, "body", rid=d["rid"])
    assert base64.b64decode(got["b64"])[:4] == b"\x89PNG" and got["content_type"] == "image/png"
    assert "no longer kept" in op(win, "body", rid="zzz")["error"]
    rids = [post_send(win, {"url": server + "/users"})[1]["rid"] for _ in range(8)]
    assert "no longer kept" in op(win, "body", rid=rids[0])["error"] and "b64" in op(win, "body", rid=rids[-1])


def test_cookies_clear_op(win, server):
    api.get(server + "/setcookie", quiet=True)
    assert api.cookies()
    op(win, "cookies_clear")
    assert api.cookies() == {}


def test_page_ships_the_new_features_and_no_outside_links():
    from fyrefly._apipage import PAGE
    for word in ("Environment", "Save to variable", "Import", "Settings", "Download", "Run:", "to var", "Find in the answer"):
        assert word in PAGE
    assert not _re.findall(r"""(?:src|href)=["']https?://""", PAGE) and "cdn" not in PAGE.lower()


# ---------------------------------------------------------------------------------------------
# Public surface: api.gui() is the only public API function
# ---------------------------------------------------------------------------------------------
def test_public_api_is_only_gui():
    import fyrefly
    assert dir(public_api) == ["gui"]
    assert callable(public_api.gui)
    assert fyrefly.api is public_api
    assert "APIError" not in fyrefly.__all__


@pytest.mark.parametrize("name", ["test", "get", "post", "bench", "run", "vars", "from_curl", "import_postman", "df", "base"])
def test_other_api_functions_are_not_public(name):
    with pytest.raises(AttributeError, match="only one function"):
        getattr(public_api, name)


def test_window_text_points_at_tabs_and_drops_python():
    from fyrefly import _apigui
    raw = ("HOW TO FIX IT\n  1. These fields are missing or not accepted: email.\n     Where:  the body. Use send=\n"
           '     Try:    api.test("x", send="a=1")\n     Note:   Replace each YOUR_... with a real value.\n')
    out = _apigui.window_text(raw)
    assert "Where:  the Body tab" in out and "api.test" not in out and "Try:" not in out and "Replace each" not in out
    assert "Variables tab" in _apigui.window_text("No value for {{TOKEN}}. Give each one a value with api.vars(TOKEN=\"...\").")


def test_window_shows_no_python_calls(server):
    ws = Workspace(None)
    for payload in [{"url": "{{HOST}}/x", "method": "get"},
                    {"url": server + "/validate", "method": "post", "body": {"type": "json", "json": '{"name": "A"}'}},
                    {"url": server + "/secure", "method": "get"}]:
        d = _apigui.run_payload(api, threading.RLock(), payload, ws)
        text = (d.get("report") or "") + (d.get("error") or "")
        assert "api." not in text and "Try:" not in text, text


def test_script_window_waits_even_if_ipykernel_is_imported(monkeypatch, tmp_path):
    """A plain terminal with ipykernel merely loaded must still keep the window alive."""
    import sys, types
    monkeypatch.setitem(sys.modules, "ipykernel", types.ModuleType("ipykernel"))
    assert _apigui._in_notebook() is False
    seen = {}

    class Fake:
        url = "http://127.0.0.1:1/?t=x"

        def wait(self):
            seen["waited"] = True

    monkeypatch.setattr(_apigui.GuiServer, "start", lambda self: Fake())
    _apigui.serve(api, None, 0, False, None, False)
    assert seen.get("waited") is True