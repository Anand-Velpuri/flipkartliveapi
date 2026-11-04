import os
from typing import Any
from urllib.parse import quote, urljoin

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"




FLIPKART_API_URL = "https://2.rome.api.flipkart.com/api/4/page/fetch"
FLIPKART_ORIGIN = "https://www.flipkart.com"

app = FastAPI(
    title="Flipkart Product Search API",
    version="1.0.0",
    description="Search Flipkart and return normalized product data.",
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

# Pydantic request/response models
class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200, description="Normal search text, e.g. laptops under 50k")
    page: int = Field(default=1, ge=1, le=20)


class Product(BaseModel):
    product_id: str | None = None
    title: str | None = None
    brand: str | None = None
    price: float | None = None
    mrp: float | None = None
    discount: int | None = None
    image_url: str | None = None
    flipkart_url: str | None = None
    description: str | None = None
    specifications: list[str] = Field(default_factory=list)
    rating: float | None = None
    rating_count: int = 0
    review_count: int = 0


class SearchResponse(BaseModel):
    query: str
    page: int
    count: int
    products: list[Product]



# Flipkart request helpers
def build_headers() -> dict[str, str]:
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": FLIPKART_ORIGIN,
        "Referer": f"{FLIPKART_ORIGIN}/",
        "User-Agent": os.getenv(
            "FLIPKART_USER_AGENT",
            "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/156.0.0.0 Mobile Safari/537.36",
        ),
        "X-User-Agent": os.getenv(
            "FLIPKART_X_USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 FKUA/website/42/website/Desktop",
        ),
    }

    # Optional browser session cookie. Keep it in an environment variable,
    # not in source control.
    cookie = os.getenv("FLIPKART_COOKIE")
    if cookie:
        headers["Cookie"] = cookie

    return headers


def build_payload(query: str, page: int) -> dict[str, Any]:
    page_uri = (
        f"/search?q={quote(query, safe='')}"
        "&otracker=search"
        "&otracker1=search"
        "&marketplace=FLIPKART"
        "&as-show=off"
        "&as=off"
    )

    # These IDs came from the captured browser request. Override them with
    # fresh values through environment variables if Flipkart rejects them.
    ssid = os.getenv("FLIPKART_SSID", "1k13edlfw00000001793773468413")
    sqid = os.getenv("FLIPKART_SQID", "bdp19o72xc0000001793773526351")

    return {
        "pageUri": page_uri,
        "pageContext": {
            "fetchSeoData": True,
            "paginatedFetch": False,
            "pageNumber": page,
        },
        "requestContext": {
            "type": "BROWSE_PAGE",
            "ssid": ssid,
            "sqid": sqid,
        },
    }



# Response extraction
def as_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def normalize_image_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None

    return (
        value.replace("{@width}", "612")
        .replace("{@height}", "612")
        .replace("{@quality}", "90")
    )


def extract_products(payload: dict[str, Any]) -> list[Product]:
    response_data = payload.get("RESPONSE", payload)
    slots = response_data.get("slots", [])

    products: list[Product] = []
    seen: set[str] = set()

    for slot in slots:
        widget = slot.get("widget") or {}
        if widget.get("type") != "PRODUCT_SUMMARY":
            continue

        cards = (widget.get("data") or {}).get("products") or []

        for card in cards:
            product_info = card.get("productInfo") or {}
            product = product_info.get("value") or {}
            if not product:
                continue

            product_id = product.get("id") or card.get("productId")
            base_url = product.get("baseUrl")
            smart_url = product.get("smartUrl")
            product_url = urljoin(FLIPKART_ORIGIN, base_url) if base_url else smart_url

            # Deduplicate repeated cards in the same response.
            unique_key = product_id or product_url
            if unique_key and unique_key in seen:
                continue
            if unique_key:
                seen.add(unique_key)

            titles = product.get("titles") or {}
            pricing = product.get("pricing") or {}

            final_price = (pricing.get("finalPrice") or {}).get("value")
            mrp = (pricing.get("mrp") or {}).get("value")

            # Prefer the final payable price; fall back to SPECIAL_PRICE.
            if final_price is None:
                price_options = pricing.get("prices") or []
                special_price = next(
                    (item.get("value") for item in price_options
                     if item.get("priceType") == "SPECIAL_PRICE" and item.get("value") is not None),
                    None,
                )
                final_price = special_price

            discount = pricing.get("totalDiscount")
            if discount is None and mrp and final_price is not None and mrp > 0:
                discount = round((mrp - final_price) / mrp * 100)

            media_images = ((product.get("media") or {}).get("images") or [])
            image_url = None
            if media_images:
                image_url = normalize_image_url(media_images[0].get("url"))

            rating_info = product.get("rating") or {}
            rating_count = int(rating_info.get("count") or 0)
            rating = as_number(rating_info.get("average")) if rating_count > 0 else None

            subtitle = titles.get("subtitle")
            specifications = list(dict.fromkeys(
                item
                for item in (product.get("minKeySpecs") or []) + (product.get("keySpecs") or [])
                if isinstance(item, str) and item.strip()
            ))
            description_parts = ([subtitle] if isinstance(subtitle, str) and subtitle.strip() else [])
            description_parts.extend(specifications)

            products.append(
                Product(
                    product_id=product_id,
                    title=titles.get("title"),
                    brand=product.get("productBrand"),
                    price=as_number(final_price),
                    mrp=as_number(mrp),
                    discount=int(discount) if isinstance(discount, (int, float)) else None,
                    image_url=image_url,
                    flipkart_url=product_url,
                    description=" | ".join(description_parts) or None,
                    specifications=specifications,
                    rating=rating,
                    rating_count=rating_count,
                    review_count=int(rating_info.get("reviewCount") or 0),
                )
            )

    return products


def run_flipkart_search(query: str, page: int) -> SearchResponse:
    request_payload = build_payload(query, page)

    try:
        # A new Session per API request avoids sharing mutable Session state
        # between concurrent FastAPI worker threads.
        with requests.Session() as session:
            response = session.post(
                FLIPKART_API_URL,
                headers=build_headers(),
                json=request_payload,
                timeout=25,
            )
            response.raise_for_status()
            raw_data = response.json()

    except requests.Timeout as exc:
        raise HTTPException(status_code=504, detail="Flipkart request timed out") from exc
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        raise HTTPException(
            status_code=502,
            detail=f"Flipkart returned HTTP {status}. Refresh the session cookies/IDs if needed.",
        ) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Could not reach Flipkart") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Flipkart returned a non-JSON response") from exc

    products = extract_products(raw_data)
    return SearchResponse(
        query=query,
        page=page,
        count=len(products),
        products=products,
    )



# API endpoints
@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse)
def search_get(
    q: str = Query(min_length=1, max_length=200, description="Example: laptops under 50k"),
    page: int = Query(default=1, ge=1, le=20),
) -> SearchResponse:
    return run_flipkart_search(q, page)


@app.post("/search", response_model=SearchResponse)
def search_post(request: SearchRequest) -> SearchResponse:
    return run_flipkart_search(request.query, request.page)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7860)