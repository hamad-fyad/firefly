
# Firefly III Test Plan

## 1. What I Test

### API
- **Account Management:**
  - Create, retrieve, update, and delete accounts
  - List all accounts and verify data structure
  - Test account transactions, attachments, and piggy banks endpoints
  - Edge cases (e.g., invalid account IDs)
- **About Endpoints:**
  - `/about`, `/about/user`, `/about/cron/{token}` for system and user info

### UI
- **User Registration and Login:**
  - Register a new user and log in with valid credentials
  - Fallback to login if registration is disabled
- **Budget Management:**
  - Create a new budget as a user
  - Delete an account and verify logout
- **Navigation:**
  - Dashboard and budgets navigation
  - Logout flow

---

## 2. How I Test (Strategy)

### API
- Use `pytest` with `requests` to send HTTP requests to the Firefly III API
- Validate responses, status codes, and returned data
- Use fixtures for setup/teardown and to share test data (e.g., account IDs)

### UI
- Use Selenium WebDriver (Python) to automate browser actions
- Page Object Model (POM) for maintainable UI automation
- Run tests in both headless and headed modes (configurable via env var)
- Use unique test data (e.g., timestamped names) to avoid conflicts
- Fallback logic for registration/login to support different deployments

**Architectural Justification:**
Firefly III is a web app with a REST API and a modern web UI. API tests ensure backend correctness; UI tests ensure end-to-end user flows work as expected. POM and fixtures improve maintainability and reliability.

---

## 3. Success Criteria
- All API and UI tests pass without errors or unexpected failures
- All created test data is cleaned up (e.g., accounts deleted, users logged out)
- No regressions or critical errors in core user flows (account, budget, login/logout)
- Test results are reproducible across environments

---

## 4. Test Environment
- **API:** Firefly III instance at `${FIREFLY_BASE_URL}` (e.g., http://52.212.42.101:8080/api/v1), API token from `.env` (`API_TESTING_TOKEN`)
- **UI:** Firefly III web UI at `${APP_URL}` (e.g., http://52.212.42.101:8080)
  - Selenium tests run in Docker, EC2, or GitHub Actions (headless Chrome supported)
  - Test user credentials and data are configurable via environment variables

---

## 5. Test Data
- Unique account and budget names generated with timestamps
- Test user: `hamad.fyad.05@gmail.com` / `Hamadf@0528259919` (for automation only)
- Bank name: `test_bank`, balance: `1000000`
- Budget amount: `1000`
- API token, cron token and FIREFLY_BASE_URL from `.env`


---

## 6. Reporting Results
- **Local/CI:**
  - API: Pytest output (terminal) 
  - UI: Pytest output, Allure reports 
  - GitHub Actions: Workflow summary, logs, and artifacts
- **Manual:**
  - Issues and bugs are reported in the project issue tracker with logs and screenshots as needed

---

_This plan covers both backend and frontend regression for Firefly III, using automated and repeatable tests._