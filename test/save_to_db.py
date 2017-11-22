from pymongo import MongoClient
import csv
import datetime

def get_date(text):
	res = None
	text_split = text.split(' ')
	for i in range(len(text_split)):
		if (text_split[i].find('/') != -1):
			res = text_split[i].split('/')
			break
	return res


def normalize(text):
	illegal = ['\xa0', '\t', '\n']
	for char in illegal:
		text = text.replace(char, ' ', 1000)
	return text


def main():
	client = MongoClient()
	db = client['project3']
	collection = db.posts

	f = open('../models/newspaper/resultdata.csv', 'r')
	reader = csv.reader(f)
	next(reader)

	for row in reader:
		document = {'title' : None, 
				'content' : None, 
				'dead' : None, 
				'injured' : None, 
				'time' : None, 
				'comments' : [], 
				'place' : {
					'raw' : None, 
					'city' : None, 
					'latLng' : {
						'lat' : None, 
						'lng' : None
								}
							},
				'__v' : 0,
				'vehicles' : [],
				'description' : None,
				'publish' : None,
				'level' : None
		}

		document['content'] = normalize(row[0])
		document['title'] = normalize(row[1])
		document['description'] = normalize(row[2])
		date_split = get_date(normalize(row[3]))
		if (date_split != None):
			document['publish'] = datetime.datetime(int(date_split[2]), int(date_split[1]), int(date_split[0]))
		else:
			print(row[3][1:-1])
			continue
		document['level'] = 0
		collection.insert_one(document)
	f.close()

if __name__ == '__main__':
	main()