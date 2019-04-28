# -*- coding: utf-8 -*-

import datetime
from dotenv import load_dotenv
import os
from pyquery import PyQuery as pq
import pyrebase
import re
from time import sleep

from utils import country_names, do_not_scrape, firebase_config, interval


def main():
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    db = firebase.database()

    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    email = os.environ.get('EMAIL')
    password = os.environ.get('PASSWORD')
    user = auth.sign_in_with_email_and_password(email, password)

    page_id = db.child('continuation').get(user['idToken']).val()
    if not page_id:
        db.child('continuation').set(1, user['idToken'])
        page_id = 1

    while True:
        user = auth.sign_in_with_email_and_password(email, password)

        print('#' * 50)
        print('page_id == {}'.format(page_id))
        print('#' * 50)
        ranking_html = pq(url='https://beta.atcoder.jp/ranking?page={}'.format(page_id))
        table = ranking_html.find('.table > tbody').children()

        if not table:
            print('#' * 50)
            print('Table is empty. Back to page 1.')
            print('#' * 50)
            page_id = 1
            db.child('continuation').set(page_id, user['idToken'])
            continue

        for tr in table:
            rank = int(pq(tr).children().eq(0).text())
            country = pq(tr).children().eq(1).children().eq(0).attr('href').split('=')[1]
            if country in country_names:
                formal_country_name = country_names[country]
            else:
                formal_country_name = None
            crown = pq(tr).children().eq(1).children('img').attr('src')
            crown = crown.split('/assets/icon/')[1].split('.gif')[0] if crown else None
            username = pq(tr).children().eq(1).children('.username').text()
            user_color_elem = pq(tr).children().eq(1).children('.username').children()
            user_color = user_color_elem.attr('class').replace('user-', '') if user_color_elem.attr('class') \
                else user_color_elem.attr('style').replace('color:', '').replace(';', '')
            affiliation = pq(tr).children().eq(1).children().eq(-1).children().text()
            affiliation = affiliation if affiliation else None
            birth_year = pq(tr).children().eq(2).text()
            birth_year = int(birth_year) if birth_year else None
            rating = int(pq(tr).children().eq(3).text())
            highest_rating = int(pq(tr).children().eq(4).text())
            competitions = int(pq(tr).children().eq(5).text())
            wins = int(pq(tr).children().eq(6).text())

            twitter_id = None
            userpage_html = pq('https://beta.atcoder.jp/users/{}'.format(username))
            user_info = userpage_html.find('.dl-table').find('tr')  # 環境によってtbodyがあったり無かったり?
            for el in user_info:
                if pq(el).children().eq(0).text() == 'twitter ID':
                    twitter_id = pq(el).find('a').text()[1:]
                    # 空文字やめて
                    if not twitter_id:
                        twitter_id = None
                        break
                    # @から始まるものを救済
                    if twitter_id[0] == '@':
                        twitter_id = twitter_id[1:]
                    # invalidなIDは弾く
                    if re.search(r'[^a-zA-Z0-9_]', twitter_id):
                        twitter_id = None
                        break
                    # @だった場合救済措置で空文字になる
                    if twitter_id == '':
                        twitter_id = None
                        break

            updated = str(datetime.datetime.today())

            data_by_username = {
                'rank': rank,
                'country': country,
                'formal_country_name': formal_country_name,
                'crown': crown,
                'user_color': user_color,
                'affiliation': affiliation,
                'birth_year': birth_year,
                'rating': rating,
                'highest_rating': highest_rating,
                'competitions': competitions,
                'wins': wins,
                'twitter_id': twitter_id,
                'updated': updated,
            }
            data_by_twitter_id = {
                'rank': rank,
                'country': country,
                'formal_country_name': formal_country_name,
                'crown': crown,
                'username': username,
                'user_color': user_color,
                'affiliation': affiliation,
                'birth_year': birth_year,
                'rating': rating,
                'highest_rating': highest_rating,
                'competitions': competitions,
                'wins': wins,
                'updated': updated,
            }

            db.child('by_username').child(username).set(data_by_username, user['idToken'])
            if twitter_id:
                db.child('by_twitter_id').child(twitter_id).set(data_by_twitter_id, user['idToken'])

            print(username)

            if do_not_scrape(datetime.datetime.today()):
                print('I\'m sleeping...')
                while True:
                    print('zzz...')
                    sleep(10 * 60)
                    if not do_not_scrape(datetime.datetime.today()):
                        print('Good morning! Let\'s work!')
                        user = auth.sign_in_with_email_and_password(email, password)
                        break

            sleep(interval)

        page_id += 1
        db.child('continuation').set(page_id, user['idToken'])


if __name__ == '__main__':
    main()
