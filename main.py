import numpy as np 
import tensorflow as tf
import fasttext as ft  
import datetime
from pymongo import MongoClient
from apis.time_detector import TimeDetector
from apis.address_detector import AddressDetector
from apis.word_tokenizer import WordTokenizer
from apis.vehicle_detector import VehicleDetector
from apis.injured_detector_syntaxnet import InjuredDetector
from apis.death_detector_syntaxnet import DeathDetector
from apis.injured_detector_rule_base import InjuredDetectorRB
from apis.death_detector_rule_base import DeathDetectorRB
from apis.POS import POS
import urllib3
import json


def main():
	### load pretrain models
	word2vec = ft.load_model('./models/word2vec/vi.bin')
	sess = tf.InteractiveSession()
	word_tokenizer = WordTokenizer(word2vec, sess)
	word_tokenizer.fit()

	### declare instants
	address_detector = AddressDetector(word_tokenizer)
	vehicle_detector = VehicleDetector()
	injured_detector = InjuredDetector(word_tokenizer)
	death_detector = DeathDetector(word_tokenizer)
	time_detector = TimeDetector()
	injured_detector_rule_base = InjuredDetectorRB(word_tokenizer)
	death_detector_rule_base = DeathDetectorRB(word_tokenizer)

	### connect db
	client = MongoClient()
	db = client['project3']
	collection = db.posts

	### define http
	http = urllib3.PoolManager()

	### process
	cnt = 0
	documents = collection.find({'level' : 0}, no_cursor_timeout = True)
	for document in documents:
		cnt += 1
		print('document ', cnt, end = '\r')

		document['level'] = 1

		time = time_detector.get_date(document['content'], str(document['publish'])[:4])
		if (time == None):
			collection.update({'_id':document['_id']}, {"$set": document}, upsert=False)
			continue

		vehicles = vehicle_detector.get_vehicle(document['content'])
		if (vehicles == None):
			collection.update({'_id':document['_id']}, {"$set": document}, upsert=False)
			continue

		woundeds = injured_detector_rule_base.get_injury_information(document['content'])
		if (woundeds == None):
			collection.update({'_id':document['_id']}, {"$set": document}, upsert=False)
			continue

		deads = death_detector_rule_base.get_death_information(document['content'])
		if (deads == None):
			collection.update({'_id':document['_id']}, {"$set": document}, upsert=False)
			continue

		address = address_detector.get_address(document['content'])
		if (address == None):
			collection.update({'_id':document['_id']}, {"$set": document}, upsert=False)
			continue

		document['level'] = 2
		document['dead'] = deads
		document['injured'] = woundeds
		document['place']['raw'] = address
		document['vehicles'] = vehicles
		date_split = time.split('-')
		document['time'] = datetime.datetime(int(date_split[0]), int(date_split[1]), int(date_split[2]))
		
		data = {'status' : 'None'}
		while ((data['status'] != 'OK') and (data['status'] != 'ZERO_RESULTS')):
			res = http.request('GET', 'https://maps.googleapis.com/maps/api/geocode/json', fields = {"address" : document['place']['raw'], "key" : "AIzaSyBQG7omCuNe8X_89xeuTb7-uo4M0QhfcZ4"})
			data = json.loads(res.data.decode('utf-8'))

		if (data['status'] == 'OK'):
			lat = data['results'][0]['geometry']['location']['lat']
			lng = data['results'][0]['geometry']['location']['lng']
			city = None
			for component in data['results'][0]['address_components']:
				if ('administrative_area_level_1' in component['types']):
					city = component['long_name']
			document['place']['latLng']['lat'] = lat
			document['place']['latLng']['lng'] = lng
			document['place']['city'] = city

		collection.update({'_id':document['_id']}, {"$set": document}, upsert=False)

	documents.close()

if __name__ == '__main__':
	main()