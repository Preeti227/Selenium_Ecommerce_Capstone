# Selenium WebDriver E-Commerce Capstone (Python)

This project automates a customer adding an iPhone to the [TutorialsNinja demo store](https://tutorialsninja.com/demo/). On the first run it registers a disposable demo account, logs out, and logs in to exercise the requested login step. Later runs reuse the locally saved credentials. It clears any cart items from earlier runs, searches for the product, adds one unit, changes the cart quantity to two, checks the product name, quantity, unit price, and line total, saves screenshots, and writes an HTML and JUnit XML execution report. It accepts JSON or Excel input. It also handles optional JavaScript alerts and waits for the site's normal success banners.

## Requirements

- Python 3.10 or later, Google Chrome, and internet access to the demo site.
- Install dependencies with `python -m pip install -r requirements.txt`. Selenium Manager normally downloads or locates the matching ChromeDriver automatically; the first run may require network access.

## Run

Run the following commands from this folder on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -v --html=reports/report.html --self-contained-html --junitxml=reports/results.xml
```

On macOS/Linux, replace the activation command with `source .venv/bin/activate`.

Add `--headless` to run Chrome without a visible window. To run with an existing demo account, set both `DEMO_EMAIL` and `DEMO_PASSWORD` in your shell before running. Never put a personal account password in the JSON, workbook, or screenshots. First-run account credentials are saved in `.local/account.json`, with restricted permissions where supported. This file is excluded from Git. Delete it to create a new demo account next time.

The test uses explicit waits and a 45-second page load timeout; availability and layout of this third-party demo can still change. If account registration is temporarily blocked, provide an existing demo account through the environment variables. The test never submits an order or payment.

## Test data

Edit `data/test_data.json` or use the included `data/test_data.xlsx`. The product must exist in the demo store and have no mandatory product options. Quantity must be at least 2 to show an actual update. The workbook has the following headers in row 1 and values in row 2 of its first sheet:

| base_url | product | quantity | first_name | last_name | telephone |
| --- | --- | ---: | --- | --- | --- |
| https://tutorialsninja.com/demo/ | iPhone | 2 | Demo | Tester | 1234567890 |

Set `TEST_DATA` to the full workbook path before running, for example in PowerShell:

```powershell
$env:TEST_DATA = "C:\path\to\test_data.xlsx"
python -m pytest -v --html=reports/report.html --self-contained-html --junitxml=reports/results.xml
```

## Deliverables and checks

| Requirement | Implementation / evidence |
| --- | --- |
| Launch browser | `driver` fixture in `conftest.py` |
| Login | `AccountPage.login`; first run registration setup |
| Search and add product | `ShopPage.search_and_add` |
| Update quantity and verify cart | `CartPage.update_and_verify`; asserts name, initial 1, final quantity, unit price > 0, and unit price × quantity = line total |
| Capture screenshots | `reports/screenshots/01_logged_in.png`, `02_added_to_cart.png`, `03_verified_cart.png`; failure screenshot on failed test |
| Read Excel/JSON | `config.load_data`, selected by `TEST_DATA` |
| Handle popup/alerts | `Page.dismiss_alert_if_present` handles optional JavaScript alerts; waits for confirmation banners |
| Execution report | `reports/report.html` and `reports/results.xml` |

Success means pytest reports **1 passed**; review the three screenshots and the HTML report. A failure means the test stopped at a specific assertion or interaction; review the pytest traceback and `FAILED_*.png` screenshot. Screenshots and reports are generated when the test runs and are excluded from version control. This package contains the test project and sample data; it does not contain a completed execution report because the browser test must run on a machine with Chrome and the dependencies installed.

References: [Selenium waits](https://www.selenium.dev/documentation/webdriver/waits/), [TutorialsNinja register page](https://tutorialsninja.com/demo/index.php?route=account/register), [iPhone product page](https://tutorialsninja.com/demo/index.php?route=product/product&product_id=40).
