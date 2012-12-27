#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import urlparse
import markdown
from jinja2 import Template
import BaseHTTPServer
import os
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

xpress_index = "index"

current_dir = os.path.dirname(os.path.abspath(__file__))
www_path = os.path.join(current_dir, 'www')
ui_path  = os.path.join(current_dir, 'ui')
tpl_path = os.path.join(current_dir, 'tpl')

config_info = load(open(os.path.join(www_path, '.xpressrc'), 'r').read().decode("utf8"), Loader=Loader)

class Xpress(object):
    def scan_dir(self, dir):
        result = []
        yid = os.walk(dir)
        for rootDir, pathList, fileList in yid:
            for file in fileList:
                print rootDir
                print file
                #filter the vi and emacs swap file,
                #other editor? sorry, we only support vi or emacs
                if self.filter_path(rootDir) and self.filter_path(file):
                    result.append(os.path.join(rootDir, file))
        return result

    def sort_file_by_ctime(self, file_list, sort_reverse=True):
        file_dict = {}
        for file in file_list:
            file_stat = os.stat(file)
            file_dict[file]=file_stat.st_ctime
        file_sorted_list = sorted(file_dict, key=file_dict.__getitem__, reverse=sort_reverse)
        print file_sorted_list
        return file_sorted_list

    def filter_path(self, path):
        basepath = os.path.basename(path)
        return not (basepath.startswith(".") or basepath.startswith("#"))

    def read_article(self, article_path):
        if os.path.isfile(article_path):
            fd = open(article_path, 'r')
            content = fd.read().decode("utf8")
            content_unit = content.split('\n\n', 3)
            meta = load(content_unit[0], Loader=Loader)
            option = load(content_unit[1], Loader=Loader)
            article_title = content_unit[2]
            article_content = markdown.markdown(content_unit[3])
            return meta, option, article_title, article_content
        else:
            return "", "", "", ""

class Index():
    def get_index(self, dir):
        xpress = Xpress()
        file_list = xpress.scan_dir(dir)
        file_sorted_list = xpress.sort_file_by_ctime(file_list)
        relpath_list = []
        for file in file_sorted_list:
            file_relpath = os.path.relpath(file, dir)
            #exclude the index page at the www root
            if dir == www_path:
                if file_relpath != xpress_index:
                    relpath_list.append(file_relpath)
            else:
                relpath_list.append(file_relpath)
        return relpath_list

class MakeIndexPage():
    def website_index_page(self, file_list, tpl_var):
        (page_start_point, page_end_point, pre_page_flag, pre_page, next_page_flag, next_page) = tpl_var
        if page_start_point >= len(file_list) or page_end_point >= len(file_list):
            #start 从0开始
            print "something happend"
            return
            #TODO Exception
        xpress = Xpress()
        index_info = []
        for file_index in range(page_start_point, page_end_point + 1):
            file = file_list[file_index]
            article_file = os.path.join(www_path, file)
            print article_file

            meta_info, option_info, article_title, article_content = xpress.read_article(article_file)
            url = "/" + file
            #TODO
            article_info = {"url" : url,
                            "meta" : meta_info,
                            "option" : option_info,
                            "article" : article_content,
                            "title" : article_title,
                            "summary" : article_content[0:80]}
            index_info.append(article_info)

        tpl = open(os.path.join(tpl_path, xpress_index + '.html'), 'r').read().decode("utf8")
        index_hero_article =os.path.join(www_path, xpress_index)
        _, _, _, index_hero_unit = xpress.read_article(index_hero_article)
        config_info = load(open(os.path.join(www_path, '.xpressrc'), 'r').read().decode("utf8"), Loader=Loader)

        template = Template(tpl)
        html = template.render(config=config_info, index=index_info, hero_unit=index_hero_unit, pre_page_flag=pre_page_flag, pre_page=pre_page, next_page_flag=next_page_flag, next_page=next_page)
        return html

    def category_index_page(self, file_list, category_path, tpl_var):
        (page_start_point, page_end_point, pre_page_flag, pre_page, next_page_flag, next_page) = tpl_var
        if page_start_point >= len(file_list) or page_end_point >= len(file_list):
            #start 从0开始
            print "something happend"
            return
            #TODO Exception
        xpress = Xpress()
        index_info = []
        for file_index in range(page_start_point, page_end_point + 1):
            file=file_list[file_index]
            article_file = os.path.join(category_path, file)
            print article_file

            meta_info, option_info, article_title, article_content = xpress.read_article(article_file)
            url = '/' + os.path.relpath(article_file, www_path)
            print url
            #TODO
            article_info = {"url" : url,
                            "meta" : meta_info,
                            "option" : option_info,
                            "article" : article_content,
                            "title" : article_title,
                            "summary" : article_content[0:80]}
            index_info.append(article_info)

        tpl = open(os.path.join(tpl_path, 'category.html'), 'r').read().decode("utf8")
        index_hero_article =os.path.join(category_path, xpress_index)
        _, _, _, index_hero_unit = xpress.read_article(index_hero_article)
        config_info = load(open(os.path.join(www_path, '.xpressrc'), 'r').read().decode("utf8"), Loader=Loader)

        template = Template(tpl)
        html = template.render(config=config_info, index=index_info, hero_unit=index_hero_unit, pre_page_flag=pre_page_flag, pre_page=pre_page, next_page_flag=next_page_flag, next_page=next_page)
        return html

class WebRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        #TODO DEBUG
        print self.path
        self.xpress_url = urlparse.urlparse(self.path)
        #TODO DEBUG
        print self.xpress_url
        self.xpress_url_params = urlparse.parse_qs(urlparse.urlparse(self.path).query)
        self.xpress_request_path = os.path.join(www_path, self.xpress_url.path[1:])
        if os.path.isfile(self.xpress_request_path) or self.xpress_url.path == '/':
            #if the request page is the index page
            if self.xpress_url.path == '/' or self.xpress_url.path == '/index':
                page_size = 5
                index = Index()
                index_file_list = index.get_index(www_path)
                #TODO 
                print len(index_file_list)
                page_num = int((len(index_file_list) + page_size -1) / page_size)
                if not self.xpress_url_params.has_key("page"):
                    page_param = 0
                else:
                    #TODO
                    print self.xpress_url_params["page"]
                    page_param = int(self.xpress_url_params["page"][0])
                #TODO
                print "$$$$$"
                print page_param
                print page_num
                if page_param < page_num - 1:
                    page_start_point = page_param * page_size
                    page_end_point = (page_param + 1) * page_size - 1
                elif page_param == page_num - 1:
                    page_start_point = page_param * page_size
                    page_end_point = len(index_file_list) - 1
                else:
                    #TODO 
                    print "hacker"
                    return
                if page_param == 0:
                    pre_page_flag = 0
                    pre_page = 0
                else:
                    pre_page_flag = 1
                    pre_page = page_param - 1
                if page_param == page_num -1 :
                    next_page_flag = 0
                    next_page = 0
                else:
                    next_page_flag = 1
                    next_page = page_param + 1

                print "%%%%"
                print page_start_point
                print page_end_point
                #print index_file_list
                make_index_page = MakeIndexPage()
                tpl_var = (page_start_point, page_end_point, pre_page_flag, pre_page, next_page_flag, next_page)
                page_content = make_index_page.website_index_page(index_file_list, tpl_var)
                #print page_content
                html = page_content
            else:
                xpress = Xpress()
                if not xpress.filter_path(self.xpress_request_path):
                    print "~~~~~~~~~~~~~~~~~~~~~~"
                    self.send_error(404)
                    return
                else:
                    article_file = self.xpress_request_path
                    meta_info, option_info, article_title, article_content = xpress.read_article(article_file)
                    tpl = open(os.path.join(tpl_path, 'content.html'), 'r').read().decode("utf8")
                    template = Template(tpl)
                    html = template.render(config=config_info, article_content=article_content, option=option_info, article_title=article_title)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf8', 'ignore'))

        elif os.path.isfile(os.path.join(ui_path, self.path[1:])):
            #if ui file request
            self.send_response(200)
            self.end_headers()
            fd = open(os.path.join(ui_path, self.path[1:]), 'rb')
            self.wfile.write(fd.read())

        elif os.path.isdir(self.xpress_request_path):
            #TODO category 
            page_size = 5
            index = Index()
            index_sort = index.get_index(self.xpress_request_path)
            #TODO 
            print len(index_sort)
            page_num = int((len(index_sort) + page_size -1) / page_size)
            if not self.xpress_url_params.has_key("page"):
                page_param = 0
            else:
                #TODO
                print self.xpress_url_params["page"]
                page_param = int(self.xpress_url_params["page"][0])
            #TODO
            print "$$$$$"
            print page_param
            print page_num
            if page_param < page_num - 1:
                page_start_point = page_param * page_size
                page_end_point = (page_param + 1) * page_size - 1
            elif page_param == page_num - 1:
                page_start_point = page_param * page_size
                page_end_point = len(index_sort) - 1
            else:
                #TODO 
                print "hacker"
                return
            if page_param == 0:
                pre_page_flag = 0
                pre_page = 0
            else:
                pre_page_flag = 1
                pre_page = page_param - 1
            if page_param == page_num -1 :
                next_page_flag = 0
                next_page = 0
            else:
                next_page_flag = 1
                next_page = page_param + 1

            print "%%%%"
            print page_start_point
            print page_end_point
            #print index_sort
            index_page = MakeIndexPage()
            tpl_var = (page_start_point, page_end_point, pre_page_flag, pre_page, next_page_flag, next_page)
            page_content = index_page.category_index_page(index_sort, self.xpress_request_path, tpl_var)
            #print page_content
            html = page_content

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf8', 'ignore'))
        else:
            self.send_error(404)

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9090
    server = BaseHTTPServer.HTTPServer((host, port), WebRequestHandler)
    server.serve_forever()
