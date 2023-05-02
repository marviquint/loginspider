import scrapy

class GithubSpider(scrapy.Spider):
    name = 'github'

    def start_requests(self):
        yield scrapy.Request('https://github.com/login', callback=self.login)

    def login(self, response):
        # Extract the authenticity token from the login page
        token = response.css('input[name="authenticity_token"]::attr(value)').get()

        # Prepare the login form data
        data = {
            'commit': 'Sign in',
            'utf8': '✓',
            'authenticity_token': token,
            'login': 'username',
            'password': 'password',
        }

        # Submit the login request
        yield scrapy.FormRequest.from_response(response, formdata=data, callback=self.after_login)

    def after_login(self, response):
        # Check if the login was successful
        if response.xpath('//a[contains(@class, "Header-link")]/@href'):

            # If the login was successful, navigate to the user's repositories page
            username = response.css('a.Header-link::text').get()
            yield scrapy.Request(f'https://github.com/{username}?tab=repositories', callback=self.parse_repositories)
        else:
            self.logger.error('Login failed')

    def parse_repositories(self, response):
        # Extract information about the user's repositories
        for repository in response.css('li.col-12'):
            data = {
                'name': repository.css('a::text').get(),
                'url': response.urljoin(repository.css('a::attr(href)').get()),
                'description': repository.css('p::text').get(),
            }
            print({
                'name': repository.css('a::text').get(),
                'url': response.urljoin(repository.css('a::attr(href)').get()),
                'description': repository.css('p::text').get(),
            })

