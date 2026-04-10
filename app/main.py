"""Flui demo FastAPI application."""

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

APP_NAME = os.environ.get('APP_NAME', 'Flui Demo FastAPI')
APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
START_TIME = datetime.now(timezone.utc)

app = FastAPI(
    title='Flui Demo — FastAPI',
    description='A minimal demo application deployed via Flui.',
    version=APP_VERSION,
    openapi_url='/api/openapi',
    docs_url='/docs',
    redoc_url=None,
)


# ─── Models ────────────────────────────────────────────────────────────────


class Item(BaseModel):
    id: str
    name: str
    description: str
    createdAt: str


class CreateItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)


class HealthResponse(BaseModel):
    status: str
    appName: str
    version: str
    uptime: int
    timestamp: str


# ─── In-memory store ───────────────────────────────────────────────────────


_items: dict[str, Item] = {}


def _seed() -> None:
    if _items:
        return
    now = datetime.now(timezone.utc).isoformat()
    _items['1'] = Item(
        id='1',
        name='Welcome to Flui',
        description='Your first demo item — feel free to delete it.',
        createdAt=now,
    )
    _items['2'] = Item(
        id='2',
        name='Try the API',
        description='Visit /docs to explore the OpenAPI documentation.',
        createdAt=now,
    )


_seed()


# ─── Routes ────────────────────────────────────────────────────────────────


@app.get('/', response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{APP_NAME}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0a0a0f; color: #e8e8ed; min-height: 100vh;
    }}
    a {{ color: #4f9eff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .page {{ max-width: 800px; margin: 0 auto; padding: 4rem 2rem; }}
    .badge {{
      display: inline-block; padding: 0.4rem 0.9rem; border-radius: 999px;
      background: linear-gradient(135deg, #4f9eff, #a855f7); color: #fff;
      font-size: 0.8rem; font-weight: 600; margin-bottom: 1.5rem;
    }}
    h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
    .subtitle {{ color: #888; margin-bottom: 2rem; }}
    .card {{
      background: #15151c; border: 1px solid #2a2a35; border-radius: 12px;
      padding: 1.5rem; margin-bottom: 2rem;
    }}
    .card h2 {{ font-size: 1.2rem; margin-bottom: 1rem; }}
    ul {{ list-style: none; display: grid; gap: 0.5rem; }}
    code {{
      display: inline-block; background: #2a2a35; color: #4f9eff;
      padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.75rem;
      font-weight: 600; margin-right: 0.4rem;
    }}
    footer {{
      margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #2a2a35;
      color: #666; font-size: 0.85rem; text-align: center;
    }}
  </style>
</head>
<body>
  <main class="page">
    <div class="badge">🚀 Flui Demo Application</div>
    <h1>{APP_NAME}</h1>
    <p class="subtitle">FastAPI · Pydantic v2 · Uvicorn · v{APP_VERSION}</p>
    <section class="card">
      <h2>API Endpoints</h2>
      <ul>
        <li><code>GET</code> <a href="/health">/health</a> — health</li>
        <li><code>GET</code> <a href="/items">/items</a> — list items</li>
        <li><code>POST</code> /items — create item</li>
        <li><code>GET</code> <a href="/api/openapi">/api/openapi</a> — spec</li>
        <li><code>GET</code> <a href="/docs">/docs</a> — Swagger UI</li>
      </ul>
    </section>
    <footer>Powered by <a href="https://flui.cloud">Flui</a></footer>
  </main>
</body>
</html>"""


@app.get('/health', response_model=HealthResponse, tags=['Health'])
def health() -> HealthResponse:
    """Service health check."""
    uptime = int((datetime.now(timezone.utc) - START_TIME).total_seconds())
    return HealthResponse(
        status='ok',
        appName=APP_NAME,
        version=APP_VERSION,
        uptime=uptime,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get('/items', tags=['Items'])
def list_items() -> dict[str, list[Item]]:
    """List all items."""
    items = sorted(_items.values(), key=lambda i: i.createdAt, reverse=True)
    return {'items': items}


@app.post(
    '/items',
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
    tags=['Items'],
)
def create_item(request: CreateItemRequest) -> Item:
    """Create a new item."""
    new_id = str(int(datetime.now(timezone.utc).timestamp() * 1000))
    item = Item(
        id=new_id,
        name=request.name,
        description=request.description,
        createdAt=datetime.now(timezone.utc).isoformat(),
    )
    _items[new_id] = item
    return item


@app.get('/items/{item_id}', response_model=Item, tags=['Items'])
def get_item(item_id: str) -> Item:
    """Get an item by ID."""
    item = _items.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail='Item not found')
    return item


@app.delete('/items/{item_id}', tags=['Items'])
def delete_item(item_id: str) -> dict[str, bool]:
    """Delete an item by ID."""
    if item_id not in _items:
        raise HTTPException(status_code=404, detail='Item not found')
    del _items[item_id]
    return {'deleted': True}
