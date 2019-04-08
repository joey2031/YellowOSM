# -*- coding: utf-8 -*-
import os
import re
import json
import random
import scrapy

CRAWLER_DEPOSITS = "/tmp/crawler_deposits/"

IGNORED_FILES = [
                    ".pdf",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".png",
                    ".tiff",
]
IGNORED_FILES.extend([ft.upper() for ft in IGNORED_FILES])
NO_FOLLOW_LINK = [
                "tel:",
                "mailto:",
                "callto:",
]
TARGETSJSON = "/tmp/osm_crawler_at.jsona" # every line is a valid json string

class YellowosmSpider(scrapy.Spider):
    name = 'yellowosm'
    start_urls = [
        # 'https://love-it.at',
        # 'https://flo.cx',
        # 'https://www.daniellamprecht.com/',
    ]
    allowed_domains = [''.join(domain.split('/')[2]) for domain in start_urls]

    def __init__(self):
        super().__init__()
        self.logger.debug(IGNORED_FILES)

    def start_requests(self):
        """return iterable of requests (scrapy.Request(url,...))
        called only once
        default generates list from start_urls"""
        targets = []
        with open(TARGETSJSON,'r') as myfile:
            for line in myfile.readlines():
                targets.append(json.loads(line))

        for target in targets:
            self.logger.debug(target)
            target = target['labels']
            self.logger.info("will scrape: " + target['website'])

            if 'website' in target:
                website = target['website']
            else:
                self.logger.debug("no website found for OSM_ID: " + str(target['osm_id']))
                # import pdb; pdb.set_trace()
                continue

            if '\\' in website:
                website = website.replace('\\','/')

            website = website if website.startswith("http") else "http://"+website

            url = ''.join(website.split('/')[2])
            url_path = CRAWLER_DEPOSITS + YellowosmSpider.name + "/" + url
            os.makedirs(url_path, exist_ok=True)
            # write known data to dir:
            known_data_path = url_path + "/known_data"
            with open(known_data_path, 'w') as kdfile:
                kdfile.write(json.dumps(target))

            yield(scrapy.Request(website, self.parse))


    def clean_html(self, text):
        newline_remover = re.compile('\n')
        text = re.sub(newline_remover, '', text)
        splitter = re.compile('<.*?>')
        clean_text_snippets = re.split(splitter, text)
        clean_text_snippets = [snip for snip in clean_text_snippets if snip]
        return clean_text_snippets


    def close(self):
        self.logger.debug("DONE! :D")

    def parse(self, response):

        url = ''.join(response.url.split('/')[2])
        path = '_'.join(response.url.split('/')[3:])
        # mkdir with url as dir
        url_path = CRAWLER_DEPOSITS + YellowosmSpider.name + "/" + url
        os.makedirs(url_path, exist_ok=True)

        contact_path = url_path + "/yosm_contact" + "_" + path
        strings_path = url_path + "/yosm_strings" + "_" + path
        hrefs_path = url_path + "/yosm_hrefs" + "_" + path

        dom_path = url_path + '/' + path
        if path == "":
            path = "index"
            dom_path = url_path + '/' + path

        # dump DOMS there
        self.logger.debug("dom_path: " + dom_path)
        with open(dom_path, 'w') as dom_file:
            dom_file.write(response.text)
        tels = []
        mails = []
        for href in response.xpath('//a/@href').getall():
            if href.startswith("mailto:"):
                mails.append(href)
            if href.startswith("tel:"):
                tels.append(href)

        with open(hrefs_path, 'w') as hrefs_file:
            for href in response.xpath('//a/@href').getall():
                hrefs_file.write(href + "\n")

        with open(strings_path, 'w') as strings_file:
            for text in self.clean_html(response.text):
                strings_file.write(text.strip() + "\n")


        self.logger.debug("contact_path: " + contact_path)
        if mails or tels:
            with open(contact_path, 'w') as contact_file:
                for mail in mails:
                    contact_file.write(mail + "\n")
                for tel in tels:
                    contact_file.write(tel + "\n")

        for href in response.xpath('//a/@href').getall():
            for el in IGNORED_FILES:
                if href.endswith(el):
                    continue
            for el in NO_FOLLOW_LINK:
                if href.startswith(el):
                    continue
            yield scrapy.Request(response.urljoin(href), self.parse)