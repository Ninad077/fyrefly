import os
import inspect
import pandas as pd
import duckdb
import requests


def _describe_schema(dataframes):
    """Builds a plain-text schema description of all loaded DataFrames for the LLM prompt."""
    lines = []
    for name, df in dataframes.items():
        cols = ", ".join(f"{col} ({dtype})" for col, dtype in df.dtypes.items())
        lines.append(f"Table '{name}': {cols}")
    return "\n".join(lines)


def _clean_sql(text):
    """Strips markdown code fences and extra whitespace/labels from a model's raw response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        lines = text.split("\n")
        if lines and lines[0].strip().lower() in ("sql", "sqlite", "duckdb"):
            lines = lines[1:]
        text = "\n".join(lines).strip()
    # Some models prefix with "SQL:" or similar
    for prefix in ("SQL:", "sql:", "Query:", "query:"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    return text.rstrip(";").strip()


def _build_prompt(question, schema_description):
    return (
        "You are a SQL generator. Given the table schema(s) below, write a single "
        "valid SQL query (DuckDB dialect) that answers the user's question. "
        "Return ONLY the raw SQL query — no explanation, no markdown formatting, no backticks.\n\n"
        f"Schema:\n{schema_description}\n\n"
        f"Question: {question}\n\n"
        "SQL:"
    )


def _detect_provider(api_key):
    """
    Guesses the provider from the API key's format. Order matters —
    check the most specific prefixes before more generic ones.
    """
    if api_key.startswith("sk-ant-"):
        return "anthropic", None
    if api_key.startswith("AIza"):
        return "gemini", None
    if api_key.startswith("gsk_"):
        return "openai_compatible", "https://api.groq.com/openai/v1"
    if api_key.startswith("sk-"):
        return "openai", None
    raise ValueError(
        "Couldn't auto-detect the provider from this API key's format. "
        "Please specify it explicitly, e.g. ask(question, provider=\"openai\", api_key=\"...\")"
    )


def _call_anthropic(prompt, api_key, model):
    model = model or "claude-haiku-4-5-20251001"
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"]


def _call_openai(prompt, api_key, model, base_url=None):
    model = model or "gpt-4o-mini"
    url = f"{(base_url or 'https://api.openai.com/v1').rstrip('/')}/chat/completions"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_gemini(prompt, api_key, model):
    model = model or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    response = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_llm(prompt, provider, api_key, model, base_url):
    """Dispatches a prompt to the given provider and returns the raw text response."""
    provider = provider.lower()

    if provider == "anthropic":
        return _call_anthropic(prompt, api_key, model)
    elif provider == "openai":
        return _call_openai(prompt, api_key, model)
    elif provider in ("gemini", "google"):
        return _call_gemini(prompt, api_key, model)
    elif provider == "openai_compatible":
        if not base_url:
            raise ValueError("provider='openai_compatible' requires base_url=\"...\"")
        if not model:
            raise ValueError("provider='openai_compatible' requires model=\"...\"")
        return _call_openai(prompt, api_key, model, base_url=base_url)
    else:
        raise ValueError(
            f"Unsupported provider '{provider}'. "
            "Supported: anthropic, openai, gemini, openai_compatible"
        )


def _resolve_provider_and_key(api_key=None, provider=None, base_url=None):
    """
    Resolves the API key (from argument or environment variable) and,
    if provider wasn't specified, auto-detects it from the key's format.
    Shared by ask() and insights().
    """
    if not api_key:
        for env_var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
            if os.environ.get(env_var):
                api_key = os.environ[env_var]
                break
    if not api_key:
        raise ValueError(
            "No API key found. Pass api_key=\"...\" or set one of: "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY"
        )

    if not provider:
        detected_provider, detected_base_url = _detect_provider(api_key)
        provider = detected_provider
        base_url = base_url or detected_base_url
        print(f"Detected provider: {provider}")

    return provider, api_key, base_url


def _generate_sql(question, schema_description, provider, api_key, model, base_url):
    prompt = _build_prompt(question, schema_description)
    raw = _call_llm(prompt, provider, api_key, model, base_url)
    return _clean_sql(raw)


def _describe_dataframe_stats(df):
    """Builds a plain-text statistical summary of a DataFrame for the LLM prompt."""
    lines = [f"Shape: {df.shape[0]} rows, {df.shape[1]} columns"]
    lines.append("Columns and dtypes: " + ", ".join(f"{c} ({t})" for c, t in df.dtypes.items()))

    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing):
        lines.append("Missing values: " + ", ".join(f"{c}: {v}" for c, v in missing.items()))
    else:
        lines.append("Missing values: none")

    numeric_df = df.select_dtypes(include="number")
    if not numeric_df.empty:
        lines.append("Numeric summary:\n" + numeric_df.describe().to_string())

    return "\n".join(lines)


def _resolve_dataframes(data, frame):
    """
    Resolves one or more DataFrames into a {name: DataFrame} mapping for
    registering with DuckDB, recovering each DataFrame's original variable
    name from the caller's scope where possible.

    Accepts:
    - a single DataFrame:            ask(c, "...")
    - a tuple/list of DataFrames, any length "up to n":  ask((c, d, e), "...")
    - a dict of {name: DataFrame} for fully explicit naming
    """
    if isinstance(data, dict):
        for name, val in data.items():
            if not isinstance(val, pd.DataFrame):
                raise ValueError(f"data['{name}'] is not a pandas DataFrame.")
        return data

    if isinstance(data, pd.DataFrame):
        items = [data]
    elif isinstance(data, (tuple, list)):
        if not data:
            raise ValueError("No DataFrames provided.")
        items = list(data)
        for i, val in enumerate(items):
            if not isinstance(val, pd.DataFrame):
                raise ValueError(f"Item {i} in the tuple/list is not a pandas DataFrame.")
    else:
        raise ValueError(
            "First argument must be a pandas DataFrame, a tuple/list of "
            "DataFrames (e.g. (c, d)), or a dict of {name: DataFrame}."
        )

    # Recover each DataFrame's original variable name from the caller's scope
    caller_vars = {**frame.f_globals, **frame.f_locals}
    id_to_name = {}
    for name, val in caller_vars.items():
        if isinstance(val, pd.DataFrame) and id(val) not in id_to_name:
            id_to_name[id(val)] = name

    dataframes = {}
    used_names = set()
    for i, val in enumerate(items):
        name = id_to_name.get(id(val))
        if not name or name in used_names:
            base = name if (name and name not in used_names) else f"t{i + 1}"
            name = base
            suffix = 1
            while name in used_names:
                suffix += 1
                name = f"{base}_{suffix}"
        used_names.add(name)
        dataframes[name] = val

    return dataframes


def insights(df, api_key=None, provider=None, model=None, base_url=None):
    """
    Generates a short, plain-English summary of a DataFrame using an LLM —
    notable trends, ranges, and data-quality issues like missing values.

    Provider auto-detected from your API key's format, same as ask():
        c = load("data.csv")
        insights(c, api_key="AIza...")

    API keys can also be set via environment variables: ANTHROPIC_API_KEY,
    OPENAI_API_KEY, GEMINI_API_KEY.
    """
    provider, api_key, base_url = _resolve_provider_and_key(api_key, provider, base_url)

    stats_description = _describe_dataframe_stats(df)
    prompt = (
        "You are a data analyst. Given the dataset summary below, write a short, "
        "plain-English overview (3-5 sentences) highlighting notable trends, ranges, "
        "and any data-quality issues like missing values. Interpret the numbers — "
        "don't just repeat them verbatim.\n\n"
        f"{stats_description}\n\nSummary:"
    )

    summary = _call_llm(prompt, provider, api_key, model, base_url)
    print(summary)
    return summary


def ask(data, question, api_key=None, provider=None, model=None, base_url=None):
    """
    Converts a natural-language question into a SQL query using an LLM,
    runs it against your data, and previews the result — same as sql(),
    but you ask in plain English.

    Pass one DataFrame:
        c = load("sales.csv")
        ask(c, "what were total sales by region last quarter?", api_key="...")

    Pass two or more (for a JOIN, comparison, etc.) — scales to any count:
        ask((c, d), "who are our top customers by total sales?", api_key="...")
        ask((c, d, e), "...", api_key="...")

    Each DataFrame's original variable name (c, d, e, ...) is automatically
    recovered from your script and used as its table name in the generated
    SQL. If a name can't be recovered (e.g. an inline, unassigned
    DataFrame), it falls back to t1, t2, etc.

    The provider is auto-detected from your API key's format, so you
    usually don't need to specify it:
        ask(c, "...", api_key="sk-ant-...")   # detected as Anthropic
        ask(c, "...", api_key="AIza...")      # detected as Gemini
        ask(c, "...", api_key="gsk_...")      # detected as Groq (openai_compatible)
        ask(c, "...", api_key="sk-...")       # detected as OpenAI

    You can still override or specify explicitly, which is required for
    openai_compatible providers other than Groq:
        ask(c, "...", provider="openai_compatible", api_key="...",
            base_url="https://api.mistral.ai/v1", model="mistral-small-latest")

    API keys can also be set via environment variables instead of passing
    api_key= directly: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY.
    """
    frame = inspect.currentframe().f_back
    dataframes = _resolve_dataframes(data, frame)

    provider, api_key, base_url = _resolve_provider_and_key(api_key, provider, base_url)

    schema_description = _describe_schema(dataframes)
    generated_sql = _generate_sql(question, schema_description, provider, api_key, model, base_url)

    print(f"Generated SQL: {generated_sql}\n")

    con = duckdb.connect()
    for name, val in dataframes.items():
        con.register(name, val)

    result = con.execute(generated_sql).df()
    print(f"Query returned {len(result)} rows, {len(result.columns)} columns\n")
    print(result.head())
    return result