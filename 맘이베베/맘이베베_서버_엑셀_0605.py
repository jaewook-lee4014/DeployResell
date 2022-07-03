# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from selenium import webdriver
from bs4 import BeautifulSoup as bs
import pandas as pd
# import csv
import re
import time
from datetime import datetime
# import tkinter.ttk as ttk
# import tkinter as tk
import time
import sys, os
# import gspread
from selenium.webdriver.chrome.options import Options
# from oauth2client.service_account import ServiceAccountCredentials
# import requests
import time
# import chromedriver_autoinstaller

'''은호 코드, 댓글에서 링크 추출하는 코드'''


regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))" 

def get_link():
    # driver.get('https://cafe.naver.com/skybluezw4rh/'+str(page))
    # driver.implicitly_wait(3)
    # driver.switch_to.frame("cafe_main")
    try:
        print('try했음')
        comment_box = driver.find_elements_by_class_name('comment_box')
        link_text = "NO_LINK"
        
        for comment in comment_box:
            name = comment.find_element_by_class_name('comment_nickname').text
            comment_text = comment.find_element_by_class_name('text_comment')
    
            # 작성자가 쓴 덧글은 닉네임 옆에 (작성자) 아이콘이 붙음 해당 파트로 작성자 여부 채크
            try:
                writer_badge = comment.find_element_by_class_name('comment_badge_writer')
                is_writer = True
            except:
                is_writer = False
                
            # 작성자가 쓴 덧글만 가져 옴
            if ( is_writer ):
                # 덧글 텍스트 칸 안에 a 태그가 존재 할 경우만 가져 옴
                try:
                    link_text = comment_text.find_element_by_tag_name('a').get_attribute('href')
                except:
                    link_text = "NO_LINK"
                    # a 태그가 없는 경우 해당 덧글의 텍스트에 정규식을 돌려서 판단함
                    url = re.findall(regex, comment_text.text)
                    if ( len(url) > 0 ):
                        link_text = url[0][0]
    
        # 덧글에서 링크가 없는 경우 본문에서 링크를 찾음
        # 본문에서 먼저 링크를 찾지 않는 이유: 본문에서 문장을 추출하는 과정 (content_box.text)가 시간 소요가 많이 됌
        # if ( link_text == "NO_LINK" ):
            
        #     content_box = driver.find_element_by_class_name('se-main-container')
        #     content_box_text = content_box.text
    
        #     print("=================\n")
        #     print(content_box_text)
        #     print("=================\n")
    
        #     # 본문 전체의 문장 중에서 정규식을 돌려 판단
        #     # 문제점) 본문에 링크가 여러개 적혀 있는 경우 어떤게 맞는 것인지 판단 할 방법이 없음
        #     # 현재로는 제일 처음 등장한 링크를 가져오게 되어 있음
        #     url = re.findall(regex, content_box_text)
    
        #     if ( len(url) > 0 ):
        #         link_text = url[0][0]
                
        #     print("regex: ", link_text, "\n")
    except:
        print('실패했음')
        link_text ="NO_LINK"
    print(link_text)
    return str(link_text)

