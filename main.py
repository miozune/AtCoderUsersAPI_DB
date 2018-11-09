# -*- coding: utf-8 -*-

import datetime
import os
from pyquery import PyQuery as pq
import pyrebase
from time import sleep

from utils import country_names, do_not_scrape, firebase_config, interval


def main():
    if not os.getenv('AtCoderUsersAPI_DB_continuation'):
        print('set')
        os.environ['AtCoderUsersAPI_DB_continuation'] = '1'
    page_id = int(os.environ.get('AtCoderUsersAPI_DB_continuation'))

    firebase = pyrebase.initialize_app(firebase_config)
    db = firebase.database()
    # db.child('hoge').set({'message': 'hello'})

    while True:
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
            continue

        for tr in table:
            rank = pq(tr).children().eq(0).text()
            country = pq(tr).children().eq(1).children().eq(0).attr('href').split('=')[1]
            formal_country_name = country_names[country]
            crown_attr = pq(tr).children().eq(1).children('img').attr('src')
            crown = crown_attr.split('/public/img/icon/')[1].split('.gif')[0] if crown_attr else ''
            username = pq(tr).children().eq(1).children('.username').text()
            user_color_elem = pq(tr).children().eq(1).children('.username').children()
            user_color = user_color_elem.attr('class').replace('user-', '') if user_color_elem.attr('class') \
                else user_color_elem.attr('style').replace('color:', '').replace(';', '')
            affiliation = pq(tr).children().eq(1).children().eq(-1).children().text()
            birth_year = pq(tr).children().eq(2).text()
            rating = pq(tr).children().eq(3).text()
            highest_rating = pq(tr).children().eq(4).text()
            competitions = pq(tr).children().eq(5).text()
            wins = pq(tr).children().eq(6).text()

            twitter_id = ''
            userpage_html = pq('https://beta.atcoder.jp/users/{}'.format(username))
            user_info = userpage_html.find('.dl-table').find('tr')  # 環境によってtbodyがあったり無かったり?
            for el in user_info:
                if pq(el).children().eq(0).text() == 'twitter ID':
                    twitter_id = pq(el).find('a').text()[1:]

            updated = str(datetime.datetime.today())

            data_by_username = {
                username: {
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
            }
            data_by_twitter_id = {
                twitter_id: {
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
            }

            # print(data_by_username, data_by_twitter_id)
            db.child('by_username').set(data_by_username)
            db.child('by_twitter_id').set(data_by_twitter_id)

            print(username)

            if do_not_scrape(datetime.datetime.today()):
                print('I\'m sleeping...')
                while True:
                    print('zzz...')
                    sleep(10 * 60)
                    if not do_not_scrape(datetime.datetime.today()):
                        print('Good morning! Let\'s work!')
                        break

            sleep(interval)

        page_id += 1


if __name__ == '__main__':
    main()
