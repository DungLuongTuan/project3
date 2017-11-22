import re

class InjuredDetectorRB(object):
	"""

	"""
	def __init__(self, wordtokenizer):
		self.wordtokenizer = wordtokenizer
		self.load_dictionary()


	def load_dictionary(self):
		### injury dictionary
		self.injury_dictionary = ['bị_thương', 'xây_xát', 'trọng_thương', 'chấn_thương', 'cấp_cứu', 'vết_thương', 'điều_trị']
		self.death_dictionary = ['bị_chết', 'chết', 'tử_vong', 'thiệt_mạng']
		### load human dictionary
		self.human_dictionary = ['tài_xế', 'hành_khách', 'thanh_niên', 'nạn_nhân', 'người', 'ai', 'phụ_xe', 'anh', 'chị', 'cô', 'bác', 'ông', 'bà', 'em_bé', 'bé']
		self.fuzzy = ['nhiều', 'tất_cả']


	def str_to_int(self, text):
		###
		if (text.isdigit()):
			return int(text)
		###
		text = text.lower()
		number = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười']
		if (text in number):
			return number.index(text)
		###
		return None


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


	def is_particular_noun(self, word):
		syllables = word.split('_')
		res = True
		for syllable in syllables:
			if not (syllable[0].isupper()):
				res = False
		return res


	def fix_specific_tokens(self, tokens,):
		### combine consecutive tokens have form 'Np Np Np... Np' into Np
		fixed_tokens = [tokens[0]]
		for i in range(1, len(tokens)):
			if (self.is_particular_noun(fixed_tokens[-1]) and (self.is_particular_noun(tokens[i]))):
				fixed_tokens[-1] = fixed_tokens[-1] + '_' + tokens[i]
			else:
				fixed_tokens.append(tokens[i])
		return fixed_tokens


	def remove_redundant_content(self, text):
		### remove content inside ()
		text_ = ''
		ok = True
		for i in range(len(text)):
			if (text[i] == '('):
				ok = False
				continue
			if (text[i] == ')'):
				ok = True
				continue
			if (ok):
				text_ += text[i]
		text = text_
		### remove content inside ""
		text_ = ''
		ok = True
		for i in range(len(text)):
			if ((text[i] == '"') and (ok == True)):
				ok = False
				continue
			if ((text[i] == '"') and (ok == False)):
				ok = True
				continue
			if (ok):
				text_ += text[i]
		return text_


	def get_injury_information(self, text):
		### normalize text
		text = text.replace(';', '.', 1000)
		### remove redundant content
		text = self.remove_redundant_content(text)
		### separate document into sentences
		sentence_split = text.split('.')
		exist = False
		number_wounded = set()
		for sentence in sentence_split:
			# standardize
			sentence = self.standardize(sentence)
			# word segmentation
			_, tokens = self.wordtokenizer.predict(sentence)
			# fix wrong segmentation
			tokens = self.fix_specific_tokens(tokens)
			# find injury word
			# check if sentence has injury word
			injury_word = ''
			for word in self.injury_dictionary:
				if (word in (' '.join(tokens).lower()).split(' ')):
					injury_id = (' '.join(tokens).lower()).split(' ').index(word)
					injury_word = ' '.join(tokens[(' '.join(tokens).lower()).split(' ').index(word)].split('_'))
					break
			if (injury_word == ''):
				continue
			exist = True
			# 
			sen_cnt = []
			human_id = -1
			for i in range(injury_id - 1, -1, -1):
				if ((tokens[i] == ',') or (tokens[i].lower() in self.death_dictionary)):
					break
				if (tokens[i].lower() in self.human_dictionary):
					if (i > 0):
						if (self.str_to_int(tokens[i-1].lower()) != None):
							sen_cnt.append(self.str_to_int(tokens[i-1]))
							continue
						if (tokens[i-1].lower() in self.fuzzy):
							number_wounded.add(-1)
							sen_cnt.append(0)
							continue
					sen_cnt.append(1)
			if (len(sen_cnt) != 0):
				number_wounded.add(sum(sen_cnt))
		### return
		number_wounded = list(number_wounded)
		if not exist:
			return 0
		else:
			if len(number_wounded) == 1:
				return number_wounded[0]
			else:
				return None