def hotdeal():
    global searh_num, cell_num, append_df, data, link_list
    append_df = pd.DataFrame([])
    
    searh_num = int(searh_num)
    # global worksheet
    # matching_number_list=[]
    newurl_list=[]
    article_title_list=[]
    product_title_list=[]
    link_list=[]
    final_matching_list=[]
    print('맘이베베 서칭 시작')
    price_list=[]
    # 기본경로 설정
    base_url = 'https://cafe.naver.com/맘이베베/ArticleList.nhn?search.clubid=29434212'
    for i in range(100):
        
        driver.get(base_url + '&search.menuid=2&search.page='+str(i+1))
        driver.implicitly_wait(10)
        driver.switch_to.frame('cafe_main')
        #html로 읽겠다 선언
        soup = bs(driver.page_source ,'html.parser')
        soup = soup.find_all(class_ = 'article-board m-tcol-c')[1]
        stop = 0
        # 네이버 카페 구조 확인후 게시글 내용만 가저오기
        datas = soup.find_all(class_ = 'td_article')
        # print('1')
        for index,data in enumerate(datas):
            # print(index)
            matching_number = data.find(class_ = 'inner_number')
            matching_number = int(matching_number.get_text().strip())
            # print('2')
            if i == 0:
                # print('3')
                if index == 0:
                    reset_num = int(matching_number)
                    last_num = int(reset_num) +1
                    print('현재의 최신 넘버',reset_num)
            if matching_number == searh_num:
                # print('4')
                stop = 1
                break
            '''하한:직전 크롤링에서의 마지막 작업 ID, 상한:이번 크롤링에서의 최신 작업 ID'''
            if matching_number > searh_num:
                '''다음페이지에서의 리셋문제 해결'''
                
                if (matching_number>=last_num):
                    print(matching_number,last_num,'매칭넘버가 더 크거나 같다, 이것만 스킵')
                    continue
                else:
                    last_num = matching_number
                
                
                    final_matching_list.append(matching_number) 
            else:
                stop = 1
                print('하한보다 작기때문에 스탑')
                break
            # matching_number_list.append(matching_number)
            article_title = data.find(class_ = 'article')
            article_title = article_title.get_text().strip()
            article_title_list.append(article_title)
            # print(matching_number)
            # mall = article_title[0 : article_title.find(')')]
            product_title = article_title[article_title.find(')')+1:]
            # article_title = re.sub("쿠팡|위메프|옥x|핫딜|롯데온|무배|지마켓|옥션|소개딜|티몬|자체쿠폰|삼카|\xa0","",article_title)
            product_title = product_title.replace(",", "")
            product_title = product_title.replace(".", "")
            product_title = product_title.replace('\n',"")
            product_title_list.append(product_title)
            # a_title.append(article_title)
            ## 가격 추출 모듈
            re1 = re.compile('[\S\s]*([0-9]{6}원)[\S\s]*')
            re12 = re.compile('[\S\s]*([0-9]{5}원)[\S\s]*')
            re13 = re.compile('[\S\s]*([0-9]{4}원)[\S\s]*')
            re2 = re.compile('[\S\s]*([0-9]{6})[\S\s]*')
            re22 = re.compile('[\S\s]*([0-9]{5})[\S\s]*')
            re23 = re.compile('[\S\s]*([0-9]{4})[\S\s]*')
            priceRe = re1.match(product_title)
            priceRe12 = re12.match(product_title)
            priceRe13 = re13.match(product_title)
            priceRe2 = re2.match(product_title)
            priceRe22 = re22.match(product_title)
            priceRe23 = re23.match(product_title)
            if priceRe:
                price = priceRe.groups()[0]
                price = price.replace("원", "")
                print('1', price)
            elif priceRe12:
                price = priceRe12.groups()[0]
                price = price.replace("원", "")
                print('2', price)

            elif priceRe13:
                price = priceRe13.groups()[0]
                price = price.replace("원", "")
                print('2', price)
            elif priceRe2:
                price = priceRe2.groups()[0]
                price = price.replace("원", "")
                print('2', price)
            elif priceRe22:
                price = priceRe22.groups()[0]
                price = price.replace("원", "")
                print('2', price)
            elif priceRe23:
                price = priceRe23.groups()[0]
                price = price.replace("원", "")
                print('2', price)
            else:
                price = 999999
            price_list.append(price)

            newurl=('https://cafe.naver.com/ArticleRead.nhn?clubid=29434212&page=1&menuid=2&boardtype=L&articleid=' + str(matching_number) + '&referrerAllArticles=false')
            newurl_list.append(newurl)
            driver.get(newurl)
            driver.implicitly_wait(5)
            try:
                driver.switch_to.frame(driver.find_element_by_xpath('//iframe[@name="cafe_main"]'))
            except:
                try:
                    driver.switch_to.frame("cafe_main")
                except:
                    pass
            #링크가져오기#

            try:
                link = driver.find_element_by_class_name('se-link').text
            except:
                print(matching_number,'댓글에서 링크 탐색 작동중')
                link = get_link()
                if link == 'NO_LINK':
                    link = '링크 없음'
                
            link_list.append(link)
        if stop == 1:
            # worksheet_reset.insert_row(['%s월 %s일 %s시 %s분' % (now.month, now.day, now.hour, now.minute),'맘이베베', reset_num, int(cell_num) + len(link_list)], 1)
            # searh_num.loc[0] = reset_num
            
            partial_df = excel_data['검색정보']['search key']
            partial_df[0] = reset_num
            partial_df.to_excel('C:\\Users\\User\\Desktop\\jaewook folder\\창업 코드\\맘베\\맘이베베.xlsx', sheet_name="검색정보", index=False)
            print('최신번호 저장완료 ', str(reset_num))
            # new_cell_num = int(cell_num) + len(link_list)
            break
    # final_matching_list = []
    # for p in matching_number:
    #     if matching_number > searh_num:
    #         final_matching_list.append(p)
    # final_matching_list 
    # 가져온 링크에 접속하여 정보 추출
    print(link_list)
    print('링크의 갯수는: ',len(link_list), '개')
    max_num = 0
    if len(link_list)==0:
        return 0
    # else:
    for link_num, newurl, article_title, product_title, link, price in zip(final_matching_list,newurl_list,article_title_list,product_title_list,link_list,price_list):
        max_num += 1
        # if max_num % 20 == 0:
        #     time.sleep(60)
        # try:
        # worksheet.append_row(['%s월 %s일 %s시 %s분' % (now.month, now.day, now.hour, now.minute),'맘이베베', link_num, newurl,article_title, product_title, link, price])
        for_df = pd.DataFrame(['%s월 %s일 %s시 %s분' % (now.month, now.day, now.hour, now.minute),'맘이베베', link_num, newurl, article_title, product_title, link, price])
        for_df = for_df.T
        append_df = pd.concat([append_df, for_df],axis = 0)
        print('데이터 프레임 붙이는 중!!!')
        # except:
        #     try:
        #         print(max_num,'번 시도 후, 최대 횟수 초과, 3분 슬립')
        #         time.sleep(180)
        #         worksheet.insert_row(['%s월 %s일 %s시 %s분' % (now.month, now.day, now.hour, now.minute),'맘이베베', link_num, newurl,article_title, product_title, link, price], 2)
        #     except:
        #         print('다시 3분 추가 슬립')
        #         time.sleep(180)
        #         worksheet.insert_row(['%s월 %s일 %s시 %s분' % (now.month, now.day, now.hour, now.minute),'맘이베베', link_num, newurl,article_title, product_title, link, price], 2)
    append_df.columns = ['시간', '핫딜몰', '게시글 id', '핫딜몰 링크', '핫딜몰 제품명', '보정 제품명', '쇼핑몰 주소', '핫딜몰 가격']
    return len(link_list)


