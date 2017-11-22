import numpy as np
import tensorflow as tf
import pickle
import fasttext as ft
import re

class WordTokenizer(object):
    '''Word segmentation using Bi-directional LSTM.

    10-fold cross validation on VLSP provides the accuracy of 97.5??
   
    Attributes:
		norm_text: text normalizer
        word2vec: word to vector
    '''
    
    def __init__(self, word2vec, sess):
        '''Initilization.'''
        self.model_file = './models/dwordtoken/model29.ckpt'
        self.transition_matrix_file = './models/dwordtoken/transition_matrix29'
        self.word2vec = word2vec
        self.sess = sess
        """initialize graph model"""
        self.build_model()

    def build_model(self):
        """build model"""
        self.init_placeholder()
        self.build_graph()
        

    def init_placeholder(self):
        """model parameters"""
        self.n_hidden = 100
        self.max_state = 500
        """placeholders"""
        self.x = tf.placeholder(tf.float32, [None, self.max_state, self.n_hidden])
        self.sequence_length = tf.placeholder(tf.int32, [None])

    def build_graph(self):
        self.w = tf.get_variable(shape = [2*self.n_hidden, 4], name = 'w')
        self.b = tf.get_variable(shape = [1, 4], name = 'b')
        self.fw_cell_lstm = tf.contrib.rnn.LSTMCell(self.n_hidden)
        self.bw_cell_lstm = tf.contrib.rnn.LSTMCell(self.n_hidden)
        (self.output_fw, self.output_bw), _ = tf.nn.bidirectional_dynamic_rnn(cell_fw = self.fw_cell_lstm, cell_bw = self.bw_cell_lstm, sequence_length = self.sequence_length, inputs = self.x, dtype = tf.float32)
        self.h = tf.concat([self.output_fw, self.output_bw], axis = -1)
        self.h_slice = tf.reshape(self.h, [-1, 2*self.n_hidden])
        self.output_slice = tf.matmul(self.h_slice, self.w) + self.b
        self.output = tf.reshape(self.output_slice, [-1, self.max_state, 4])

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

    def text_to_vec(self, norm_text):
        """transform sentence to sequence of vectors"""
        text_split = norm_text.split(' ')
        seq = []
        for word in text_split:
            seq.append(self.word2vec[word])
        while (len(seq) < self.max_state):
            seq.append(np.zeros(100))
        """return sequence vectors + sequence length"""
        return [seq], [len(text_split)]

    def transform(self, norm_text):
        '''Provide intermediate results for other calculation.'''
        """transform text to input's form of model"""
        seq, seqlen = self.text_to_vec(norm_text)
        """get prediction"""
        predict_output = self.sess.run(self.output, feed_dict = {self.x: seq, self.sequence_length: seqlen})
        predict_output = predict_output[0][:seqlen[0]]
        predict_labels, _ = tf.contrib.crf.viterbi_decode(predict_output, self.transition_matrix)
        """prediction to tokens"""
        tokens = []
        text_split = norm_text.split(' ')
        predict_labels.append(0)
        mark = 0
        for i in range(1, len(predict_labels)):
            if (predict_labels[i] == 0):
                token = '_'.join([text_split[k] for k in range(mark, i)])
                tokens.append(token)
                mark = i
        return None, tokens

    def predict(self, text):
        '''Provide predictions.'''
        error, tokens = self.transform(text)
        return error, tokens

    def save(self, *args, **kwargs):
        '''Any postprocessing.'''
        pass

def main():
    wordtokenizer = WordTokenizer()
    wordtokenizer.fit()
    _, tokens = wordtokenizer.predict('Cú va chạm mạnh làm anh Quý tử vong tại chỗ, người bạn gái bị thương nặng được người dân đưa đi cấp cứu')
    print(' '.join(tokens))

if __name__ == '__main__':
    main()