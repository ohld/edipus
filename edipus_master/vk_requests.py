import os
import pickle
from datetime import datetime, timedelta
import webbrowser
import json
import urllib2
import urlparse

fileDir = os.path.dirname(os.path.realpath(__file__))


APP_ID = '5712831'
# file, where auth data is saved
AUTH_FILE = '.auth_data'


def get_saved_auth_params():
    access_token = None
    user_id = None
    try:
        with open(AUTH_FILE, 'rb') as pkl_file:
            token = pickle.load(pkl_file)
            expires = pickle.load(pkl_file)
            uid = pickle.load(pkl_file)
        if datetime.now() < expires:
            access_token = token
            user_id = uid
    except IOError:
        pass
    return access_token, user_id



def save_auth_params(access_token, expires_in, user_id):
    expires = datetime.now() + timedelta(seconds=int(expires_in))
    with open(AUTH_FILE, 'wb') as output:
        pickle.dump(access_token, output)
        pickle.dump(expires, output)
        pickle.dump(user_id, output)



def get_auth_params():
    auth_url = ("https://oauth.vk.com/authorize?client_id={app_id}"
        "&scope=photos&redirect_uri=http://oauth.vk.com/blank.html"
        "&display=page&response_type=token".format(app_id=APP_ID))
    webbrowser.open_new_tab(auth_url)
    redirected_url = raw_input("Paste here url you were redirected:\n")
    aup = urlparse.parse_qs(redirected_url)
    aup['access_token'] = aup.pop(
        'https://oauth.vk.com/blank.html#access_token')
    save_auth_params(aup['access_token'][0], aup['expires_in'][0],
        aup['user_id'][0])
    return aup['access_token'][0], aup['user_id'][0]


def get_imgs_metadata(access_token, user_id):
    url = ("https://api.vk.com/method/photos.getProfile.json?"
        "uid={uid}&access_token={atoken}".format(uid=user_id, atoken=access_token))
    imgs_get_page = urllib2.urlopen(url).read()
    return json.loads(imgs_get_page)['response']


def get_me(access_token, user_id):
    url = ("https://api.vk.com/method/users.get.json?"
           "uids={uids}&access_token={atoken}".format(uids=user_id, atoken=access_token))
    info = urllib2.urlopen(url).read()
    return json.loads(info)['response']


def get_my_friends_list(access_token, user_id):
    url = ("https://api.vk.com/method/friends.get.json?"
        "uid={uid}&access_token={atoken}".format(uid=user_id, atoken=access_token))
    friends_get_page = urllib2.urlopen(url).read()
    return json.loads(friends_get_page)['response']


def get_photos_urls(photos_list):
    result = []
    new_photos_list = take_n_first(photos_list, 8)
    for photo in new_photos_list:
        #Choose photo with largest resolution
        if "src_xxbig" in photo:
            url = photo["src_xxbig"]
        elif "src_xbig" in photo:
            url = photo["src_xbig"]
        else:
            url = photo["src_big"]
        result.append(url)
    return result


def take_n_first(list_l, n):
    i = 0
    out_list = []
    while ((i < n) and (i < len(list_l))):
        out_list.append(list_l[i])
        i+=1
    return out_list