def shopmall(stop_num):
    global cell_num, append_df,total_data
    shop_df = pd.DataFrame([])
    print('링크내 제목 탐색 시작')
    # print(cell_num,'부터 ',stop_num,'개를 탐색')
    # print()
    if stop_num == 0:   # 할게 없으면 패스
        pass
    else:
        # cell_link_list = worksheet.range('G' + str(cell_num) + ':G' + str(int(cell_num)+stop_num-1))
        article_title_list=[]
        cell_link_list = append_df['쇼핑몰 주소']
        for i in cell_link_list:
            mall_link = i
            print(mall_link)
            try:
                driver.get(mall_link)
            except:
                mall_title = '링크 접속불가'
                article_title_list.append(mall_title)
                continue
            time.sleep(10)
            # driver.implicitly_wait(10)
            try:
                if mall_link.find('auction') > 0:
                    try:
                        mall_title = driver.find_element_by_xpath('/html/body/div[9]/div[2]/div[2]/form/h1').text
                    except:
                        mall_title = driver.find_element_by_xpath('//*[@id="frmMain"]/h1]').text
        
                elif mall_link.find('lotteon') > 0:
                    try:
                        mall_title = driver.find_element_by_xpath(
                            '/html/body/div[1]/main/div/div[1]/div[2]/div[1]/div[2]/h1').text
                    except:
                        try:
                            mall_title = driver.find_element_by_xpath(
                                '/html/body/div[1]/main/div/div[1]/div[2]/div[1]/div[3]/h1').text
                        except:
                            mall_title = driver.find_element_by_xpath(
                                '//*[@id="stickyTopParent"]/div[2]/div[2]/div[3]/h1]').text
        
                elif 'wemakeprice' in mall_link:
                    try:
                        mall_title = driver.find_element_by_xpath(
                            '/html/body/div[2]/div[2]/div/div[1]/div[3]/div[1]/div[2]/div[1]/h3').text
                    except:
                        mall_title = driver.find_element_by_xpath('//*[@id="_infoDescription"]/div[1]/h3').text
        
                elif mall_link.find('gmarket') > 0:
                    try:
                        mall_title = driver.find_element_by_xpath(
                            '/html/body/div[4]/div[2]/div[2]/div[1]/div/div[1]/h1').text
                    except:
                        try:
                            mall_title = driver.find_element_by_xpath(
                                '/html/body/div[1]/div[4]/div[2]/div[1]/div[2]/div[2]/div[2]/div[1]/h3').text
                        except:
                            try:
                                mall_title = driver.find_element_by_xpath(
                                    '//*[@id="goodsDetailTab"]/div[2]/div/div[3]/h3').text
                            except:
                                mall_title = driver.find_element_by_xpath(
                                    '/html/body/div[1]/div[4]/div[2]/div[1]/div[2]/div/div[2]/div[1]/h3').text
        
                elif mall_link.find('gs') > 0:
                    try:
                        mall_title = driver.find_element_by_xpath('/html/body/div[4]/div[1]/section[1]/h1').text
                    except:
                        mall_title = driver.find_element_by_xpath('//*[@id="mainInfo"]/div[1]/section[1]/h1').text
        
                elif mall_link.find('tmon') > 0:
                    try:
                        mall_title = driver.find_element_by_xpath(
                            '/html/body/div[3]/div[2]/div/div/section[1]/section[1]/section[1]/div[3]/article[1]/div[2]/h2').text
                    except:
                        try:
                            mall_title = driver.find_element_by_xpath(
                                '/html/body/div[2]/section[1]/section[1]/div[4]/article[1]/div[2]/h2').text
                        except:
                            try:
                                mall_title = driver.find_element_by_xpath(
                                    '/html/body/div[2]/div/div/div/section[1]/section[1]/section[1]/div[3]/article[1]/div[2]/h2').text
                            except:
                                mall_title = driver.find_element_by_xpath(
                                    '/html/body/div[2]/div/div/div[1]/div[3]/div[1]/p[1]').text
                elif mall_link.find('11st') > 0:
                    try:
                        mall_title = driver.find_element_by_xpath(
                            '/html/body/div[2]/div[3]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[3]/h1').text
                    except:
                        try:
                            mall_title = driver.find_element_by_xpath(
                                '/html/body/div[2]/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[2]/h1').text
                        except:
                            mall_title = driver.find_element_by_xpath(
                                '//*[@id="layBodyWrap"]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[2]/h1').text
        
                elif mall_link.find('interpark') > 0:
                    mall_title = driver.find_element_by_xpath(
                        '/html/body/div[1]/div[5]/div/div[2]/div/div/div[2]/h2/span[2]').text
        
                elif mall_link.find('coupang') > 0:
                    mall_title = driver.find_element_by_xpath(
                        '/html/body/div[1]/section/div[1]/div/div[3]/div[3]/h2').text
        
                elif mall_link.find('naver') > 0:
                    try:
                        mall_title = driver.find_element_by_xpath(
                            '/html/body/div/div/div[2]/div[2]/div[2]/div[2]/fieldset/div[2]/div[1]/h3').text
                    except:
                        try:
                            mall_title = driver.find_element_by_xpath(
                                '/html/body/div/div/div[3]/div/div[1]/h2').text
                        except:
                            try:
                                mall_title = driver.find_element_by_xpath(
                                    '/html/body/div/div/div[3]/div[2]/div[2]/div/div[2]/div[2]/fieldset/div[1]/div[1]/h3').text
                            except:
                                mall_title = driver.find_element_by_xpath(
                                    '/html/body/div/div/div[2]/div/div[2]/div/div[2]/div[2]/fieldset/div[1]/div[2]/div/strong/span[2]').text
        
                elif mall_link.find('brand.naver') > 0:
                    mall_title = driver.find_element_by_xpath(
                        '/html/body/div/div/div[2]/div/div[2]/div/div[2]/div[2]/fieldset/div[1]/div[1]/h3').text
        
                elif mall_link.find('kakao') > 0:
                    mall_title = driver.find_element_by_xpath(
                        '/html/body/fu-app-root/fu-talkstore-wrapper/div/div/fu-pw-product-detail/div/div[1]/strong').text
        
                elif mall_link.find('yes24') > 0:
                    mall_title = driver.find_element_by_xpath(
                        '/html/body/div/div[4]/div[2]/div[1]/div/h2').text
        
                elif mall_link.find('nsmall') > 0:
                    mall_title = driver.find_element_by_xpath(
                        '/html/body/div/div[1]/div/div/section[1]/div[2]/div[1]/h3').text
        
                elif mall_link.find('ssg') > 0:
                    try:
                        mall_title = driver.find_element_by_xpath(
                            '/html/body/div[4]/div[6]/div[2]/div[1]/div[2]/div[2]/h2').text
                    except:
                        mall_title = driver.find_element_by_xpath(
                            '/html/body/div[4]/div[6]/div/div[2]/div[1]/div[2]/div[2]/h2').text
                else:
                    mall_title = "모르는 사이트"
            except:
                mall_title = "설정된 사이트, 설정안된 태그"
            article_title_list.append(mall_title)
            print('쇼핑몰에서 찾은 제품명: ',mall_title)
        print('전체 제품명 리스트는: ',article_title_list)
        # cell_title_list = worksheet.range('I' + str(cell_num) + ':I' + str(int(cell_num) + stop_num-1))
        
        # for index, val in enumerate(article_title_list):
        #     cell_title_list[index].value = val
        # worksheet.update_cells(cell_title_list)
        append_df['쇼핑몰 제목'] = article_title_list
        
