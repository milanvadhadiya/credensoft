import json
import re
import requests
from scrapy import Selector


class chewy():

    def normalize_whitespace(self, string):
        return re.sub(r'(\s)\1{1,}', r'\1', string)


    def normalize_space(self, name):
        return self.normalize_whitespace(
            str(name).replace('\\n', '').replace('\\\\n', '').replace('\\t', '').replace('\\\\t', '').replace('\n',
                                                                                                              '').replace(
                '\t', '').replace('\\r', '').replace('\\\\r', '').replace('\r', '').replace('\xa0', '')).strip()

    def __init__(self):

        self.session = requests.Session()
        self.base_url = 'https://www.chewy.com'
        self.main_link = 'https://www.chewy.com/b/dog-288'
        self.category_link = 'https://www.chewy.com/b/dog-288'
        self.product_link = 'https://www.chewy.com/pedigree-adult-complete-nutrition/dp/141438'

        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'referer': 'https://www.chewy.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }

        res = self.session.get(self.main_link, headers=self.headers)
        self.response = Selector(text=res.text)

        self.wet_category = self.base_url + self.response.xpath(
            '//div[@class="container"]//h3/a[contains(text(),"Food")]/../following-sibling::div//li/a[contains(text(),"Wet Food")]/@href').get()

    def categories(self):

        all_categories = self.response.xpath(
            '//div[@class="container"]//h3/a[contains(text(),"Food")]/../following-sibling::div//li/a/text()').getall()[
                         :-1]
        category_count = 0
        for category_name in all_categories:
            category_count += 1
            print(f"category {category_count} : ", category_name)

    def category_product_link(self):

        res = self.session.get(self.wet_category, headers=self.headers)
        resp = Selector(text=res.text)

        product_urls = resp.xpath('//*[@class="product"]/@href').getall()
        for product_url in product_urls:
            if 'http' not in product_url:
                product_url = 'https://www.chewy.com' + product_url
            print(product_url)

        self.wet_category = self.base_url + resp.xpath(
            '//*[@class="pagination_selection cw-pagination__next "]/@href').get()

        while self.wet_category:
            self.category_product_link()

    def number_of_page(self, link):

        res = self.session.get(link, headers=self.headers)
        resp = Selector(text=res.text)

        try:
            page = resp.xpath('//*[@class="pagination_selection cw-pagination__item "]/text()').getall()[-1]
        except:
            page = 1

        print(f"There was {page} page in this category")

    def final_data(self):

        item = {}

        res = self.session.get(self.product_link, headers=self.headers)
        resp = Selector(text=res.text)

        product_name = self.normalize_space(resp.xpath('//div[@id="product-title"]/h1/text()').get())
        brand = resp.xpath('//div[@id="product-subtitle"]/a/span/text()').get()
        description = self.normalize_space(
            resp.xpath('//*[@class="descriptions__content cw-tabs__content--left"]/span/p/text()').get())
        key_benifit = self.normalize_space(
            ' '.join(resp.xpath('//span[@class="cw-type__h2"]/following-sibling::ul/li/text()').getall()))

        js = json.loads(
            resp.xpath('//*[@id="vue-portal__sfw-attribute-buttons"]/@data-attributes').get().replace('&quot;', '"'))
        js1 = res.text.split('var itemData =')[1].split(';')[0]
        images = re.findall("//img.chewy.com(.*?)',", js1)
        product_image = []
        for image in images:
            product_image.append('//img.chewy.com' + image)

        price_dict = {}
        sizes = []
        for attr in js[0]['attributeValues']:
            size = attr['value']
            sizes.append(size)
            price_dict[size] = attr['sku']['price']

        Ingredients = ''
        attr_checks = js[0]['attributeValues'][0]['sku']['attribute']
        for attr_check in attr_checks:
            attr_ingre = attr_check['name']
            if attr_ingre == 'Ingredients':
                Ingredients = self.normalize_space(attr_check['value'][0]['value'])

        category = ', '.join(resp.xpath('//*[@itemprop="itemListElement"]//span/text()').getall())

        item['ProductName'] = product_name
        item['Description'] = description
        item['Size'] = ','.join(sizes)
        item['Ingredients'] = Ingredients
        item['Images'] = product_image
        item['Categories'] = category
        item['Key Benefits'] = key_benifit
        item['Brand'] = brand
        item['Price'] = price_dict
        print(item)


chewy = chewy()
# chewy.categories()
# chewy.category_product_link()
# chewy.number_of_page('https://www.chewy.com/b/wet-food-293')
# chewy.final_data()
