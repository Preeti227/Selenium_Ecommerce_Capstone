"""Small page objects for the OpenCart based TutorialsNinja demo."""
from decimal import Decimal
import re

from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def money(value):
    match = re.search(r"-?\d[\d,]*(?:\.\d{1,2})?", value)
    if not match:
        raise AssertionError(f"No price found in {value!r}")
    return Decimal(match.group().replace(",", ""))


class Page:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url.rstrip("/") + "/"
        self.wait = WebDriverWait(driver, 20)

    def go(self, route):
        self.driver.get(self.base_url + "index.php?route=" + route)

    def visible(self, by, selector):
        return self.wait.until(EC.visibility_of_element_located((by, selector)))

    def click(self, by, selector):
        self.wait.until(EC.element_to_be_clickable((by, selector))).click()

    def fill(self, by, selector, value):
        element = self.visible(by, selector)
        element.clear()
        element.send_keys(str(value))

    def dismiss_alert_if_present(self):
        """Close an optional JavaScript alert; normal success banners stay visible."""
        try:
            self.driver.switch_to.alert.accept()
            return True
        except NoAlertPresentException:
            return False


class AccountPage(Page):
    def register(self, data, email, password):
        self.go("account/register")
        fields = {
            "firstname": data["first_name"], "lastname": data["last_name"],
            "email": email, "telephone": data["telephone"],
            "password": password, "confirm": password,
        }
        for name, value in fields.items():
            self.fill(By.NAME, name, value)
        self.click(By.NAME, "agree")
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Continue']")
        self.dismiss_alert_if_present()
        heading = self.visible(By.CSS_SELECTOR, "#content h1").text
        if "Your Account Has Been Created" not in heading:
            errors = [el.text for el in self.driver.find_elements(By.CSS_SELECTOR, ".text-danger, .alert-danger")]
            raise AssertionError(f"Registration failed: {heading}; {errors}")
        self.go("account/logout")

    def login(self, email, password):
        self.go("account/login")
        self.fill(By.ID, "input-email", email)
        self.fill(By.ID, "input-password", password)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Login']")
        self.dismiss_alert_if_present()
        self.wait.until(lambda d: "route=account/account" in d.current_url)
        assert "My Account" in self.visible(By.CSS_SELECTOR, "#content h2").text


class ShopPage(Page):
    def search_and_add(self, name):
        self.fill(By.CSS_SELECTOR, "#search input[name='search']", name)
        self.click(By.CSS_SELECTOR, "#search button")
        self.visible(By.CSS_SELECTOR, "#content h1")
        product = self.wait.until(lambda d: next(
            (el for el in d.find_elements(By.CSS_SELECTOR, ".product-thumb h4 a")
             if el.text.strip() == name), False
        ), message=f"Search did not return {name!r}")
        product.click()
        assert self.visible(By.CSS_SELECTOR, "#content h1").text.strip() == name
        self.click(By.ID, "button-cart")
        self.dismiss_alert_if_present()
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-success")))
        self.go("checkout/cart")


class CartPage(Page):
    def clear(self):
        """Start every run from an empty cart, including repeat runs."""
        self.go("checkout/cart")
        for _ in range(20):
            buttons = self.driver.find_elements(
                By.CSS_SELECTOR, ".table-responsive tbody button[data-original-title='Remove'], "
                ".table-responsive tbody button[title='Remove']"
            )
            if not buttons:
                assert not self.driver.find_elements(By.CSS_SELECTOR, ".table-responsive tbody tr"), (
                    "Cart has rows but no Remove button; it could not be reset"
                )
                return
            count = len(buttons)
            buttons[0].click()
            self.dismiss_alert_if_present()
            self.wait.until(lambda d: len(d.find_elements(
                By.CSS_SELECTOR, ".table-responsive tbody button[data-original-title='Remove'], "
                ".table-responsive tbody button[title='Remove']"
            )) < count)
        raise AssertionError("Could not clear the existing shopping cart")

    def row(self, name):
        def matching(driver):
            for row in driver.find_elements(By.CSS_SELECTOR, ".table-responsive tbody tr"):
                if any(a.text.strip() == name for a in row.find_elements(By.CSS_SELECTOR, "td:nth-child(2) a")):
                    return row
            return False
        return self.wait.until(matching)

    def update_and_verify(self, name, quantity):
        row = self.row(name)
        assert row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a").text.strip() == name
        initial = int(row.find_element(By.CSS_SELECTOR, "input[name^='quantity']").get_attribute("value"))
        assert initial == 1, f"Expected one item initially, got {initial}"
        unit_price = money(row.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text)
        assert unit_price > 0
        field = row.find_element(By.CSS_SELECTOR, "input[name^='quantity']")
        field.clear()
        field.send_keys(str(quantity))
        row.find_element(By.CSS_SELECTOR, "button[data-original-title='Update'], button[title='Update']").click()
        self.dismiss_alert_if_present()
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-success")))
        row = self.row(name)
        actual = int(row.find_element(By.CSS_SELECTOR, "input[name^='quantity']").get_attribute("value"))
        subtotal = money(row.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text)
        assert actual == quantity, f"Cart quantity: expected {quantity}, got {actual}"
        assert subtotal == unit_price * quantity, (
            f"Line total: expected {unit_price * quantity}, got {subtotal}"
        )
        return {"product": name, "quantity": actual, "unit_price": str(unit_price), "line_total": str(subtotal)}