def navermall(stop_num):
    global cell_num, append_df,total_data
    print('네이버에서 최저가 탐색 시작', stop_num, '개')
    # naver_url_list = []
    # naver_link_list,catalog_id_list,naver_pro_name_list,priceText_list,delivery_list,naver_review_num_list = []
    naver_link_list = []
    catalog_id_list = []
    naver_pro_name_list = []
    priceText_list = []
    delivery_list = []
    naver_review_num_list = []
    # for i in range(300):
    #     cell_data = worksheet.acell( 'I' + str(i+1) ).value
    #     print(cell_data)
    #     if cell_data != None:
    #         stop_num = i
    #         print(stop_num)
    #         break
    if stop_num == 0:
        pass
    else:
        cell_title_list = append_df['쇼핑몰 제목']
        article_title_list=[]
        raw_title_list = append_df['보정 제품명']
        # print(cell_title_list)
        '''index_cell의 숫자 확인해보기.'''
        for raw_title, mall_title in zip(raw_title_list,cell_title_list):
            # mall_title =mall_title.value
            url = "https://shopping.naver.com/"
            time.sleep(0.5)
            if mall_title == "설정된 사이트, 설정안된 태그" : 
                mall_title = raw_title
                
            elif mall_title == "모르는 사이트":
                mall_title = raw_title
                
            elif mall_title == "링크 접속불가":
                mall_title = raw_title
                
            if mall_title is None:
                continue
            driver.get(url)
            element = driver.find_element_by_xpath('//*[@id="_verticalGnbModule"]/div/div[2]/div/div[2]/div/div[2]/form/fieldset/div/input')
            # 1. 검색창에 단어 입력하기
            print('네이버에서 탐색하는 제품명: ',mall_title)
            element.send_keys(mall_title)

            driver.find_element_by_xpath('//*[@id="_verticalGnbModule"]/div/div[2]/div/div[2]/div/div[2]/form/fieldset/div/button[2]').click()
            time.sleep(2)


            # 3. 가격비교 창 들어가기
            try:
                diff = driver.find_element_by_xpath(
                    '//*[@id="__next"]/div/div[2]/div/div[3]/div[1]/div[1]/ul/li[2]/a')
                diff.click()
            except:
                # worksheet.update_acell('J'+str(int(cell_num) + index_cell), '네이버 가격비교 없음')
                # naver_url_list.append('네이버 가격비교 없음')
                naver_link_list.append('네이버 가격비교 없음')
                catalog_id_list.append('네이버 가격비교 없음')
                naver_pro_name_list.append('네이버 가격비교 없음')
                priceText_list.append('네이버 가격비교 없음')
                delivery_list.append('네이버 가격비교 없음')
                naver_review_num_list.append('네이버 가격비교 없음')
                # 특정 셀 쓰기
                continue
            time.sleep(1)
            try:
                naver_review_num = driver.find_element_by_xpath(
                    '/html/body/div/div/div[2]/div/div[3]/div[1]/ul/div/div[1]/li/div/div[2]/div[5]/a/em').text
            except:
                # naver_link_list.append('리뷰 없음')
                # catalog_id_list.append('리뷰 없음')
                # naver_pro_name_list.append('리뷰 없음')
                # priceText_list.append('리뷰 없음')
                # delivery_list.append('리뷰 없음')
                naver_review_num = '리뷰 없음'

            try:
                item = driver.find_element_by_xpath(
                    '//*[@id="__next"]/div/div[2]/div/div[3]/div[1]/ul/div/div[1]/li/div/div[2]/div[1]/a')

            # 가격 비교 상품 없을시
            except:
                # worksheet.update_acell('J'+str(int(cell_num) + index_cell), '네이버 가격비교 없음')
                naver_link_list.append('네이버 가격비교 없음')
                catalog_id_list.append('네이버 가격비교 없음')
                naver_pro_name_list.append('네이버 가격비교 없음')
                priceText_list.append('네이버 가격비교 없음')
                delivery_list.append('네이버 가격비교 없음')
                naver_review_num_list.append('네이버 가격비교 없음')
                continue
            entry = item.get_attribute("data-nclick")
            entry = entry.split(",")
            catalog_id = entry[1].replace("i:", "")
            naver_link = 'https://search.shopping.naver.com/catalog/' + catalog_id
            driver.get(naver_link)
            time.sleep(1)
            # 배송료 포함버튼
            try:
                driver.find_element_by_xpath(
                    '//*[@id="__next"]/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[2]/div/div/div/div[2]/span[1]/a').click()
    
                time.sleep(1)
                naver_pro_name = driver.find_element_by_xpath(
                    '/html/body/div/div/div[2]/div[2]/div[1]/h2').text
                priceText = driver.find_element_by_xpath(
                    '//*[@id="__next"]/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[2]/table/tbody/tr[1]/td[2]/a/em').text
                priceText = priceText.replace(",", "")
                delivery = driver.find_element_by_xpath(
                    '/html/body/div/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[2]/table/tbody/tr[1]/td[3]').text
            # all_list=[naver_link,catalog_id,naver_pro_name,priceText,delivery,naver_review_num]
            except:
                naver_link_list.append('에러 발생')
                catalog_id_list.append('에러 발생')
                naver_pro_name_list.append('에러 발생')
                priceText_list.append('에러 발생')
                delivery_list.append('에러 발생')
                naver_review_num_list.append('에러 발생')
                continue
            naver_link_list.append(naver_link)
            catalog_id_list.append(catalog_id)
            naver_pro_name_list.append(naver_pro_name)
            priceText_list.append(priceText)
            delivery_list.append(delivery)
            naver_review_num_list.append(naver_review_num)
            
    append_df['네이버 주소'] = naver_link_list
    append_df['네이버 번호'] = catalog_id_list
    append_df['네이버 제목'] = naver_pro_name_list
    append_df['네이버 가격'] = priceText_list
    append_df['네이버 배송료'] = delivery_list
    append_df['네이버 리뷰 개수'] = naver_review_num_list
    total_data = pd.concat([total_data['맘이베베 내용'],append_df],axis=0)
    total_data.to_excel('C:\\Users\\User\\Desktop\\jaewook folder\\창업 코드\\맘베\\맘이베베_기본.xlsx', sheet_name="맘이베베 내용", index=False)
            # cell_list_all = worksheet.range('J'+str(int(cell_num) + index_cell)+':O' + str(int(cell_num) + index_cell))
            # for index, val in enumerate(all_list):
            #     cell_list_all[index].value = val
            # worksheet.update_cells(cell_list_all)



