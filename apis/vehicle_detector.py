class VehicleDetector(object):
	"""
		detect all the vehicle appear in paragraph
	"""
	def __init__(self):
		self.load_dictionary()

	def load_dictionary(self):
		f = open('./models/dictionary/vehicle_dictionary', 'r')
		self.vehicle_dictionary = []
		self.vehicle_labels = []
		for row in f:
			row_split = row[:-1].split('\t')
			self.vehicle_dictionary.append(row_split[0])
			self.vehicle_labels.append(row_split[1])
		f.close()

	def get_vehicle(self, text):
		text = text.lower()
		vehicles = set()
		for vehicle in self.vehicle_dictionary:
			if (vehicle in text):
				vehicles.add(self.vehicle_labels[self.vehicle_dictionary.index(vehicle)])
		return list(vehicles)