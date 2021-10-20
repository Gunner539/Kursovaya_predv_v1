import requests
from pprint import pprint
import os
import urllib
import datetime
import time
from tqdm import tqdm
import json

def file_exist(file_name):
    current_path = os.getcwd()
    if file_name != '':
        file_address = f'{current_path}\\{file_name}'
    else:
        return False

    if not os.path.isfile(file_address):
        return False
    else:
        return True


def save_to_hdd(list_for_write_in_file, site_name):
    backup_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    dir_backup_name = f'backup_files'
    if not os.path.exists(dir_backup_name):
        os.mkdir(dir_backup_name)
    dir_backup_for_site = f'{dir_backup_name}/{site_name}'
    if not os.path.exists(dir_backup_for_site):
        os.mkdir(dir_backup_for_site)

    with open(f'{dir_backup_for_site}/{backup_date}.json', 'w') as backup_file:
        json.dump(list_for_write_in_file, backup_file, indent=4)

class YaDisk:
    def __init__(self, token: str, backup_count=2):
        self.token = token
        self.backup_count = backup_count

    def get_headers(self):
        return {'Content-Type': 'application/json', 'Authorization': 'OAuth {}'.format(self.token)}

    def _file_exist(self, likes, dir, extension):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': f'{dir}/{likes}.{extension}', 'fields': 'name'}
        response = requests.get(url=upload_url, headers=headers, params=params)
        if response.status_code == 200:
            return True
        else:
            return False

    def delete_folder(self, path):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': path, 'force_async': False, 'permanently': True}
        requests.delete(url=url, headers=headers, params=params)

    def delete_old_backups(self, site_name):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': f'backup/{site_name}', 'fields': 'items', 'sort': 'created'}
        response = requests.get(url=url, headers=headers, params=params)
        if response.status_code == 200:
            backups = response.json()['_embedded']['items']
            for ind in list(range(0, len(backups) - self.backup_count)):
                self.delete_folder(backups[ind]['path'])


    def catalog_exist(self, path='backup'):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': path}
        if requests.get(url=url, headers=headers, params=params).status_code == 200:
            return True
        else:
            return False

    def create_backup_catalog(self, catalog_name='backup'):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': catalog_name}
        resp = requests.put(url=url, headers=headers, params=params)
        if not resp.status_code == 201:
            return 'error'

    def upload(self, biggest_pic_data, likes, download_date, dir):

        file_path = biggest_pic_data['url']
        file_extension = biggest_pic_data['extension']
        if self._file_exist(likes, dir, file_extension):
            file_name = f'{likes}_{download_date}'
        else:
            file_name = likes
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        params = {'path': f'{dir}/{file_name}.{file_extension}', 'url': file_path}
        response = requests.post(url=url, headers=headers, params=params)
        response.raise_for_status()
        return f'{file_name}.{file_extension}'