# scope = [
#     'https://spreadsheets.google.com/feeds',
#     'https://www.googleapis.com/auth/drive',
# ]
# time.sllep(5)C:\Users\User\Desktop\파이썬 코드_21_12_27\쇼핑몰_자동화\woogi\GUI도전
# C:\Users\User\Desktop\파이썬 코드_21_12_27\쇼핑몰_자동화\woogi
# C:\Users\tako\Desktop\코드_0208\GUI도전
# C:\Users\woshi\Desktop\쇼핑몰_자동화-20220122T070904Z-001\쇼핑몰_자동화\woogi\GUI도전
# json_file_name = 'C:\\Users\\tako\\Desktop\\코드_0208\\GUI도전\\graphic-centaur-322708-b1cb3ca5388c.json'
# credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
# gc = gspread.authorize(credentials)
# spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1MU6FcSwHgk2MnWNFgzpO6d9HLyApl1X4OiCrm0Biw_A/edit#gid=0'

# 스프레스시트 문서 가져오기
# doc = gc.open_by_url(spreadsheet_url)
# 시트 선택하기
# time.sleep(5)
# worksheet = doc.worksheet('핫딜몰_기본정보')

# worksheet_reset = doc.worksheet('최신_게시글정보')



while True:
    # try:
    excel_data = pd.read_excel('C:\\Users\\User\\Desktop\\jaewook folder\\창업 코드\\맘베\\맘이베베.xlsx', sheet_name=None)
    searh_num = str(excel_data['검색정보']['search key'].loc[0])
    '''임시설정'''
    # searh_num = str(7641856)
    # searh_num = worksheet_reset.acell('c1').value
    print('이전의 탐색번호:',searh_num)
     # total_data= excel_data['맘이베베 내용']
    total_data = pd.read_excel('C:\\Users\\User\\Desktop\\jaewook folder\\창업 코드\\맘베\\맘이베베_기본.xlsx', sheet_name=None)
    # cell_num = worksheet_reset.acell('d1').value
    # print('이전의 셀 번호', cell_num)
    # if searh_num is None:
    #     searh_num = worksheet_reset.acell('c2').value
    #     print('두번째 이전의 탐색번호:',searh_num)
    # searh_num = worksheet.acell('B4').value
    # searh_num = '6296062'
    now = datetime.now()
    '''자동로그인 코드-고운'''
    # chromedriver_autoinstaller.install()
    # chrome_options = Options() 
    # chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
    # driver = webdriver.Chrome(options=chrome_options)
    '''위에까지'''
    
    option = Options()
    option.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 1
    })
    if getattr(sys, 'frozen', False):
        chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
        driver = webdriver.Chrome(chromedriver_path)
    else:
        driver = webdriver.Chrome(options=option,executable_path='C:\\Users\\User\\Desktop\\jaewook folder\\창업 코드\\chromedriver')
        
    '''서칭개수 공유'''
    new_search_num = hotdeal()
    
    shopmall(new_search_num)
    
    navermall(new_search_num)
    '서칭끝 10분 슬립'
    time.sleep(600)
    # except:
    #     print('오류 발생, 10분 슬립')
    #     time.sleep(100)