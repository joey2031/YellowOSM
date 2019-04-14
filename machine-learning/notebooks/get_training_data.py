#!/usr/bin/python3
"""Get data from crawler directory, clean them up and print them out as json"""
import os
import json

CRAWLER_DIR="/tmp/crawler_deposits/yellowosm/"
# KNOWLEDGE = "known_data"
KNOWLEDGE_PATH = CRAWLER_DIR +"{url}/known_data"
WEBCRAWLDATA_STRINGS = CRAWLER_DIR +"{url}/yosm_strings_"
STRINGSFILE_PREFIX = "yosm_strings_"
MAX_LENGTH = 50

class Business():
    def __init__(self, url):
        self.matched = False # matched phone number on website
        self.url = url
        self.not_phone = [] # list of non-phone number strings
        self.osm_id = self._get_osm_id()
        self.osmphone = self._read_osmphone_data()
        self.osmphone_clean = self._clean_phone_number(self.osmphone)
        self.webphone = self._cleanup_web_string()
        self.webphone_clean = self._clean_phone_number(self.webphone)
        self._find_web_phone_string()
    def pretty_print(self):
        s =  "url:     " + str(self.url) + " osm_id:  " + str(self.osm_id) + "\n"
        s += "website: " + str(self.webphone) + "\n"
        s += "osm:     " + str(self.osmphone)
        return s
    def get_array(self):
        d = []
        d.append({'osm_id': str(self.osm_id)})
        d[0]['phone_web'] = str(self.webphone)
        d[0]['phone_osm'] = str(self.osmphone)
        d.append(self.not_phone)
        return d

    def _get_osm_id(self):
        with open(KNOWLEDGE_PATH.format(url=self.url),'r') as inputfile:
            data = json.loads(inputfile.read())
            return data['osm_id'] if 'osm_id' in data else None
    def _read_osmphone_data(self):
        with open(KNOWLEDGE_PATH.format(url=self.url),'r') as inputfile:
            data = json.loads(inputfile.read())
            phone = data['phone'] if 'phone' in data else None
            return phone
    def _clean_phone_number(self, number):
        phone = number
        if not number:
            return None
        # phone = phone.strip(["/"," ","-","(",")"])
        phone = phone.replace(" ", "")
        phone = phone.replace("/", "")
        phone = phone.replace("-", "")
        phone = phone.replace("(0)", "")
        phone = phone.replace("(", "")
        phone = phone.replace(")", "")
        return phone
    def _cleanup_web_string(self):
        # files = os.listdir((CRAWLER_DIR+"{url}").format(url=self.url))
        # # print(files)
        # for f in files:
        f = WEBCRAWLDATA_STRINGS.format(url=self.url)
        with open(f,'r') as inputfile:
            for line in inputfile.readlines():
                if ("Tel" in line or line.startswith('tel')) and len(line) < MAX_LENGTH:
                    # print(line)
                    return line.strip()
            else:
                return None
    def __get_substrings(self, string, size=3):
        for index in range(0,len(string)+1-size):
            yield(string[index:index+size])
    def _get_all_site_strings(self):
        files = os.listdir((CRAWLER_DIR+"{url}").format(url=self.url))
        # print(files)
        for f in files:
            if f.startswith(STRINGSFILE_PREFIX):
                with open((CRAWLER_DIR+"{url}/").format(url=self.url)+f,'r') as myf:
                    for line in myf.readlines():
                        if line.strip() and len(line.strip()) < MAX_LENGTH and \
                            len(line.strip()) > 3:
                            yield(line.strip())

    def _find_web_phone_string(self):
        phone_substrings = self.__get_substrings(self.osmphone_clean, size=4)
        phone_substrings = [i for i in phone_substrings]
        # for
        #     if i in
        #     for i in phone_substrings:
        #     print(i)
        strings = self._get_all_site_strings()
        # for s in strings:
        #     print(s)
        for s in strings:
            # print(s)
            count = 0
            orig_s = s
            s = self._clean_phone_number(s)
            orig_s = orig_s.strip()
            for i in phone_substrings:
                if i in s:
                    count += 1
            if count > 3:
                self.matched = True
                # if count == 4:
                #     print("="*20 + " MATCH " + "="*20)
                self.webphone = s
                return # found phone number, k thx bye
            else:
                # is not a phone number...
                self.not_phone.append(orig_s)




# get dirs in crawler dir
urls = os.listdir(CRAWLER_DIR)
# print(urls)
all_data = []
# print every url in crawler dir
for url in urls:
    try:
        b = Business(url)
        if b.webphone == None or not b.matched:
            continue
        #print(b)
        #print("="*75)
        all_data.append(b.get_array())
        # print(b.url)
    # except ValueError as e:
    except FileNotFoundError as e:
        pass

print(json.dumps(all_data))
# print(len(all_data))