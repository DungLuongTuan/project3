"""
	chưa thể viết luật được do nhập nhằng trong địa chỉ của người và địa chỉ xảy ra tai nạn
	giải pháp: nhận dạng người và loại bỏ thông tin của người đó
"""
import numpy as np 
import re
from apis.word_tokenizer import WordTokenizer

class AddressDetector(object):
	"""
		detect where the acident occured
	"""

	def __init__(self, wordtokenizer):
		self.wordtokenizer = wordtokenizer
		self.load_dictionary()


	def load_dictionary(self):
		# load province dictionary
		f = open('./models/dictionary/province_dictionary', 'r')
		self.province_dictionary = []
		for row in f:
			self.province_dictionary.append(row[:-1])
		f.close()
		# load words belong to address domain (province, city, district, ...)
		f = open('./models/dictionary/address_domain', 'r')
		self.address_domain = []
		for row in f:
			self.address_domain.append(row[:-1])
		f.close()
		# load word belong to specific address domain (cross roads, bridge, pass, ...)
		f = open('./models/dictionary/specific_address_domain', 'r')
		self.specific_address_domain = []
		for row in f:
			self.specific_address_domain.append(row[:-1])
		f.close()
		# load address rules
		f = open('./models/dictionary/address_rules', 'r')
		self.start = []
		self.end = []
		self.pos = []
		for row in f:
			row_split = row[:-1].split('\t')
			self.start.append(row_split[0])
			self.end.append(row_split[1])
			self.pos.append(row_split[2])
		f.close()


	def standardize(self, text):
		### Replace new line to space
		norm_text = text.replace('\n', ' ', 1000)
		norm_text = norm_text.replace(u'\xa0', u' ', 1000)
		norm_text = norm_text.replace('_', '-', 1000)
		### Pad punctuation with spaces on both sides
		for char in ['.', '"', ',', '(', ')', '!', '?', ';', ':', '\'s', '\'', '-']:
			norm_text = norm_text.replace(char, ' ' + char + ' ')
		norm_text = re.sub(' +', ' ', norm_text)
		while (norm_text != '' and norm_text[-1] == ' '):
			norm_text = norm_text[:-1]
		while (norm_text != '' and norm_text[0] == ' '):
			norm_text = norm_text[1:]
		return norm_text


	def fix_specific_tokens1(self, tokens, np_labels):
		### combine consecutive tokens have form 'Np Np Np... Np' into Np
		fixed_tokens = [tokens[0]]
		fixed_np_labels = [np_labels[0]]
		for i in range(1, len(tokens)):
			if (np_labels[i] and fixed_np_labels[-1]):
				fixed_tokens[-1] = fixed_tokens[-1] + '_' + tokens[i]
			else:
				fixed_tokens.append(tokens[i])
				fixed_np_labels.append(np_labels[i])
		return fixed_tokens, fixed_np_labels


	def fix_specific_tokens2(self, tokens, np_labels):
		### combine consecutive tokens have form 'Np - Np - Np... - Np' into Np
		# add signal token
		tokens.append(' ')
		np_labels.append(False)
		# combine
		fixed_tokens = []
		fixed_np_labels = []
		i = 0
		while (i < len(tokens) - 1):
			if ((tokens[i] == '-' or tokens[i] == '–') and (i != 0)):
				if (fixed_np_labels[-1] and np_labels[i+1]):
					fixed_tokens[-1] = fixed_tokens[-1] + '_-_' + tokens[i+1]
					i += 2
					continue
			fixed_tokens.append(tokens[i])
			fixed_np_labels.append(np_labels[i])
			i += 1
		return fixed_tokens, fixed_np_labels


	def fix_specific_tokens3(self, tokens, np_labels):
		### change number followed by word ['đường', 'quận', 'quốc lộ']
		for i in range(1, len(tokens)):
			if (any(char.isdigit() for char in tokens[i]) and (tokens[i-1].lower() in self.specific_address_domain)):
				np_labels[i] = True
		for i in range(1, len(tokens)):
			if (any(char.isdigit() for char in tokens[i]) and (tokens[i-1].lower() in self.address_domain)):
				np_labels[i] = True
		return tokens, np_labels


	def remove_punctuation(self, tokens, np_labels):
		fixed_tokens = []
		fixed_np_labels = []
		for i in range(len(tokens)):
			if not (tokens[i] in self.punct):
				fixed_tokens.append(tokens[i])
				fixed_np_labels.append(np_labels[i])
		return fixed_tokens, fixed_np_labels


	def is_particular_noun(self, word):
		syllables = word.split('_')
		res = True
		for syllable in syllables:
			if not (syllable[0].isupper()):
				res = False
		return res


	def sentence_to_address(self, tokens, np_labels):
		# checking if Np in sentence is address or not
		raw_addresses = []
		range_token = []
		raw_type = []
		distance = 0
		ok = False
		for i in range(len(tokens)):
			if (np_labels[i]):
				# check 1 previous token
				if (i-1 >= 0):
					if (tokens[i-1].lower() in self.address_domain):
						raw_addresses.append(' '.join(self.address_domain[self.address_domain.index(tokens[i-1].lower())].split('_')) + ' ' + ' '.join(tokens[i].split('_')))
						range_token.append(distance - 1)
						raw_type.append(self.address_domain[self.address_domain.index(tokens[i-1].lower())])
						distance = 0
						ok = True
						continue
					if (tokens[i-1].lower() in self.specific_address_domain):
						raw_addresses.append(' '.join(self.specific_address_domain[self.specific_address_domain.index(tokens[i-1].lower())].split('_')) + ' ' + ' '.join(tokens[i].split('_')))
						range_token.append(distance - 1)
						raw_type.append(self.specific_address_domain[self.specific_address_domain.index(tokens[i-1].lower())])
						distance = 0
						continue
				# check 2 previous tokens
				if (i-2 >= 0):
					token = tokens[i-2] + '_' + tokens[i-1]
					if (token.lower() in self.address_domain):
						raw_addresses.append(' '.join(self.address_domain[self.address_domain.index(token.lower())].split('_')) + ' ' + ' '.join(tokens[i].split('_')))
						range_token.append(distance - 2)
						raw_type.append(self.address_domain[self.address_domain.index(token.lower())])
						distance = 0
						ok = True
						continue
					if (token.lower() in self.specific_address_domain):
						raw_addresses.append(' '.join(self.specific_address_domain[self.specific_address_domain.index(token.lower())].split('_')) + ' ' + ' '.join(tokens[i].split('_')))
						range_token.append(distance - 2)
						raw_type.append(self.specific_address_domain[self.specific_address_domain.index(token.lower())])
						distance = 0
						continue
				# check is province?
				if (tokens[i] in self.province_dictionary):
					raw_addresses.append(' '.join(tokens[i].split('_')))
					range_token.append(distance)
					raw_type.append('tỉnh')
					distance = 0
					ok = True
					continue
				# check corresponding
				if (ok):
					raw_addresses.append(' '.join(tokens[i].split('_')))
					range_token.append(distance)
					raw_type.append('UNKNOW')
					distance = 0
					ok = True
					continue
			else:
				ok = False
			distance += 1
		### check exist address
		addresses = []
		level = []
		type_set = []
		if (len(raw_addresses) == 0):
			return addresses, level
		### combine near address into 1 address
		addresses = [raw_addresses[0]]
		level = [1]
		type_set = [raw_type[0]]
		for i in range(1, len(raw_addresses)):
			if (range_token[i] <= 1) and ((raw_type[i] == 'UNKNOW') or ((raw_type[i] != 'UNKNOW') and (raw_type[i] not in type_set))):
				addresses[-1] = addresses[-1] + ',' + raw_addresses[i]
				level[-1] = level[-1] + 1
				type_set.append(raw_type[i])
			else:
				addresses.append(raw_addresses[i])
				level.append(1)
				type_set = [raw_type[i]]
		return addresses, level


	def get_address(self, text):
		### detect particular noun in sentence
		# change TP. -> TP -> tp
		text = text.replace('TP.', 'TP ', 1000)
		text = text.replace('TP', 'thành phố', 1000)
		text = text.replace(';', '.', 1000)
		# separate document into sentences
		sentences = text.split('.')
		# define list of addresses in document
		all_addresses = []
		# define punctuation
		self.punct = [',', '.', '"', '!', '?', '(', ')', '{', '}', '[', ']', '', ' ']
		
		### detect all address in each sentence
		for sentence in sentences:
			# standardize sentence
			sentence = self.standardize(sentence)
			# check is sentence
			if (sentence in ['', ' ', '\t', '\n', '\r']):
				continue
			# transform sentence into tokens
			_, tokens = self.wordtokenizer.predict(sentence)
			# label for each token if it is Np or not
			np_labels = []
			for token in tokens:
				np_labels.append(self.is_particular_noun(token))
			# fix specific wrong token
			tokens, np_labels = self.fix_specific_tokens1(tokens, np_labels)
			tokens, np_labels = self.fix_specific_tokens2(tokens, np_labels)
			tokens, np_labels = self.fix_specific_tokens3(tokens, np_labels)
			# remove all punctuation
			tokens, np_labels = self.remove_punctuation(tokens, np_labels)
			# get potential addresses
			addresses_in_sentence, level = self.sentence_to_address(tokens, np_labels)
			if not (len(addresses_in_sentence) == 0):
				all_addresses += addresses_in_sentence

		### apply rules to detect true address
		true_address = []
		for sentence in sentences:
			# standardize sentence
			sentence = self.standardize(sentence)
			# find the suitable rule for this sentence
			sub_sentence = ''
			for i in range(len(self.start)):
				if ((sentence.lower()).find(self.start[i]) != -1) and ((sentence.lower()).find(self.start[i]) < (sentence.lower()).find(self.end[i])):
					if (self.pos[i] == '1'):
						sub_sentence = sentence[:(sentence.lower()).find(self.start[i]) + len(self.start[i])]
					if (self.pos[i] == '2'):
						sub_sentence = sentence[(sentence.lower()).find(self.start[i]):(sentence.lower()).find(self.end[i]) + len(self.end[i])]
					if (self.pos[i] == '3'):
						sub_sentence = sentence[(sentence.lower()).find(self.end[i]):]
					break
			if (sub_sentence == ''):
				continue
			# check is sentence
			if (sub_sentence in ['', ' ', '\t', '\n', '\r']):
				continue
			sub_sentence = self.standardize(sub_sentence)
			# transform sentence into tokens
			_, tokens = self.wordtokenizer.predict(sub_sentence)
			# label for each token if it is Np or not
			np_labels = []
			for token in tokens:
				np_labels.append(self.is_particular_noun(token))
			# fix specific wrong token
			tokens, np_labels = self.fix_specific_tokens1(tokens, np_labels)
			tokens, np_labels = self.fix_specific_tokens2(tokens, np_labels)
			tokens, np_labels = self.fix_specific_tokens3(tokens, np_labels)
			# remove all punctuation
			tokens, np_labels = self.remove_punctuation(tokens, np_labels)
			# get potential addresses
			addresses_in_sentence, level = self.sentence_to_address(tokens, np_labels)
			if not (len(addresses_in_sentence) == 0):
				true_address += [addresses_in_sentence[np.argmax(level)]]

		### if no true address is finded, exit
		if (len(true_address) == 0):
			return None
		### combine all information to find the best address
		# match 2 address which point to 1 address
		remove_addresses = set()
		true_address_ = set([i for i in true_address])
		for i in range(len(true_address)):
			for j in range(len(true_address)):
				split_i = true_address[i].split(',')
				split_j = true_address[j].split(',')
				if (split_i[-1] in split_j) and (split_j.index(split_i[-1]) != (len(split_j) - 1)):
					true_address_.add(','.join(split_i + split_j[split_j.index(split_i[-1]) + 1:]))
					remove_addresses.add(true_address[i])
				if (split_j[-1] in split_i) and (split_i.index(split_j[-1]) != (len(split_i) - 1)):
					true_address_.add(','.join(split_j + split_i[split_i.index(split_j[-1]) + 1:]))
					remove_addresses.add(true_address[j])
		true_address = list(true_address_)
		for remove_address in remove_addresses:
			true_address.remove(remove_address)

		# check if all true addresses point to 1 address
		last_address = ''
		for i in range(len(true_address)):
			check_true_address_split = true_address[i].split(',')
			for address in all_addresses:
				address_split = address.split(',')
				for j in range(len(address_split)):
					if (address_split[j].find(check_true_address_split[-1]) != -1):
						check_true_address_split = check_true_address_split[:-1] + address_split[j:]
					if (check_true_address_split[-1].find(address_split[j]) != -1):
						check_true_address_split += address_split[j+1:]
			check_true_address = ','.join(check_true_address_split)
			if (len(check_true_address) > len(last_address)):
				last_address = check_true_address

		if (last_address == ''):
			return None
			
		if (len(last_address.split(',')) == 1) and (len(last_address.split(' ')) <= 5):
			return None

		return last_address

