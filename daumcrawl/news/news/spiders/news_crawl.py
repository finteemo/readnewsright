import scrapy
from datetime import datetime, timedelta
from user_agent import generate_user_agent
from urllib.parse import urljoin
from .clean import *
import re

'''
#파일 위치
finance > spiders> news_crawl.py

#가상환경 생성
python = 3.8 버전으로 가상환경 생성

#스크래피 설치
conda install -c scrapinghub scrapy

#필요 라이브러리 설치
pip install hanja
pip install chardet
pip install user_agent

#날짜 변경 _ 각자 본인이 맡은 연도로 수정
start_date = date(2009, 1, 1)
end_date = date(2009, 12, 31)

#스크래피 실행 및 파일 저장(cmd 창에 입력)
scrapy crawl finance -o '파일명'.csv -t csv
'''

headers = {'User-Agent': generate_user_agent(os='win', device_type='desktop')}

class DaumFinanceNewsSpider(scrapy.Spider):
    name = 'politics'
    # allowed_domains = ['finance.naver.com']
    def __init__(self, *args, **kwargs):
        super(DaumFinanceNewsSpider, self).__init__(*args, **kwargs)
        # self.base_url = 'https://finance.naver.com/news/news_search.naver?rcdate=&q=%B1%DD%B8%AE&x=0&y=0&sm=all.basic&pd=4&stDateStart={}&stDateEnd={}&page={}'
        self.base_url = 'https://news.daum.net/breakingnews/politics/{}?page={}&?regDate={}'
        self.current_date = datetime(2009, 1, 1)
        self.end_date = datetime(2009, 1, 27)
        self.current_page = 1
        self.category = {
        ('정치', 'politics') : {
            '행정/지자체':'administration',
            '국회/정당':'assembly',
            '북한': 'north',   
        },
    }

    def start_requests(self):
        #크롤링 시작 url 생성
        date_str = self.current_date.strftime('%Y%m%d')
        for main_ctg in self.CATEGORIES:
            main_name, main_id = main_ctg
            for sub_name, sub_id in self.CATEGORIES[main_ctg].items():
                url = self.base_url.format(sub_id, self.current_page, date_str)
                yield scrapy.Request(url=url, callback=self.parse, headers=headers)

    def parse(self, response):
        # # 기사 목록이 없을 경우 다음 날짜로 넘어감
        # if not response.css('#contentarea_left > div.newsSchResult > dl > dt.articleSubject'):
        #     self.current_date += timedelta(days=1)
        #     #다음 날짜가 종료 날짜 이전일 경우 다시 parse함수 실행
        #     if self.current_date <= self.end_date:
        #         self.current_page = 1
        #         date_str = self.current_date.strftime('%Y-%m-%d')
        #         url = self.base_url.format(date_str, date_str, self.current_page)
        #         yield scrapy.Request(url=url, callback=self.parse, headers=headers)
        #     return

        # 기사 목록이 있을 경우 기사 url 크롤링 진행
        #mArticle > div.box_etc > ul > li:nth-child(1) > div > strong > a
        detail_urls = response.css('#mArticle > div.box_etc > ul > li:nth-child(1) > div > strong > a::attr(href)').getall()
        
        for detail_url in detail_urls:
            try:
                # absolute_url = urljoin('https://finance.naver.com', detail_url)
                absolute_url = detail_url
                yield scrapy.Request(url=absolute_url, callback=self.parse_detail, headers=headers)
            except Exception as e:
                print(e)
                continue

        # 다음 페이지로 넘어감
        # self.current_page += 1
        date_str = self.current_date.strftime('%Y%m%d')
        # next_url = self.base_url.format(sub_id, self.current_page, date_str)
        next_url = re.sub('self.current_page\=\d+', f'self.current_page={self.current_page+1}', response.url)
        yield scrapy.Request(url=next_url, callback=self.parse, headers=headers)

    #상세 뉴스 페이지 내용 크롤링(제목, 날짜, 본문, 신문사)
    def parse_detail(self, response):
        title = response.css('.tit_view::text').get()
        content = response.css('.article_view')[0].xpath('string(.)').extract()[0].strip()
        infos = response.css('.info_view .txt_info')
        if len(infos) == 1:
            writer = ''
            writed_at = infos[0].css('.num_date::text').get()
            edit_writed_at = ''
        elif len(infos) == 2:
            writer = response.css('.info_view .txt_info::text').get()
            writed_at = infos[1].css('.num_date::text').get()
            edit_writed_at = ''
        else:
            writer = response.css('.info_view .txt_info::text').get()
            writed_at = infos[1].css('.num_date::text').get()
            edit_writed_at = infos[2].css('.num_date::text').get()
        
        news_id = response.url.split('/')[-1]
        # 스티커
        news_url = f'https://v.daum.net/v/{news_id}'
        r = requests.get(news_url)
        idx = r.text.find('data-client-id')
        client_id = r.text[idx:idx+100].split()[0].split('"')[-2]

        token_url = "https://alex.daum.net/oauth/token?grant_type=alex_credentials&client_id={}".format(client_id)
        r = requests.get(token_url, headers = {'referer': news_url})
        auth = 'Bearer ' + r.json()['access_token']

        r = requests.get(f'https://action.daum.net/apis/v1/reactions/home?itemKey={news_id}', headers={
            'User-Agent': 'Mozilla/5.0',
            'Authorization': auth
        })
        stickers = r.json()['item']['stats']


        # #클리닝
        # cleaned_title = clean_title(title)
        # cleaned_date = clean_date(date)
        # cleaned_contents = ' '.join(clean_content(c) for c in contents)
        # cleaned_company = clean_company(company)
        # 언론사, 수정일자
        datas = [2, response.meta.pop('main_category'), response.meta.pop('sub_category'), 
                     title, content, response.meta['cp'], 
                     writer, writed_at, edit_writed_at, '', news_url, 
                     news_id, str(stickers)]

        yield {
            'platform' : '다음',
            'main_category': response.meta.pop('main_category'),
            'sub_category': response.meta.pop('sub_category'),
            'title': title,
            'content' : content,
            'company': response.meta['cp'],
            'writer': writer,
            'writed_at': writed_at,
            'edit_writed_at': edit_writed_at,
            'news_url': news_url,
            'news_id': news_id,
            'stickers': str(stickers),
        }

    


        