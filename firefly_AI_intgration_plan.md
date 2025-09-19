# Firefly III + AI Integration Plan
file:///Users/hamadfyad/Downloads/Firefly%20Ai%20Integration%20Plan.pdf

This document outlines the full integration of an AI service into Firefly III, including Docker builds, Docker Compose setup, CI/CD workflows, testing strategy, and infrastructure provisioning.

---

## 1️⃣ Firefly III + AI Integration

### Backend (Firefly III)

* Add a service in Firefly III to call the AI API for categorizing transactions.
* Example PHP code:

```php
function categorizeTransaction($transaction) {
    $aiServiceUrl = getenv('AI_SERVICE_URL') . '/categorize';
    $response = file_get_contents($aiServiceUrl . '?text=' . urlencode($transaction['description']));
    $result = json_decode($response, true);
    return $result['category'] ?? 'Uncategorized';
}
```

* Store results in DB:

  * Add `ai_category` column in `transactions` table.
  * Create a migration for schema update.

### Frontend (UI)

* Add a column or badge showing AI category:

```html
<td>{{ $transaction->ai_category ?? 'Uncategorized' }}</td>
```

* Optional: color-code categories or add filters.

---

## 2️⃣ AI Service (Separate Repo)

### Dockerfile (from scratch)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### FastAPI Example `/categorize` Endpoint

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TextRequest(BaseModel):
    text: str

@app.post("/categorize")
def categorize(request: TextRequest):
    categories = ["Food", "Transport", "Entertainment"]
    return {"category": categories[hash(request.text) % len(categories)]}
```

---

## 3️⃣ Docker Compose (Firefly III + AI)

```yaml
version: '3.9'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: firefly
      POSTGRES_USER: firefly
      POSTGRES_PASSWORD: secret
    volumes:
      - db-data:/var/lib/postgresql/data

  firefly:
    build:
      context: ./firefly-iii
      dockerfile: Dockerfile
    environment:
      DB_HOST: db
      DB_USER: firefly
      DB_PASS: secret
      AI_SERVICE_URL: http://ai:8000
    depends_on:
      - db
      - ai
    ports:
      - "8080:8080"

  ai:
    build:
      context: ./ai-repo
      dockerfile: Dockerfile
    ports:
      - "8000:8000"

volumes:
  db-data:
```

---

## 4️⃣ Testing Strategy

### Firefly III Tests (PHP)

```php
public function testAiIntegration() {
    $transaction = ['description' => 'Uber ride'];
    $category = categorizeTransaction($transaction);
    $this->assertNotEmpty($category);
}
```

### AI Repo Tests (Python)

* API test:

```python
def test_categorize(client):
    response = client.post("/categorize", json={"text": "Pizza"})
    assert response.status_code == 200
    assert "category" in response.json()
```

* UI test: Selenium / Playwright checks Firefly III UI shows AI category.

---

## 5️⃣ CI/CD (GitHub Actions)

```yaml
name: Firefly + AI CI/CD

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: firefly
          POSTGRES_USER: firefly
          POSTGRES_PASSWORD: secret
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      # Build Firefly III image
      - name: Build Firefly III image
        run: docker build -t firefly-custom ./firefly-iii

      # Build AI image
      - name: Build AI image
        run: docker build -t ai-service ./ai-repo

      - name: Run tests
        run: |
          docker run --rm firefly-custom php artisan test
          docker run --rm ai-service pytest

      - name: Push images
        run: |
          docker tag firefly-custom ghcr.io/${{ github.repository }}/firefly:latest
          docker tag ai-service ghcr.io/${{ github.repository }}/ai:latest
          docker push ghcr.io/${{ github.repository }}/firefly:latest
          docker push ghcr.io/${{ github.repository }}/ai:latest
```

---

## 6️⃣ Infrastructure (Terraform / Ansible)

### Terraform EC2 Example

```hcl
resource "aws_instance" "firefly_server" {
  ami           = "ami-0abcdef12345"
  instance_type = "t3.medium"
  key_name      = var.key_name
  security_groups = [aws_security_group.firefly_sg.name]

  user_data = <<-EOF
              #!/bin/bash
              apt update && apt install -y docker.io docker-compose
              git clone https://github.com/your-org/firefly-iii.git
              git clone https://github.com/your-org/ai-repo.git
              docker-compose -f /path/to/docker-compose.yml up -d
              EOF
}
```

* Ansible could alternatively configure instance and deploy Docker Compose.

---

## 7️⃣ Optional Improvements

* Monitoring: Prometheus + Grafana to track AI API calls.
* Logging: Centralized logging for Firefly III + AI.
* Versioned Docker images (use Git tags).
* Retry/fallback if AI service fails.

---

## ✅ Summary

1. Firefly III backend + UI updates for AI categories.
2. Separate AI service container.
3. Docker Compose with Firefly III, AI, DB.
4. Tests (PHP, Python, UI).
5. CI/CD pipeline (GitHub Actions).
6. Infrastructure deployment (Terraform/Ansible).
7. Optional: monitoring, logging, image versioning.
