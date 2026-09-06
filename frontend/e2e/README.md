# Browser E2E tests

The Playwright configuration starts both services automatically:

- FastAPI on `127.0.0.1:8010`, using `backend/tests/e2e_server.py` to replace
  PostgreSQL and Gemini calls with deterministic test data.
- Vite on `127.0.0.1:5173`, configured to call that FastAPI process.

Install the browser once, then run the suite from `frontend/`:

```bash
npx playwright install --with-deps chromium
npm run test:e2e
```

`--with-deps` requires root privileges on Linux/WSL. CI may instead use the
matching official Playwright image. Test traces and screenshots are written to
`test-results/`; the HTML report is written to `playwright-report/`.

The resolved-without-purchase scenario deliberately uses 5 monitors against a
fixed 2 warehouse units plus 3 assignable assets, so the expected net-new
purchase quantity is always zero.