class VK():
    def __init__(self):
        self.token = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'
        self.url_api = 'https://api.vk.com/method/'
        self.v = '5.131'
        self.id_screen_name = ''
        self.id = 0


    def get_id_by_screenname(self):
        url = f'{self.url_api}users.get'
        params = {'user_ids': self.id_screen_name, 'v': self.v, 'access_token': self.token}
        response = requests.get(url=url, params=params)
        if response.status_code == 200:
            self.id = response.json()['response'][0]['id']
            return True
        else:
            response.raise_for_status()
            return False


    def get_photos(self, album_id='profile'):

        photos_list = []
        if not album_id == 'profile':
            album_ids = self.get_albums()
            if album_ids == None:
                return
            album_ids.append({'id': 'profile', 'album_name': 'profile'})
            album_ids.append({'id': 'saved', 'album_name': 'saved'})
            album_ids.append({'id': 'wall', 'album_name': 'wall'})
        else:
            album_ids = [{'id': 'profile', 'album_name': 'profile'}]

        url = f'{self.url_api}photos.get'
        for element in album_ids:
            params = {'owner_id': self.id, 'v': self.v, 'access_token': self.token, 'album_id': element['id'], 'extended': True}
            response = requests.get(url=url, params=params)
            if response.status_code == 200:
                if 'error' not in response.json():
                    for photo in response.json()['response']['items']:
                        photos_list.append({'album_id': element['id'], 'album_name': element['album_name'],
                                            'photo_id': photo['id'], 'likes': photo['likes'],
                                            'sizes': photo['sizes'], 'date': photo['date']})
                else:
                    print(f'Ошибка! Альбом "{element["album_name"]}": {response.json()["error"]["error_msg"]}')
                    return
        return photos_list

    def get_albums(self):
        url = f'{self.url_api}photos.getAlbums'
        params = {'owner_id': self.id, 'v': self.v, 'access_token': self.token, 'photo_sizes': 1}

        response = requests.get(url, params=params)
        if response.status_code == 200:
            albums_list = []
            if 'error' not in response.json():
                for album_item in response.json()['response']['items']:
                    if album_item['size'] > 0:
                        albums_list.append({'id': album_item['id'], 'album_name': album_item['title']})
                return albums_list
            else:
                print('Ошибка доступа к альбомам')
                return
        else:
            response.raise_for_status()

    def get_biggest_pic(self, pics):
        the_biggest_pic = {'s': pics[0]['height'] * pics[0]['width'], 'url': pics[0]['url'], 'type': pics[0]['type'], 'extension': pics[0]['url'].split('?')[0].split('.')[-1]}
        i = 1
        while i < len(pics):
            current_s = pics[i]['height'] * pics[i]['width']
            if current_s == 0:
                return {'url': pics[-1]['url'], 'type': pics[-1]['type'], 'extension': pics[-1]['url'].split('?')[0].split('.')[-1]}
            elif current_s > the_biggest_pic['s']:
                the_biggest_pic['s'] = current_s
                the_biggest_pic['url'] = pics[i]['url']
                the_biggest_pic['type'] = pics[i]['type']
                the_biggest_pic['extension'] = pics[i]['url'].split('?')[0].split('.')[-1]
            i += 1
        return the_biggest_pic


    def save_on_YaDisk(self, photos_list, ya_token, count=5):

        ya_disk = YaDisk(ya_token)
        photos_in_list = len(photos_list)
        backup_catalog_name = 'backup'
        backup_for_site_dir_name = f'backup/vk_com'
        backup_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_date_folder = f'{backup_for_site_dir_name}/{backup_date}'
        if not ya_disk.catalog_exist(backup_catalog_name):
            ya_disk.create_backup_catalog(backup_catalog_name)
        if not ya_disk.catalog_exist(backup_for_site_dir_name):
            ya_disk.create_backup_catalog(backup_for_site_dir_name)
        if not ya_disk.catalog_exist(backup_date_folder):
            ya_disk.create_backup_catalog(backup_date_folder)
        list_for_write_in_file = []
        index = 1

        created_and_existing_folders = []

        for item_index in tqdm(list(range(0, min(photos_in_list, count)))):
            album_dir_on_ya_disk = f'{backup_date_folder}/{photos_list[item_index]["album_name"]}'
            if photos_list[item_index]['album_name'] not in created_and_existing_folders:
                if not ya_disk.catalog_exist(album_dir_on_ya_disk):
                    ya_disk.create_backup_catalog(album_dir_on_ya_disk)

            item = photos_list[item_index]
            if index > count:
                break
            time.sleep(1)
            biggest_pic = self.get_biggest_pic(item['sizes'])
            download_date = datetime.datetime.utcfromtimestamp(item['date']).strftime('%Y_%m_%d_%H_%M_%S')
            likes_count = item['likes']['count']
            file_name_in_backup = ya_disk.upload(biggest_pic, likes_count, download_date, album_dir_on_ya_disk)
            index += 1
            list_for_write_in_file.append({'file_name': file_name_in_backup, 'size': biggest_pic['type']})

        save_to_hdd(list_for_write_in_file, 'vk_com')
        print(f'Backup path: https://disk.yandex.ru/client/disk/{backup_date_folder}')

def make_vk_backup(album='profile'):

    ya_token = input('Введите Ваш Яндекс Токен : ')
    id_screenname = input('Введите Ваш вк id или screen_name : ')
    api_vk = VK()
    api_vk.id_screen_name = id_screenname

    if api_vk.get_id_by_screenname() == False:
        print('Пользователь не найден')
        return

    photos_list = api_vk.get_photos(album)
    if photos_list == None:
        return
    api_vk.save_on_YaDisk(photos_list, ya_token)
    YaDisk(ya_token).delete_old_backups('vk_com')

    print('ready')

if __name__ == '__main__':

    print('------------------------------------------------------------------------------')
    print('|КЛАВИША | ДЕЙСТВИЕ                    |       ВХОДНЫЕ ПАРАМЕТРЫ              |')
    print('------------------------------------------------------------------------------')

    print('|  (1)   | Бэкап фото из профиля ВК    |  Токен яндекса, имя/id VK            |')
    print('|  (2)   | Бэкап всех фото ВК          |  Токен яндекса, имя/id VK            |')
    print('------------------------------------------------------------------------------')

    action = int(input('Выберите действие: '))
    if action == 1:
        make_vk_backup()
    if action == 2:
        make_vk_backup('all')

