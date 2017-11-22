import numpy as np 
import re
import os
import subprocess

class InjuredDetector(object):
	"""
		detect number of injured people in paragraph
	"""

	def __init__(self, wordtokenizer):
		self.wordtokenizer = wordtokenizer
		self.load_dictionary()


	def load_dictionary(self):
		### injury dictionary
		self.injury_dictionary = ['bị_thương', 'xây_xát', 'trọng_thương', 'chấn_thương', 'cấp_cứu']
		### load human dictionary
		f = open('./models/dictionary/human_dictionary', 'r')
		self.human_dictionary = []
		for row in f:
			self.human_dictionary.append(row[:-1])
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
			if (text[i] == '"'):
				ok = False
				continue
			if (text[i] == '"'):
				ok = True
				continue
			if (ok):
				text_ += text[i]
		return text_


	def feed_input_syntaxnet(self, tokens):
		f = open('./models/syntaxnet/syntaxnet/models/data/sentence', 'w')
		for i in range(len(tokens)):
			token = ' '.join(tokens[i].split('_'))
			f.write(str(i+1) + '\t' + token + '\t' + '_' + '\t' + '_' + '\t' + '_' + '\t' + '_' + '\t' + '0' + '\t' + '_' + '\t' + '_' + '\t' + '_')
			if (i < len(tokens) - 1):
				f.write('\n')
		f.close()


	def get_output_syntaxnet(self):
		### get output syntaxnet
		f = open('./models/syntaxnet/syntaxnet/models/result/result')
		tokens = [' ']
		head = [' ']
		labels = [' ']
		for row in f:
			if not (row[0].isdigit()):
				break
			row_split = row[:-1].split('\t')
			tokens.append(row_split[1])
			head.append(row_split[6])
			labels.append(row_split[7])
		f.close()
		return tokens, head, labels


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


	def is_particular_noun(self, word):
		syllables = word.split('_')
		res = True
		for syllable in syllables:
			if not (syllable[0].isupper()):
				res = False
		return res


	def get_number_wounded(self, tokens, head, labels, injury_word):
		# define number wounded
		number_wounded = None
		### if injured word is V
		# get injury word index
		injury_word_index = tokens.index(injury_word)
		# get number modify
		for i in range(1, len(tokens)):
			if (int(head[i]) == injury_word_index):
				for j in range(1, i):
					if ((int(head[j]) == i) and (labels[j] == 'nummod')):
						number_wounded = self.str_to_int(tokens[j])
						return [number_wounded]
		# get specific wounded
		for i in range(1, len(tokens)):
			if ((int(head[i]) == injury_word_index) and (self.is_particular_noun(tokens[i]) or (tokens[i] in self.human_dictionary))):
				number_wounded = 1
		if (self.is_particular_noun(head[injury_word_index]) or tokens[head[injury_word_index]] in self.human_dictionary):
			number_wounded = 1
		if (number_wounded != None):
			return [number_wounded]
		### if injured word is N or A and supported for another word
		# get injured object index
		injured_object_index = int(head[tokens.index(injury_word)])
		# get number modify
		for i in range(1, injured_object_index):
			if ((int(head[i]) == injured_object_index) and (labels[i] == 'nummod')):
				number_wounded = self.str_to_int(tokens[i])
				break
		if (number_wounded != None):
			return [number_wounded]
		# get fuzzy number modify
		for i in range(1, injured_object_index):
			if ((int(head[i]) == injured_object_index) and (tokens[i].lower() == 'nhiều')):
				number_wounded = -1
				break
		if (number_wounded != None):
			return [number_wounded]
		# get specific wounded
		if (self.is_particular_noun(tokens[injured_object_index]) or (tokens[injured_object_index].lower() in self.human_dictionary)):
			number_wounded = 1
		if (number_wounded != None):
			return [number_wounded]
		# return None
		return []


	def get_injury_information(self, text, this_dir):
		### normalize text
		text = text.replace(';', '.', 1000)
		### remove redundant content
		text = self.remove_redundant_content(text)
		### separate document into sentences
		sentence_split = text.split('.')
		### process
		injury_information = []
		exist = False
		for sentence in sentence_split:
			# standardize
			sentence = self.standardize(sentence)
			# word segmentation
			_, tokens = self.wordtokenizer.predict(sentence)
			# fix wrong segmentation
			tokens = self.fix_specific_tokens(tokens)
			# check if sentence has injury word
			injury_word = ''
			for word in self.injury_dictionary:
				if (word in (' '.join(tokens).lower()).split(' ')):
					injury_word = ' '.join(tokens[(' '.join(tokens).lower()).split(' ').index(word)].split('_'))
					break
			if (injury_word == ''):
				continue
			exist = True
			# write sentence to file
			self.feed_input_syntaxnet(tokens)
			# run syntaxnet model
			dir_path = os.path.dirname(os.path.realpath('./models/syntaxnet/syntaxnet'))
			os.chdir(dir_path)
			subprocess.call(["cat syntaxnet/models/data/sentence | syntaxnet/run.sh"], shell = True)
			os.chdir(this_dir)
			# get output syntaxnet
			tokens, head, labels = self.get_output_syntaxnet()
			print(tokens)
			# get number of the wounded
			injury_information += self.get_number_wounded(tokens, head, labels, injury_word)

		injury_information = list(set(injury_information))
		if (exist):
			if (len(injury_information) == 1):
				return injury_information[0]
			else:
				return None
		else:
			return 0
			