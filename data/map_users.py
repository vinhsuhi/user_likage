from utils import MongoDB, JsonObject, Pickle
from string_similarity import dice_coefficient3
from pprint import pprint
import os

foursquare_data_path = 'foursquare' + os.sep + 'data.json'


def get_twitter_info():
  # if os.path.exists('twitter' + os.sep + 'twitter_user_info.pkl'):
  #   return Pickle.load_obj('twitter' + os.sep + 'twitter_user_info'), Pickle.load_obj('twitter' + os.sep + 'twitter_user_checkins')

  users_twitter = MongoDB.get_collection(database_name='twitter', collection_name='users')
  checkins_twitter = MongoDB.get_collection(database_name='twitter', collection_name='checkins')
  locations_twitter = MongoDB.get_collection(database_name='twitter', collection_name='locations')

  twitter_user_checkins = {} # {'#id':[{creatAt: time, 'location':{'lat':, 'lng':}}]}
  twitter_user_info = {} # {'#id': {'screen_name', 'name'}}
  for checkin in checkins_twitter.find():
    # get user_id of the checkin
    try:
      user_id = str(checkin['user_id'])
      time =checkin['created_at']
      onwer_of_checkin = users_twitter.find_one({'id': user_id})
      if onwer_of_checkin == None:
        print("can't find owner")
        continue
    except Exception as err:
      print('err to get user_id ', err)
      continue
    # get coordinate of the checkin
    try:
      coordinate = checkin['coordinates']['coordinates']
    except Exception as err:
      print('error to get coordinate of the checkin ', err)
      print('start to look at geo')
      try:
        coordinate = list(reversed(checkin['geo']['coordinates'])) # list of [lat, lng]
      except Exception as err:
        print('error to get coordinate from geo ', err)
        print('start to lock at location ')
        try:
          location = locations_twitter.find_one({'id': checkin['location_id']})
          coordinate = location['centroid'] # list of [lat, lng]
        except Exception as err:
          print('error to get coordinate at all ', err)
          continue

    if twitter_user_checkins.get(user_id) == None:
      twitter_user_checkins[user_id] = [{'createAt': time, 'location':{'lat': coordinate[0], 'lng': coordinate[1]}}]
    else:
      twitter_user_checkins[user_id].append({'createAt': time, 'location':{'lat': coordinate[0], 'lng': coordinate[1]}})

    # get user_info of the checkin
    try:
      screen_name = onwer_of_checkin['screen_name']
    except:
      screen_name = ''
    try:
      name_of_owner = name_of_owner['name']
    except:
      name_of_owner = ''
    if twitter_user_info.get(user_id) == None:
      twitter_user_info[user_id] = {'screen_name': screen_name, 'name': name_of_owner}
  Pickle.save_obj(twitter_user_info, 'twitter' + os.sep + 'twitter_user_info')
  Pickle.save_obj(twitter_user_checkins, 'twitter' + os.sep + 'twitter_user_checkins')
  return twitter_user_info, twitter_user_checkins

get_twitter_info()

def map_by_name(full_name, the_other):
  max_point = 0
  maps = None
  for key in the_other:
    point = dice_coefficient3(full_name, the_other[key]['name'])*0.8 + dice_coefficient3(full_name, the_other[key]['screen_name'])*0.2
    if point > max_point:
      max_point = point
      maps = key
  return key


def map_foursquare_twitter():
  foursquare_data = JsonObject.load_json_data(foursquare_data_path)
  twitter_user_info, twitter_user_checkins = get_twitter_info()
  mapss = []
  count = 0
  for key in foursquare_data:
    try:
      first_name = foursquare_data[key]['info']['firstName']
    except:
      first_name = ''
    try:
      last_name = foursquare_data[key]['info']['lastName']
    except:
      last_name = ''
    foursquare_full_name = first_name + last_name
    try:
      foursquare_checkins = foursquare_data[key]['checkins'] # list of checkins as dict {'location':{'lat':,'lng':}, 'createAt'}
    except:
      print('some how...')
      continue

    # find max_point of full name
    maps_key = map_by_name(foursquare_full_name, twitter_user_info)
    maps_info = {'F_id': key, 'F_full_name': foursquare_full_name, 'T_id': maps_key, \
                  'T_user_name': twitter_user_info[maps_key]['screen_name'], 'T_full_name': twitter_user_info[maps_key]['name']}
    mapss.append(maps_info)
    count += 1
    if count < 20:
      print(maps_info)
    # calculate point of location checkin
  Pickle.save_obj(mapss, 'maps')


# map_foursquare_twitter()

