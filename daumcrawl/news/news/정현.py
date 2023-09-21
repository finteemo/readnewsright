import scrapy
import time
import csv
from daum_scrapy.items import DaumPoliticsItem
import logging
class DaumNewsSpider(scrapy.Spider):
    name = "daum_news"
    allowed_domains = ["news.daum.net"]
    # start_urls = ["https://news.daum.net"]
    def start_requests(self):
        pageNum = 2#0
        sub_categories =['others'] #['administration', 'assembly', 'north', 'others', 'dipdefen', 'president']
        date = ['20230801']
        for sub_category in sub_categories:
            # item = DaumPoliticsItem()
            # item['sub_category']=sub_category
            for day in date:
                for i in range(1, pageNum, 1):
                    yield scrapy.Request(url="https://news.daum.net/breakingnews/politics/{}?page={}&regDate={}".format(sub_category, i, day),
                                        callback = self.parse_news)
    def parse_news(self, response):
        for sel in response.xpath('//*[@id="mArticle"]/div[3]/ul/li/div'):
            item = DaumPoliticsItem()
            item['source'] = sel.xpath('strong/span[@class="info_news"]/text()').extract()[0]
            item['url'] = sel.xpath('strong[@class="tit_thumb"]/a/@href').extract()[0]
            item['category'] = '정치'
            item['title']= sel.xpath('strong[@class="tit_thumb"]/a/text()').extract()[0]
            yield item