def main():
	wordtokenizer = WordTokenizer()
	wordtokenizer.fit()
	address_detector = AddressDetector(wordtokenizer)
	text = 'Lúc 11h ngày 29/10, tại quốc lộ 1A thuộc địa phận xã Cẩm Hưng, huyện Cẩm Xuyên, xảy ra vụ tai nạn giao thông giữa ôtô mang BKS 74C - 03323 do Hoàng Dục (44 tuổi, trú tại phường 1, TP Đông Hà, tỉnh Quảng Trị) điều khiển với môtô mang BKS 38H3  - 1466 của Bùi Quang Quyền (40 tuổi, trú tại tổ 13, thị trấn Cẩm Xuyên, huyện Cẩm Xuyên).Hậu quả Quyền tử vong. Nguyên nhân ban đầu được xác định là người lái môtô không làm chủ tốc độ, đâm vào đuôi ôtô khi đang chạy cùng chiều.Qua nắm tình hình vụ tai nạn giao thông, Công an huyện Cẩm Xuyên cho biết, Quyền là người nghiện ma tuý, có 4 tiền án, vừa ra tù tháng 3/2016, đã li dị vợ. Trước tình hình trên, lực lượng Công an Cẩm Xuyên đã nhanh chóng xác minh thông qua các mối quan hệ của Quyền. Được biết Quyền đã tâm sự với bạn bè là sẽ chuẩn bị hai quả bộc phá để ""tặng"" vợ và người tình. Qua kiểm tra nhà, hàng xóm và bạn của Quyền phát hiện 2 lon bia, một đầu được bịt kín bằng xi măng, nối với nhau bằng một số dây điện, có ăng ten và đồng hồ bấm giờ. Tại thời điểm phát hiện, người dân thấy đồng hồ bấm giờ nhảy từ số 28 sang số 29, thấy vậy người dân đã cầm ném ra vườn. Trước tình hình đó, lực lượng công an huyện đã nhanh chóng vào cuộc, thông báo di dời người dân sống xung quanh ra nơi an toàn.Sau khi nhận được thông tin, ông Dương Tất Thắng, Phó chủ tịch UBND tỉnh; đại tá Lê Văn Sao, Giám đốc Công an tỉnh; đại tá Trần Văn Sơn, Chỉ huy trưởng Bộ chỉ huy Quân sự tỉnh, đã trực tiếp xuống hiện trường, chỉ đạo xử lý vụ việc.Vụ việc đã được các lực lượng chức năng phối hợp triển khai các phương án xử lý, đảm bảo ANTT.'
	print(address_detector.get_address(text))

if __name__ == '__main__':
	main()