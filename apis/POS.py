import numpy as np 
import tensorflow as tf 
import pickle


class POS(object):
	"""

	"""

	def __init__(self, word2vec, sess):
		self.tags = ['I', 'S', 'L', 'P', 'R', 'X', 'Y', 'C', 'T', 'B', 'E', 'N', 'A', 'PUNCT', 'V', 'M']
		self.word2vec = word2vec
		self.sess = sess
		self.model_file = './models/POS/model8.ckpt'
		self.transition_matrix_file = './models/POS/transition_matrix8'
		self.build_model()


	def build_model(self):
		self.init_placeholder()
		self.build_graph()


	def init_placeholder(self):
		### parameters
		self.n_hidden = 100
		self.max_state = 150
		### placeholders
		self.x = tf.placeholder(tf.float32, [None, self.max_state, 100])
		self.y = tf.placeholder(tf.int32, [None, self.max_state])
		self.sequence_length = tf.placeholder(tf.int32, [None])


	def build_graph(self):
		with tf.variable_scope('POS'):
			self.w = tf.Variable(tf.truncated_normal([2*self.n_hidden, 16]), name = 'w_POS')
			self.b = tf.Variable(tf.truncated_normal([1, 16]), name = 'b_POS')
			self.fw_cell_lstm = tf.contrib.rnn.LSTMCell(self.n_hidden)
			self.bw_cell_lstm = tf.contrib.rnn.LSTMCell(self.n_hidden)
			(self.output_fw, self.output_bw), _ = tf.nn.bidirectional_dynamic_rnn(cell_fw = self.fw_cell_lstm, cell_bw = self.bw_cell_lstm, sequence_length = self.sequence_length, inputs = self.x, dtype = tf.float32)
			self.h = tf.concat([self.output_fw, self.output_bw], axis = -1)
			self.h_slice = tf.reshape(self.h, [-1, 2*self.n_hidden])
			self.output_slice = tf.matmul(self.h_slice, self.w) + self.b
			self.output = tf.reshape(self.output_slice, [-1, self.max_state, 16])


	def fit(self):
		'''Fit the model or load pretrained model.'''
		self.saver = tf.train.Saver()
		self.saver.restore(self.sess, self.model_file)
		f_matrix = open(self.transition_matrix_file, 'rb')
		self.transition_matrix = pickle.load(f_matrix)


	def text_normalizer(self, text):
		# Replace new line to space
		norm_text = text.replace('\n', ' ')
		# Pad punctuation with spaces on both sides
		for char in ['.', '"', ',', '(', ')', '!', '?', ';', ':', '\'s', '\'', '-']:
			norm_text = norm_text.replace(char, ' ' + char + ' ')
		return re.sub(' +', ' ', norm_text)


	def text_to_vec(self, tokens):
		seq = []
		for i in range(len(tokens)):
			seq.append(self.word2vec[tokens[i]])
		while (len(seq) < self.max_state):
			seq.append(np.zeros(100))
		return [seq], [len(tokens)]


	def transform(self, tokens):
		### change text to input vector
		seq, seq_len = self.text_to_vec(tokens)
		### transform
		predict_output = self.sess.run(self.output, feed_dict = {self.x: seq, self.sequence_length: seq_len})
		predict_output = predict_output[0][:seq_len[0]]
		predict_labels, _ = tf.contrib.crf.viterbi_decode(predict_output, self.transition_matrix)
		labels = []
		for i in range(len(predict_labels)):
			labels.append(self.tags[predict_labels[i]])
		return tokens, labels


	def predict(self, tokens):
		tokens, labels = self.transform(tokens)
		return tokens, labels

