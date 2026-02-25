import datetime
import json
import os

import msal
import requests

from .constants import CONFIG_DIR

AUTHORITY = "https://login.microsoftonline.com/common"
# MSAL handles reserved OIDC scopes internally; only request resource scopes.
SCOPES = ["Tasks.ReadWrite"]
TOKEN_CACHE_FILE = os.path.join(CONFIG_DIR, "ms_token_cache.json")


def _ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _load_token_cache():
    _ensure_config_dir()
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            cache.deserialize(f.read())
    return cache


def _save_token_cache(cache):
    if cache.has_state_changed:
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def _select_account(app, account_id=None, preferred_username=None):
    accounts = app.get_accounts()
    if account_id:
        for acct in accounts:
            if acct.get("home_account_id") == account_id:
                return acct
    if preferred_username:
        for acct in accounts:
            if acct.get("username") == preferred_username:
                return acct
    return accounts[0] if accounts else None


def _acquire_token(client_id, account_id=None, interactive=False):
    if not client_id:
        raise ValueError("Microsoft Client ID is not configured.")
    cache = _load_token_cache()
    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=AUTHORITY,
        token_cache=cache,
    )
    account = _select_account(app, account_id=account_id)
    result = None
    if not interactive and account:
        result = app.acquire_token_silent(SCOPES, account=account)
    if not result and interactive:
        result = app.acquire_token_interactive(SCOPES, prompt="login")
        preferred = result.get("id_token_claims", {}).get("preferred_username")
        account = _select_account(app, preferred_username=preferred) or account
    if not result:
        raise RuntimeError("No cached token. Use Test Sync to sign in.")
    _save_token_cache(cache)
    if "access_token" not in result:
        raise RuntimeError(result.get("error_description") or "Token error")
    new_account_id = account.get("home_account_id") if account else account_id
    return result["access_token"], new_account_id


def _graph_request(method, url, token, json_body=None):
    headers = {"Authorization": f"Bearer {token}"}
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    response = requests.request(
        method,
        url,
        headers=headers,
        data=json.dumps(json_body) if json_body is not None else None,
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"{method} {url} failed: {response.status_code} {response.text}"
        )
    if response.text:
        return response.json()
    return None


def _get_list_id(token, list_name):
    url = "https://graph.microsoft.com/v1.0/me/todo/lists"
    data = _graph_request("GET", url, token)
    for item in data.get("value", []):
        if item.get("displayName") == list_name:
            return item["id"]
    created = _graph_request(
        "POST",
        url,
        token,
        json_body={"displayName": list_name},
    )
    return created["id"]


def _iter_tasks(token, list_id):
    url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
    while url:
        data = _graph_request("GET", url, token)
        for item in data.get("value", []):
            yield item
        url = data.get("@odata.nextLink")


def _clear_list(token, list_id):
    for item in _iter_tasks(token, list_id):
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks/{item['id']}"
        _graph_request("DELETE", url, token)


def _to_graph_date(iso_str):
    """Convert to Graph dateTimeTimeZone with date only (for dueDateTime)."""
    dt = datetime.datetime.fromisoformat(iso_str)
    return {
        "dateTime": dt.strftime("%Y-%m-%dT00:00:00"),
        "timeZone": "UTC",
    }


def _to_graph_datetime(iso_str):
    """Convert to Graph dateTimeTimeZone with full time (for reminderDateTime)."""
    dt = datetime.datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    else:
        dt = dt.astimezone(datetime.timezone.utc)
    dt = dt.replace(microsecond=0)
    return {"dateTime": dt.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "UTC"}


def _now_graph_datetime():
    dt = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    return {"dateTime": dt.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "UTC"}


def _task_payload(task):
    title = str(task.get("text", "")).strip() or "(untitled)"
    payload = {
        "title": title,
        "status": "completed" if task.get("done") else "notStarted",
    }
    if int(task.get("star", 0) or 0) > 0:
        payload["importance"] = "high"
    reminder = task.get("reminder")
    if reminder:
        payload["dueDateTime"] = _to_graph_date(reminder)
        payload["reminderDateTime"] = _to_graph_datetime(reminder)
        payload["isReminderOn"] = True
    if task.get("done"):
        payload["completedDateTime"] = _now_graph_datetime()
    return payload


def _create_task(token, list_id, payload):
    url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
    return _graph_request("POST", url, token, json_body=payload)


def push_tasks(tasks, list_name, client_id, account_id=None, interactive=False):
    token, new_account_id = _acquire_token(
        client_id, account_id=account_id, interactive=interactive
    )
    list_id = _get_list_id(token, list_name)
    _clear_list(token, list_id)

    for task in tasks:
        _create_task(token, list_id, _task_payload(task))
    return new_account_id
