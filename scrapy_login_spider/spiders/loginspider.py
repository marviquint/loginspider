from scrapy import Spider, Request, FormRequest
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import scrapy


class ExampleSpider(scrapy.Spider):
    name = 'login'
    allowed_domains = ['page name']

    def __init__(self, username="username", password="password", *args, **kwargs):
        super(ExampleSpider, self).__init__(*args, **kwargs)
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome(executable_path = "path")
        self.driver.maximize_window()

    def start_requests(self):
        # Start by logging in
        self.driver.get("page name")
        self.driver.find_element("name", "username").send_keys(self.username)
        self.driver.find_element("name","password").send_keys(self.password)
        self.driver.find_element(By.XPATH, "//button").click()

        # Wait for the page to load
        self.driver.implicitly_wait(10)


        # Start crawling from the dashboard
        yield scrapy.Request(
            url="page name",
            callback=self.parse_dashboard,
        )
    
        

    def parse_dashboard(self, response):
        # Parse the first anchor tag inside #HEADER_MY_TASKS_text .alfresco-navigation-_HtmlAnchorMixin
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        anchor_url = "page name"
        yield scrapy.Request(url=response.urljoin(anchor_url), callback=self.parse_anchor)

    def parse_anchor(self, response):
        # Parse the anchor tag inside #insert-taskTitle li:nth-child(1) .filter4
        anch_url = "page name"

        if anch_url:    
             yield scrapy.Request(url=response.urljoin(anch_url), callback=self.parse_inner_anchor)
        else:
            print("No inner anchor URL found.")

    def parse_inner_anchor(self, response):
        # Parse the anchor tags inside .yui-dt-col-title .theme-color-1
        for anchor in response.css(".yui-dt-col-title .theme-color-1"):
            # Parse the anchor tag with class .view_more_actions inside each anchor tag in .yui-dt-col-title .theme-color-1
            view_more_url = anchor.css(".view_more_actions::attr(href)").get()
            yield scrapy.Request(url=response.urljoin(view_more_url), callback=self.parse_details)

        # Follow the next page link if it exists
        next_page_url = response.css(".yui-pg-next::attr(href)").get()
        if next_page_url:
            yield scrapy.Request(url=response.urljoin(next_page_url), callback=self.parse_inner_anchor)

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

    def close(self, reason):
        self.driver.quit()
