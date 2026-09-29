"""Capstone: login, search, add, update, verify, and save evidence."""
from conftest import SCREENSHOTS
from pages import AccountPage, CartPage, ShopPage


def shot(driver, filename):
    path = SCREENSHOTS / filename
    assert driver.save_screenshot(str(path)), f"Could not save {path}"


def test_ecommerce_purchase_flow(driver, account, test_data):
    base_url = test_data["base_url"]
    email, password = account

    AccountPage(driver, base_url).login(email, password)
    shot(driver, "01_logged_in.png")
    CartPage(driver, base_url).clear()

    ShopPage(driver, base_url).search_and_add(test_data["product"])
    shot(driver, "02_added_to_cart.png")

    details = CartPage(driver, base_url).update_and_verify(
        test_data["product"], test_data["quantity"]
    )
    shot(driver, "03_verified_cart.png")
    print(f"Verified cart: {details}")
