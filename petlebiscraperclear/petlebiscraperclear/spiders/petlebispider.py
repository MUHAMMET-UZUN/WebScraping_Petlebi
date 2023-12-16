import scrapy
import json
from petlebiscraperclear.items import  PetlebiItem

class PetlebiSpider(scrapy.Spider):
    name = "petlebispider"
    allowed_domains = ["www.petlebi.com"]
    start_urls = ["https://www.petlebi.com/"]
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,  # Limit the number of concurrent requests
        'DOWNLOAD_DELAY' : 2, # You can adjust this value
    }

    custom_settings = {
        'FEEDS':{
            'petlebi_data.json' : {'format':'json','overwrite':True}
        }
    }

    def __init__(self):
        self.previous_urls = set()
        self.iteration_count = 0
        self.output_data = []

    def parse(self, response):
        self.iteration_count += 1
        product_urls = response.css("div.wstheading.clearfix a")

        for product_url in product_urls:
            url = product_url.attrib["href"]

            if url in ["https://www.petlebi.com/", "https://www.petlebi.com", "", None]:
                continue

            if url in self.previous_urls:
                continue

            self.previous_urls.add(url)

            if self.iteration_count % 3 == 0:
                # Wait for 3 previous URL requests to finish
                for previous_url in self.previous_urls:
                    yield scrapy.Request(previous_url, callback=self.parse_product_page)

            first_page_url = f"{url}?page=1"
            yield response.follow(first_page_url, callback=self.parse_product_page, meta={'url': url})

    def parse_product_page(self, response):
        # Extract next page URL
        next_page_url = response.css("#pagination_area ul li:last-child a::attr(href)").extract_first()

        #products on each page
        cart = response.css("div.col-lg-4.col-md-4.col-sm-6.search-product-box")

        for product in cart:
            #product's url
            product_link = product.css("a::attr(href)").extract_first()

            yield response.follow(product_link, callback=self.parse_product_info)

        # Follow the next page link
        if next_page_url is not None:
            yield response.follow(next_page_url, callback=self.parse_product_page, meta={'url': response.meta['url']})

    def parse_product_info(self, response):
        petlebi_item = PetlebiItem()

        #description part has many <p> tag.
        product_description = ""
        _description = response.css("div.tab-pane.active.show p::text")
        for part in _description:
            product_description += part.get()

        petlebi_item['product_url'] = response.xpath("/html/head/link[2]").attrib["href"]
        petlebi_item['product_name'] = response.css(".product-h1::text").get()
        petlebi_item['product_barcode'] = response.xpath("//*[@id='hakkinda']/div[2]/div[2]/text()").get()
        petlebi_item['product_image'] = response.css("div.row.product-detail-main .col-md-6.col-sm-5 a")[0].attrib["href"]
        petlebi_item['product_description'] = product_description
        petlebi_item['product_category'] = response.xpath("/html/body/div[3]/div[1]/div/div/div[1]/ol/li[3]/a/span/text()").get()
        petlebi_item['product_brand'] = response.css("div.row.mb-2.brand-line a::text").get()
        petlebi_item['product_new_price'] = response.css(".new-price::text").get()
        petlebi_item['product_old_price'] = response.css(".old-price::text").get()
        petlebi_item['product_stock'] = ''  # I couldn't find these attributes
        petlebi_item['sku'] = ''
        petlebi_item['productID'] = ''
        yield petlebi_item