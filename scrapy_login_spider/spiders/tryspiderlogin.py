import scrapy
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse



class GrcSpider(scrapy.Spider):
    name = "grc_spider"
    start_urls = ["dashboard url"]

    def __init__(self, username="username", password="password", *args, **kwargs):
        super(GrcSpider, self).__init__(*args, **kwargs)
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome(executable_path="Users\InnoCSR\Downloads\chromedriver_win32\chromedriver.exe")
        self.driver.maximize_window()

    def start_requests(self):
        # Start by logging in using Selenium
        self.driver.get("login url")
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
            url="dashboard url",
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

        # Click the first filter option using Selenium
        filter_option = response.meta['driver'].find_element(By.CSS_SELECTOR, filter_option_selector1)
        filter_option.click()

        filter_option_selector2 = '#insert-taskTitle li:nth-child(1) .filter4'
        WebDriverWait(response.meta['driver'], 120).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, filter_option_selector2))
        )

        # Click the first filter option using Selenium
        filter_option2 = response.meta['driver'].find_element(By.CSS_SELECTOR, filter_option_selector2)
        filter_option2.click()

        # Wait for the page to load
        WebDriverWait(response.meta['driver'], 120).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(concat(" ", @class, " "), concat(" ", "yui-dt-col-title", " "))]//*[contains(concat(" ", @class, " "), concat(" ", "theme-color-1", " "))]'))
        )

        # Find all the document links using Scrapy
        document_links = response.xpath('//*[contains(concat(" ", @class, " "), concat(" ", "yui-dt-col-title", " "))]//*[contains(concat(" ", @class, " "), concat(" ", "theme-color-1", " "))]')
        num_links = len(document_links)
        self.logger.info(f"Found {num_links} document links")

        # Get the handle of the original tab
        original_tab_handle = response.meta['driver'].current_window_handle

        for i, document_link in enumerate(document_links, start=1):
            # Extract the taskId parameter value from the document link
            document_link_url = document_link.attrib['href']
            query_params = urlparse.parse_qs(urlparse.urlparse(document_link_url).query)
            taskId = query_params.get('taskId', [None])[0]
            if not taskId:
                self.logger.warning(f"Could not extract taskId parameter value from document link: {document_link_url}")
                continue
                
            # Construct the URL of the document page using the taskId parameter value
            document_url = f"document url"
            self.logger.info(f"Extracting data from document: {document_url}")
            
            # Open the document page in a new tab
            response.meta['driver'].execute_script(f"window.open('{document_url}');")
            
            # Switch to the new tab
            response.meta['driver'].switch_to.window(response.meta['driver'].window_handles[-1])
            
            # Wait for the document page to load
            WebDriverWait(response.meta['driver'], 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.view_more_actions'))
            )
            
            # Click the "view more actions" link to get the document title and properties using JavaScript
            view_more_actions_link = response.meta['driver'].find_element(By.CSS_SELECTOR, '.view_more_actions')
            response.meta['driver'].execute_script("arguments[0].click();", view_more_actions_link)
            
            # Wait for the document title and document properties to load
            WebDriverWait(response.meta['driver'], 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.node-info .dark')),
                EC.presence_of_element_located((By.CSS_SELECTOR, '.form-fields'))
            )
            
            # Extract the document title and properties using Scrapy
            document_title = response.css('.node-info .dark::text').get()
            document_properties = response.css('.field-item').getall()
            
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

            # Close the "view more actions" modal using JavaScript
            close_view_more_actions_link = response.meta['driver'].find_element(By.CSS_SELECTOR, '.view-more-actions-modal .icon-close')
            response.meta['driver'].execute_script("arguments[0].click();", close_view_more_actions_link)

            # Go back to the task list page using JavaScript
            response.meta['driver'].execute_script("window.history.back();")

            # Wait for the task list page to load
            WebDriverWait(response.meta['driver'], 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#tasksGridContainer'))
            )

            if i == num_links: # Check if this is the last link
                break # Exit the loop if this is the last link


    def handle_error(self, failure):
        # Log any errors
        self.logger.error(repr(failure))
        
    def closed(self, response):
        self.driver.quit()

