"""UI tests — Selenium against the auto-generated Swagger UI (/docs).

These tests require a running server instance (started in CI or locally)
and a Chrome/Chromium browser with chromedriver available on PATH.

Run locally:
    uvicorn app.main:app --port 8000 &
    pytest tests/ui/ -v
"""

from __future__ import annotations

import os
import socket

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
TIMEOUT = 15


def is_server_running(url: str) -> bool:
    """Check if the server is running and reachable."""
    try:
        # Parse host and port from URL
        host = url.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        port = 8000
        if ":" in url:
            port = int(url.split(":")[-1])
        
        # Attempt socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="module")
def driver():
    # Check if server is running before attempting to create driver
    if not is_server_running(BASE_URL):
        pytest.skip(f"Test server unavailable at {BASE_URL}. Start with: uvicorn app.main:app --port 8000")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        d = webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Chrome/chromedriver unavailable in this environment: {exc}")
    d.implicitly_wait(TIMEOUT)
    yield d
    d.quit()


class TestSwaggerDocsPage:
    """Verify the Swagger UI loads and displays the expected API sections."""

    def test_docs_page_loads(self, driver):
        driver.get(f"{BASE_URL}/docs")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swagger-ui"))
        )

    def test_title_contains_energy_grid(self, driver):
        driver.get(f"{BASE_URL}/docs")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swagger-ui"))
        )
        title_el = driver.find_element(By.CSS_SELECTOR, ".info .title")
        assert "Energy Grid" in title_el.text

    def test_simulation_section_visible(self, driver):
        driver.get(f"{BASE_URL}/docs")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swagger-ui"))
        )
        sections = driver.find_elements(By.CSS_SELECTOR, ".opblock-tag-section h3 a")
        tag_names = [s.text.strip() for s in sections]
        assert "Simulation" in tag_names, f"Sections found: {tag_names}"

    def test_supplies_section_visible(self, driver):
        driver.get(f"{BASE_URL}/docs")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swagger-ui"))
        )
        sections = driver.find_elements(By.CSS_SELECTOR, ".opblock-tag-section h3 a")
        tag_names = [s.text.strip() for s in sections]
        assert "Supplies" in tag_names, f"Sections found: {tag_names}"

    def test_demands_section_visible(self, driver):
        driver.get(f"{BASE_URL}/docs")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swagger-ui"))
        )
        sections = driver.find_elements(By.CSS_SELECTOR, ".opblock-tag-section h3 a")
        tag_names = [s.text.strip() for s in sections]
        assert "Demands" in tag_names, f"Sections found: {tag_names}"

    def test_network_section_visible(self, driver):
        driver.get(f"{BASE_URL}/docs")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swagger-ui"))
        )
        sections = driver.find_elements(By.CSS_SELECTOR, ".opblock-tag-section h3 a")
        tag_names = [s.text.strip() for s in sections]
        assert "Network" in tag_names, f"Sections found: {tag_names}"


class TestRedocPage:
    """Verify the ReDoc documentation page is accessible."""

    def test_redoc_page_loads(self, driver):
        driver.get(f"{BASE_URL}/redoc")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "redoc, .redoc-wrap"))
        )

    def test_redoc_has_api_info(self, driver):
        driver.get(f"{BASE_URL}/redoc")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "redoc, .redoc-wrap"))
        )
        assert "Energy Grid" in driver.page_source
