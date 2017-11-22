import numpy as np 
import csv

def main():
	fi = open('../models/newspaper/zing.csv', 'r')
	fo = open('../models/newspaper/zing_labels.tsv', 'w')
	reader = csv.reader(fi)
	next(reader)
	cnt = 0
	for row in reader:
		cnt += 1
		if (cnt <= 300):
			continue
		print(row[0])
		label = input('label: ')
		if (label == '1'):
			fo.write(row[0] + '\t' + row[1] + '\t' + row[2] + '\t' + row[3] + '\n')
	fo.close()
	fi.close()

if __name__ == '__main__':
	main()