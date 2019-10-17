#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
################################################################################
#
#    Copyright 2017 Félix Brezo and Yaiza Rubio (i3visio, contacto@i3visio.com)
#
#    This file is part of Pycloner. You can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero  General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################


import hashlib
import os
import requests
import shutil
import sys
from fake_useragent import UserAgent 

from bs4 import BeautifulSoup

from pycloner.utils import error, warning, success, info, safelyCreateDirectories
from pycloner.dbInstance import dbSingle
import time

class CrawlerInitializationException(Exception):
    def __init__(self, message="Crawler instance could not be done."):
        self.message = error(message)


class CrawlingException(Exception):
    def __init__(self, message="Something happened when cloning the website."):
        self.message = error(message)


class Crawler():
    # Defining static variables
    visited_links = []
    error_links = []
    max_deep_level = 1


    def __init__(self, url, project_name="website_crawled", data_folder="./tmp", deep_level=None):
        # Verifying if the instance is correct
        if not self._isUrl(url):
            raise CrawlerInitializationException("The URL provided ('"  + url + "') is not a valid URL.")

        # Initializing the variables
        self.original_url = url                             # http://example.com/index.html
        self.site_name = self.original_url.split("/")[2]    # example.com
        self.base_url = self._getBaseUrl(self.original_url) # http://example.com/
        self.project_name = project_name
        self.data_folder = data_folder
        self.project_path = os.path.join(self.data_folder, self.project_name)
        # self.ua = UserAgent().random
        # self.header = {"User-Agent":UserAgent().random,
        # "cookie":"_ga=GA1.2.2028114516.1544012438; _gid=GA1.2.1035883623.1545824560; wordpress_test_cookie=WP+Cookie+check; wordpress_logged_in_dab6060be3245b934689b7ec8bb2feab=xcodest%7C1547034170%7C11YBH6tFBiweH9tqF3PjcABjocZQAWhMuUv9WRZLNOH%7C064a8bac841ab9dd847bcb2d0baa832c8881c2180d6ef8d1b153815c14088ba8"
        # }
        self.header = {"User-Agent":UserAgent().random
        }
        self.session = requests.Session()

        try:
            safelyCreateDirectories(self.project_path, type="DIRECTORY")
        except:
            raise CrawlerInitializationException("The project path ('"  + self.project_path + "') could not be created.")
        # Setting the deep level
        if deep_level != None:
            Crawler.max_deep_level = deep_level


    def _isUrl(self, url):
        """Private method that verifies whether an URL is an URL.
        """
        if "http://" not in url and "https://" not in url:
            return False
        return True


    def _getBaseUrl(self, url):
        """Private method that gets the base for an URL.
        """
        parts = url.split("/")
        return parts[0] + "//" + parts[2] + "/"


    def _getUrlHash(self, url):
        """An auxiliary method that calculates the SHA256 hash of the Url provided.
        """
        return hashlib.sha256(url.encode('utf-8')).hexdigest()


    def _buildFullUrl(self, url):
        """Method that encapsulates the creation of URL.
        """
        if url:
            clean_url = url.split("#")[0]
            if self._isUrl(clean_url):
                return clean_url
            elif url[0] not in [".", "/"]:
                return self.original_url.rsplit("/", 1)[0] + clean_url
            else:
                # Eliminating any '/' at the beginning
                while url[0] == "/":
                    url = url[1:]
                return self.base_url + clean_url

        raise CrawlingException(warning("Could not create a valid URL for the URL seen '" + str(url) + "' as seen in " + str(self.original_url)))


    def _save(self, bs, element, folder_path, check=None):
        """Method that iterates over HTML so as to find a given element and collect them.
        """
        links = bs.find_all(element)

        for l in links:
            # Catching the href for most elements which is in <script href="…"
            if element != "img":
                href = l.get("href")
            # Catching the href for images which is in <img src="…"
            else:
                href = l.get("src")

            if href is not None and href not in Crawler.visited_links:
                if check == None or check != None and check in href :
                    # print(info("Working with: {}".format(href)))
                    if "//" in href:
                        path_s = href.split("/", 3)
                        file_name = path_s[3]
                    elif href[0] == "/":
                        file_name = href[1:]

                    l = os.path.join(self.base_url, file_name)
                    try:
                        if element != "img":
                            # r = requests.get(l)
                            r = self.session.get(l,headers = self.header)
                        # Saving images
                        else:
                            # r = requests.get(l, stream=True)
                            r = self.session.get(l,stream=True,headers = self.header)
                    except requests.exceptions.ConnectionError:
                        Crawler.error_links.append(l)
                        continue

                    if r.status_code != 200:
                        Crawler.error_links.append(l)
                        print(warning("Status code for " + l + " is: " + str(r.status_code)))
                        break

                    try:
                        file_path = os.path.join(folder_path, file_name.split("?")[0].split("#")[0])
                        # Check the existence of the folder structure
                        safelyCreateDirectories(file_path)
                    except:
                        print(error("We could not create the directory tree for: " + file_path))

                    print(info("Saving asset at {}".format(file_path)))
                    if element != "img":
                        with open(file_path, "wb") as f:
                            f.write(r.text.encode('utf-8'))
                            f.close()
                    # Saving images
                    else:
                        with open(file_path, "wb") as f:
                            shutil.copyfileobj(r.raw, f)

                    Crawler.visited_links.append(l)


    def _save_assets(self, html_text, folder_path):
        """Saving the assets from an HTML text.
        """
        bs = BeautifulSoup(html_text, "html.parser")

        # Saving CSS
        self._save(bs=bs, element="link", check=".css", folder_path=folder_path)

        # Saving Javascript
        self._save(bs=bs, element="script", check=".js", folder_path=folder_path)

        # Saving the rest of the images
        self._save(bs=bs, element="img", folder_path=folder_path)


    def crawl(self, link=None, full_website=True, current_level=0):
        """Main crawling function. It receives a link to be crawled and is recursive. If none is provided the original_url of the class will be used.
        """
        if not link:
            link = self.original_url

        # Method needed to create relative URL when called recursively
        if "http://" not in link and "https://" not in link:
            link = self.base_url + link

        if "hacked.com" in link == False:
            return
        if "login" in link:
            return
        if "logout" in link:
            return
        # if dbSingle.checkUrlCanAdd(link) == False:
        #     print('++++++ this url exists')
        #     return
        # time.sleep(3)

        if self.site_name in link and link not in Crawler.visited_links:
            # print(info("Crawling level: " + str(current_level) + ". Working with: {}".format(link)))

            # Recovering the resource
            try:
                # r = requests.get(link)
                r = self.session.get(link,headers = self.header)
            except requests.exceptions.ConnectionError:
                raise CrawlingException("Connection error when requesting " + link)

            try:
                if r.status_code != 200:
                    raise CrawlingException("Invalid response when requesting " + link)
            except Exception as e:
                print(error(e.message))

            # Building the current URL folder
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string
            # current_url_folder = os.path.join(self.project_path,  title+"_"+ self._getUrlHash(link))
            # current_url_folder = os.path.join(self.project_path,  title)
            current_url_folder =  self.project_path
            # print("current_url_folder = "+current_url_folder)
            try:
                safelyCreateDirectories(current_url_folder, type="DIRECTORY")
            except:
                raise CrawlerInitializationException("The path for the current website ('"  + current_url_folder + "') could not be created.")

            # Get the file name after https?://
            if link.count("/") <= 2:
                # file_name = "index.html"
                file_name = title+".html"
            elif link.count("/") == 3 and link[-1] == "/":
                # file_name = "index.html"
                file_name = title+".html"
            else:
                file_name = link.split("/", 3)[3]
                if file_name[-1] == "/":
                    # file_name += "index.html"
                    file_name = title+".html"

            # Check to avoid file names starting with / which create a conflict when trying to join paths
            while file_name[0] == "/":
                file_name = file_name[1:]

            file_path = os.path.join(current_url_folder, file_name)
            # print("file_path = "+file_path)
            try:
                safelyCreateDirectories(file_path)
            except:
                raise CrawlerInitializationException("The path for the current website ('"  + file_path + "') could not be created.")

            # Saving the crawled file
            # zb remove
            # with open(file_path, "wb") as f:
            #     print("self.site_name = ",self.site_name)
            #     print("self.project_path = ",self.project_path)
            #     # Replacing any reference  to the website to a local instance of the crawled data
            #     text = r.text.replace("https://hacked.com", ".")
            #     f.write(text.encode('utf-8'))
            #     f.close()

            #     print(info("Crawled file:\t" + file_path))

            # Adding the link to the visited links
            Crawler.visited_links.append(link)

# zb remove
            # if full_website:
            #     # Saving the assets found in the text recovered
            #     self._save_assets(r.text, current_url_folder)

            # Collecting more resources in deep
            if current_level < self.max_deep_level:
                # soup = BeautifulSoup(r.text, "html.parser")

                # Iterating again through all the elements in the HTML website to get new links
                tags = soup.find_all('a')
                for i, link in enumerate(tags):
                    href = link.get("href")
                    if href != "/":
                        try:
                            # Building the url from the given href
                            print(href)
                            if href == "#":
                                continue
                            new_link = self._buildFullUrl(href)
                            # print(new_link)

                            # print(info("Starting a new crawling process " + str(i+1) + "/" + str(len(tags)) + " for " + href))

                            # Instatiating the crwaler
                            # zb remove
                            new_crawler = Crawler(new_link, self.project_name, self.data_folder)
                            # Starting the crawling process
                            new_crawler.crawl(current_level=current_level+1)
                        except CrawlerInitializationException as e:
                            print(e.message)
                            break
                        except Exception as e:
                            print(e)
                            break
                        # print(success("Finished crawling for " + new_link))
                        # print(new_link)
                        # dbSingle.insertUrlIntoDB(new_link)
