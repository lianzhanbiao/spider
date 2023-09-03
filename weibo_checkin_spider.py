import requests
import os
import re
from datetime import datetime, timezone
import json
import subprocess

os.environ['NO_PROXY'] = "m.weibo.cn"

headers = {
    'authority': 'm.weibo.cn',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
}


def time_format(input_time_str):
    input_format = '%a %b %d %H:%M:%S %z %Y'
    output_format = '%Y-%m-%d %H:%M:%S'
    return datetime.strptime(input_time_str, input_format).strftime(output_format)


def clean_text(ori_text):
    return re.compile(r'<[^>]+>').sub('', ori_text)


def get_location_container_id(location_name='杭州西湖'):
    params = {
        'containerid': f'100103type=92&q={location_name}&t=',
        'page_type': 'searchall',
    }

    response = requests.get('https://m.weibo.cn/api/container/getIndex', params=params, headers=headers)
    try:
        location_list = response.json().get('data', {}).get('cards', [{}])[0].get('card_group', [])
    except Exception as e:
        print(e)
        return
 
    for location in location_list:
        if location['card_type'] == 8:
            scheme = location['scheme']
            return scheme[scheme.index('=') + 1: scheme.index('&')]
    return None


def get_location_weibo(location_name, location_container_id, page, start_time, latitude, longitude):
    params = {
        "containerid": location_container_id,
        "luicode": "10000011",
        "lcardid": "frompoi",
        "extparam": "frompoi",
        'lfid': f'100103type=92&q={location_name}&t=',
        "since_id": page,
    }
    try:
        response = requests.get('https://m.weibo.cn/api/container/getIndex', params=params, headers=headers) 
        # print(response.json().get('data', {}).get('cards', {}))
        location_weibo_list = response.json().get('data', {}).get('cards', [{}, {}])[1].get('card_group', [])
        result_dir = f'{location_name}_weibo'
        if not os.path.exists(result_dir):
            os.mkdir(result_dir)
    except Exception as e:
        print(e)
        return

    for location_weibo in location_weibo_list:
        if location_weibo['card_type'] == 9:
            try:
                weibo = location_weibo['mblog']
                if weibo['user'] is None:
                    continue
                mid = weibo['mid']
                print("mid=", mid)

                location = weibo.get('page_info', {}).get('page_title', '')
                if location is None or location == '':
                    continue
                print("location=", location)
                if datetime.strptime(weibo['created_at'], '%a %b %d %H:%M:%S %z %Y').replace(tzinfo=timezone.utc) < start_time:
                    continue
                weibo_data = {
                    'mid': weibo['mid'],
                    'publish_time': time_format(weibo['created_at']),
                    'content': clean_text(weibo['text']).replace(location, ''),
                    'location': location,
                    'iplocation': weibo.get('region_name', None),
                    'longitude': latitude,
                    'latitude': longitude,
                    'user_id': weibo['user']['id'],
                    'user_name': weibo['user']['screen_name'],
                    'user_link': f'https://weibo.com/u/{weibo["user"]["id"]}',
                    'weibo_link': f'https://weibo.com/{weibo["user"]["id"]}/{weibo["bid"]}',
                }
                print(weibo_data['publish_time'])
                # 以文件夹的形式把微博文本内容和相关图片保存在一起
                temp_result_dir = f'{result_dir}/{mid}'
                if not os.path.exists(temp_result_dir):
                    os.mkdir(temp_result_dir)
                else:
                    continue
                temp_result_file = f'{temp_result_dir}/{mid}.json'
                with open(temp_result_file, 'w', encoding='utf-8', newline='') as f:
                    json.dump(weibo_data, f, ensure_ascii=False, indent=4)
                pics = weibo.get('pics', [])

                if len(pics) > 0:
                    image_urls = ','.join([f'{pic["url"]}' for pic in pics])
                    for url in image_urls.split(','):
                        savepath = f'{temp_result_dir}/{url.split("/")[-1]}'
                        subprocess.run(['wget', url, '-O', savepath])
            except Exception as e:
                print(e)
                continue


def get_location_coordinates(address):
    # print("address=", address)
    if address is None:
        return None
    base_url = "https://restapi.amap.com/v3/geocode/geo"
    api_key = "0a8c0971cc74c84927299b7376cd2e51"  # 替换为你自己的高德API密钥

    params = {
        "key": api_key,
        "address": address
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if data["status"] == "1" and int(data["count"]) >= 1:
        location = data["geocodes"][0]["location"]
        longitude, latitude = location.split(",")
        return float(longitude), float(latitude)
    else:
        return None, None


file = "beijing.txt"
start_time = datetime.strptime('2023-08-18 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
location2latitude = {}
with open(file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines:
        input_location_name = line.strip()
        container_id = get_location_container_id(input_location_name)
        print(container_id)
        if location2latitude.get(input_location_name, None) is not None:
            longitude, latitude = location2latitude[input_location_name]
        else:
            longitude, latitude = get_location_coordinates(input_location_name)
            location2latitude[input_location_name] = (longitude, latitude)
            if longitude is None or latitude is None:
                continue
        if container_id:
            for page in range(2, 300):
                print("page=", page)
                get_location_weibo(input_location_name, container_id, page, start_time, latitude, longitude)
        else:
            print(f'没有搜索到 {input_location_name} 对应的微博签到数据')
