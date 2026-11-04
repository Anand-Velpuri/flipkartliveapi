# Flipkart Live API

A lightweight product search application built with **FastAPI** that retrieves product listings from Flipkart and exposes them through a structured REST API. It includes a responsive web interface for searching products, viewing prices, comparing discounts, and accessing product details.

## Features

- **Product Search:** Search for products using natural-language queries such as `laptops under 50000` or `mobiles under 30000`.
- **Structured Responses:** Extracts product information into consistent JSON responses using Pydantic models.
- **Product Information:** Provides product titles, brands, prices, MRP, discounts, images, ratings, reviews, specifications, and direct Flipkart links.
- **Web Interface:** Responsive product listing interface built with HTML, JavaScript, and Tailwind CSS.
- **REST API:** Supports both GET and POST search requests.
- **API Documentation:** Interactive API documentation through Swagger UI.
- **Containerization:** Docker support for consistent development and deployment.
- **Dependency Management:** Uses Astral UV for fast and reproducible Python dependency management.

## Tech Stack

| Component             | Technology                     |
| --------------------- | ------------------------------ |
| Backend               | Python, FastAPI                |
| Data Validation       | Pydantic                       |
| HTTP Client           | Requests                       |
| ASGI Server           | Uvicorn                        |
| Frontend              | HTML, JavaScript, Tailwind CSS |
| Dependency Management | Astral UV                      |
| Containerization      | Docker, Docker Compose         |

## Project Structure

```text
flipkartliveapi/
│
├── static/
│   └── index.html
│
├── app.py
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

Install the following tools:

- Python 3.12 or later
- [Astral UV](https://docs.astral.sh/uv/)
- Docker and Docker Compose (optional)

### 1. Clone the repository

```bash
git clone https://github.com/Anand-Velpuri/flipkartliveapi.git

cd flipkartliveapi
```

### 2. Install dependencies

Synchronize the project environment using UV:

```bash
uv sync --frozen
```

This creates the virtual environment and installs the dependencies specified in `uv.lock`.

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
FLIPKART_COOKIE=
FLIPKART_SSID=
FLIPKART_SQID=
```

These variables are used for Flipkart session configuration when required.

Use fresh session values when the existing session expires. Never commit cookies or other session credentials to version control.

For local development, export the variables into your shell before starting the application:

```bash
set -a
source .env
set +a
```

### 4. Start the application

Run the FastAPI application using UV:

```bash
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:

| Resource          | URL                                |
| ----------------- | ---------------------------------- |
| Web Interface     | http://localhost:8000/             |
| API Documentation | http://localhost:8000/docs         |
| OpenAPI Schema    | http://localhost:8000/openapi.json |
| Health Check      | http://localhost:8000/health       |

## API Reference

### Search Products

Retrieves product listings matching the supplied search query.

**Endpoint**

```http
POST /search
```

**Request Body**

```json
{
  "query": "laptops under 50000",
  "page": 1
}
```

**Example using cURL**

```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "laptops under 50000",
       "page": 1
     }'
```

**Example Response**

```json
{
  "query": "laptops under 50000",
  "page": 1,
  "count": 1,
  "products": [
    {
      "product_id": "PRODUCT_ID",
      "title": "Product Title",
      "brand": "HP",
      "price": 45990,
      "mrp": 65000,
      "discount": 29,
      "image_url": "https://example.com/product.jpg",
      "flipkart_url": "https://www.flipkart.com/product-link",
      "description": "Product specifications and details",
      "specifications": [],
      "rating": 4.4,
      "rating_count": 1200,
      "review_count": 120
    }
  ]
}
```

The response above illustrates the response structure. Actual values depend on the search results returned by Flipkart.

### Search Products Using GET

```http
GET /search?q=laptops%20under%2050000&page=1
```

**Example**

```bash
curl -G "http://localhost:8000/search" \
     --data-urlencode "q=laptops under 50000" \
     --data-urlencode "page=1"
```

### Health Check

```http
GET /health
```

Used to verify that the application is running.

### Interactive API Documentation

FastAPI automatically generates interactive documentation.

Visit:

```text
http://localhost:8000/docs
```

You can execute API requests, inspect request models, and explore response schemas directly through Swagger UI.

## Docker Deployment

The application can also run inside a Docker container.

### Build and Start

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up --build -d
```

### View Logs

```bash
docker compose logs -f
```

### Stop the Application

```bash
docker compose down
```

Once the container starts, access the application at:

```text
http://localhost:8000
```

The frontend and API are served by the same FastAPI application, so no separate frontend server is required.

## Configuration

| Environment Variable | Description                     |
| -------------------- | ------------------------------- |
| `FLIPKART_COOKIE`    | Optional browser session cookie |
| `FLIPKART_SSID`      | Search session identifier       |
| `FLIPKART_SQID`      | Search query identifier         |

Session-related values may expire and need to be refreshed.

## Notes and Limitations

- This project uses Flipkart's web-facing internal API endpoint, not an officially documented public developer API.
- Internal endpoint structures and request requirements may change without notice.
- Search availability depends on Flipkart's upstream service, session validity, and applicable request restrictions.
- Product prices, ratings, discounts, availability, and listings can change at any time.
- Product descriptions are assembled from the specifications available in search results and may not represent the complete product description.
- The project does not process orders, payments, or user transactions.

Use the service responsibly and comply with Flipkart's applicable terms and policies.

## License

This project is intended for educational and personal development purposes.

Add an explicit open-source license to the repository if you intend to grant others permission to use, modify, and distribute the code.

## Author

**Anand Velpuri**

- GitHub: [@Anand-Velpuri](https://github.com/Anand-Velpuri)
- Repository: [flipkartliveapi](https://github.com/Anand-Velpuri/flipkartliveapi)
