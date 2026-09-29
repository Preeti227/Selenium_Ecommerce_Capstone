"""Browser lifetime, demo account bootstrap, and failure evidence."""
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import ROOT, load_data
from pages import AccountPage

REPORTS = ROOT / "reports"
SCREENSHOTS = REPORTS / "screenshots"
ACCOUNT_FILE = ROOT / ".local" / "account.json"


def pytest_sessionstart(session):
    REPORTS.mkdir(parents=True, exist_ok=True)


def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", help="Run Chrome without opening a window")


@pytest.fixture(scope="session")
def test_data():
    return load_data()


@pytest.fixture
def driver(request):
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    options = Options()
    if request.config.getoption("--headless"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-notifications")
    browser = webdriver.Chrome(options=options)  # Selenium Manager handles the driver.
    browser.set_page_load_timeout(45)
    request.node.driver = browser
    yield browser
    browser.quit()


@pytest.fixture
def account(driver, test_data):
    email = os.getenv("DEMO_EMAIL")
    password = os.getenv("DEMO_PASSWORD")
    if bool(email) != bool(password):
        raise ValueError("Set both DEMO_EMAIL and DEMO_PASSWORD, or neither")
    if email and password:
        return email, password
    if ACCOUNT_FILE.exists():
        saved = json.loads(ACCOUNT_FILE.read_text(encoding="utf-8"))
        return saved["email"], saved["password"]
    email = f"selenium.capstone.{secrets.token_hex(6)}@example.com"
    password = "Demo!" + secrets.token_urlsafe(12)
    AccountPage(driver, test_data["base_url"]).register(test_data, email, password)
    ACCOUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACCOUNT_FILE.write_text(json.dumps({"email": email, "password": password}, indent=2), encoding="utf-8")
    ACCOUNT_FILE.chmod(0o600)
    return email, password


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when in ("setup", "call") and report.failed and hasattr(item, "driver"):
        SCREENSHOTS.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = SCREENSHOTS / f"FAILED_{stamp}.png"
        try:
            if item.driver.save_screenshot(str(path)):
                report.sections.append(("Failure screenshot", str(path)))
        except Exception:
            pass 
