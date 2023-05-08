import scrapy
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from urllib.parse import urlparse, parse_qs
from selenium.common.exceptions import NoSuchWindowException


class GrcSpider(scrapy.Spider):
    name = "grc_spider"
    start_urls = ["dashboard "]

    def __init__(self, username="username", password="password", *args, **kwargs):
        super(GrcSpider, self).__init__(*args, **kwargs)
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome(executable_path="path")
        self.driver.maximize_window()

    def start_requests(self):
        # Start by logging in using Selenium
        self.driver.get("login page")
        username_input = self.driver.find_element(By.NAME, "username")
        password_input = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.XPATH, "//button")
        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        login_button.click()

        # Wait for the page to load
        WebDriverWait(self.driver, 120).until(
            EC.presence_of_element_located((By.ID, "HEADER_MY_TASKS_text"))
        )

        # Once logged in, crawl the tasks using Scrapy
        yield SeleniumRequest(
            url="dashboard",
            wait_time=120,
            screenshot=True,
            callback=self.parse_dashboard,
            dont_filter=True,
            meta={'driver': self.driver}
        )
    
    def parse_dashboard(self, response: HtmlResponse):
        # Click My Tasks link using JavaScript
        my_tasks_link = response.meta['driver'].find_element(By.ID, "HEADER_MY_TASKS_text").find_element(By.TAG_NAME, 'a')
        response.meta['driver'].execute_script("arguments[0].click();", my_tasks_link)

        # Wait for the page to load
        WebDriverWait(response.meta['driver'], 120).until(
            EC.presence_of_element_located((By.ID, "insert-taskTitle"))
        )

        # Once on My Tasks page, crawl the tasks using Scrapy
        yield SeleniumRequest(
            url=response.url,
            wait_time=120,
            screenshot=True,
            callback=self.parse_tasks,
            dont_filter=True,
            meta={'driver': response.meta['driver']}
        )

    def parse_tasks(self, response: HtmlResponse):
        # Wait for the filter option to be clickable
        filter_option_selector1 = '#taskF'
        WebDriverWait(response.meta['driver'], 120).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, filter_option_selector1))
        )

        # Click the first filter option using JavaScript
        filter_option = response.meta['driver'].find_element(By.CSS_SELECTOR, filter_option_selector1)
        response.meta['driver'].execute_script("arguments[0].click();", filter_option)

        filter_option_selector2 = '#insert-taskTitle li:nth-child(1) .filter4'
        WebDriverWait(response.meta['driver'], 120).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, filter_option_selector2))
        )

        # Click the first filter option using JavaScript
        filter_option2 = response.meta['driver'].find_element(By.CSS_SELECTOR, filter_option_selector2)
        response.meta['driver'].execute_script("arguments[0].click();", filter_option2)

        # Wait for the page to load
        WebDriverWait(response.meta['driver'], 120).until(
            EC.presence_of_element_located((By.XPATH, '//td')),
            EC.presence_of_element_located((By.XPATH, '//*[contains(concat( " ", @class, " " ), concat( " ", "type", " " ))]//a'))
        )

        # Get all the datatable elements
        datatables = response.xpath('//*[@id="yuievtautoid-0"]')

        # Get all the document links from all the datatables
        document_links = []
        for datatable in datatables:
            datatable_links = datatable.xpath('.//a/@href').extract()
            document_links.extend(datatable_links)
        num_links = len(document_links)
        self.logger.info(f"Found {num_links} document links")

        # Get the handle of the original tab
        original_tab_handle = self.driver.current_window_handle

        # Open all the links in separate tabs
        tabs = []
        for i, document_link in enumerate(document_links, start=1):
            # Append the base URL to the document link
            document_url = "url" + document_link

            # Click the document link using JavaScript to open it in a new tab
            self.driver.execute_script("window.open(arguments[0]);", document_url)
            tabs.append(self.driver.window_handles[-1]) # Save the handle of the new tab

        # Process the links in parallel
        for tab, document_link in zip(tabs, document_links):
            # Switch to the tab with the document
            self.driver.switch_to.window(tab)

            # Wait for the document page to load
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.node-info .dark')),
                EC.presence_of_element_located((By.CSS_SELECTOR, '.form-fields'))
            )

            # Extract the document title and properties using Scrapy
            document_title = Selector(text=self.driver.page_source).css('.node-info .dark::text').get().strip()
            document_properties = Selector(text=self.driver.page_source).css('.field-item').getall()

            # Store the document data in a dictionary
            properties_dict = {}
            for prop in document_properties:
                key = Selector(text=prop).css('label::text').get().strip()
                value = Selector(text=prop).css('.field-item::text').get().strip()
                properties_dict[key] = value

            document_data = {
                'title': document_title.strip(),
                'properties': properties_dict,
            }

            print(document_data) # Print the scraped data

            # Close the document page using JavaScript
            self.driver.close()

            # Switch back to the original tab
            self.driver.switch_to.window(original_tab_handle)

        # Close all the tabs
        for tab in tabs:
            self.driver.switch_to.window(tab)
            self.driver.close()

        # Switch back to the original tab
        self.driver.switch_to.window(original_tab_handle)



    def handle_error(self, failure):
        # Log any errors
        self.logger.error(repr(failure))
        
    def closed(self, response):
        self.driver.quit()

