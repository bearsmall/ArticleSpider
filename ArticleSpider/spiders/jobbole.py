# -*- coding: utf-8 -*-
import datetime
import scrapy
import re
from scrapy.http import Request
from urllib import parse
from ArticleSpider.items import JobBoleArticleItem
from ArticleSpider.utils.common import get_md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        """
        1. 获取文章列表中的文章URL并交给scrapy下载后进行解析
        2. 获取下一页的URL并交给scrapy进行下载，下载完成后交给parse
        """

        # 解析列表中的所有文章URL并交给scrapy下载后进行解析
        post_nodes = response.css("#archive div.floated-thumb div.post-thumb a")
        for post_node in post_nodes:
            front_image_url = post_node.css("img::attr(src)").extract_first("")
            front_image_url = parse.urljoin(response.url, front_image_url)
            post_url = post_node.css("::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": front_image_url},
                          callback=self.parse_detail)
        # 提前下一页URL，并交给scrapy进行下载
        next_urls = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_urls:
            yield Request(url=parse.urljoin(response.url, next_urls), callback=self.parse)
        pass

    def parse_detail(self, response):
        # self.xpath(response)
        # self.css(response)
        yield from self.cssParser(response)

    def cssParser(self, response):
        article_item = JobBoleArticleItem()
        front_image_url = response.meta.get("front_image_url", "")  # 文章封面图
        title = response.css("div.entry-header h1::text").extract_first()
        create_date = response.css(".entry-meta-hide-on-mobile::text").extract_first()
        create_date = create_date.strip().replace("·", "").strip()
        praise_num = response.css(".vote-post-up h10::text").extract_first()
        favorite_num = response.css(".bookmark-btn::text").extract_first()
        match_re = re.match(".*?(\d+).*", favorite_num)
        if match_re:
            favorite_num = int(match_re.group(1))
        else:
            favorite_num = 0
        comment_num = response.css("a[href='#article-comment'] span::text").extract_first()
        match_re = re.match(".*?(\d+).*", comment_num)
        if match_re:
            comment_num = int(match_re.group(1))
        else:
            comment_num = 0
        content = response.css("div.entry").extract_first()
        tags = response.css("p.entry-meta-hide-on-mobile a::text").extract()
        tags = [element for element in tags if not element.strip().endswith("评论")]
        tags = ",".join(tags)
        article_item["url_object_id"] = get_md5(response.url)
        article_item["title"] = title
        article_item["url"] = response.url
        try:
            create_date = datetime.datetime.strptime(create_date, "%y/%m/%d").date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        article_item["create_date"] = create_date
        article_item["front_image_url"] = [front_image_url]
        article_item["praise_num"] = praise_num
        article_item["fav_num"] = favorite_num
        article_item["comment_num"] = comment_num
        article_item["content"] = content
        article_item["tags"] = tags
        yield article_item

    # xpath选择器
    def xpath(self, response):
        title = response.xpath('//*[@class="entry-header"]/h1/text()').extract_first()
        create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract_first()
        create_date = create_date.strip().replace("·", "").strip()
        praise_num = response.xpath('//span[contains(@class,"vote-post-up")]/h10/text()').extract_first()
        praise_num = int(praise_num)
        favorite_num = response.xpath('//span[contains(@class,"bookmark-btn")]/text()').extract_first()
        match_re = re.match(".*?(\d+).*", favorite_num)
        if match_re:
            favorite_num = int(match_re.group(1))
        else:
            favorite_num = 0
        comment_num = response.xpath('//a[@href="#article-comment"]/span/text()').extract_first()
        match_re = re.match(".*?(\d+).*", comment_num)
        if match_re:
            comment_num = int(match_re.group(1))
        else:
            comment_num = 0
        content = response.xpath('//div[@class="entry"]').extract_first()
        tags = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        tags = [element for element in tags if not element.strip().endswith("评论")]
        tags = ",".join(tags)
        print(title, create_date, praise_num, favorite_num, comment_num, tags)
