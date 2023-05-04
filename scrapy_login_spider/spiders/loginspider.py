from scrapy import Spider, Request
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import scrapy


class ExampleSpider(scrapy.Spider):
    name = 'login'
    allowed_domains = ['website url']

    def __init__(self, username="username", password="password", *args, **kwargs):
        super(ExampleSpider, self).__init__(*args, **kwargs)
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome(executable_path = "path")
        self.driver.maximize_window()

    def start_requests(self):
        # Start by logging in
        self.driver.get("login url")
        self.driver.find_element("name", "username").send_keys(self.username)
        self.driver.find_element("name","password").send_keys(self.password)
        self.driver.find_element(By.XPATH, "//button").click()

        # Wait for the page to load
        self.driver.implicitly_wait(10)

        # Go to the initial page to crawl
        initial_url = "active task url"
        yield scrapy.Request(url=initial_url, callback=self.parse)

    def parse(self, response):
        # Parse the initial page to get the next URL to crawl
        next_url = response.urljoin("enact indexing url")

        # Crawl the next URL
        yield scrapy.Request(url=response.urljoin(next_url), callback=self.parse_inner_anchor)

    def parse_inner_anchor(self, response):
        # Parse the anchor tags inside .yui-dt-col-title .theme-color-1
        for anchor in response.css(".yui-dt-col-title .theme-color-1"):
            # Parse the anchor tag with class .view_more_actions inside each anchor tag in .yui-dt-col-title .theme-color-1
            view_more_url = anchor.css(".view_more_actions::attr(href)").get()
            yield scrapy.Request(url=response.urljoin(view_more_url), callback=self.parse_details)

    def parse_details(self, response):
        # Extract the document title and properties from the page
        document_title = response.css(".node-info .dark::text").get()
        properties = response.css(".form-fields ::text").getall()

        # Yield the extracted data
        yield {
            "document_title": document_title,
            "properties": properties,
        }
        # Print the extracted data
        print(f"Title: {document_title}")
        print(f"Properties: {properties}")

        # Follow the next page link if it exists
        next_page_url = response.css(".yui-pg-next::attr(href)").get()
        if next_page_url:
            yield scrapy.Request(url=response.urljoin(next_page_url), callback=self.parse_details)

    def closed(self, reason):
        self.driver.quit()
