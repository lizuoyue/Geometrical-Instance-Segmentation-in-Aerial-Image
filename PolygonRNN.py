import os, re, sys
if os.path.exists('../Python-Lib/'):
	sys.path.insert(1, '../Python-Lib')
import io, glob
import numpy as np
import tensorflow as tf
from PIL import Image, ImageDraw
ut = __import__('Utility')

class PolygonRNN(object):

	def __init__(self, max_seq_len, lstm_out_channel, v_out_res, train_batch_size, pred_batch_size):
		# v_out_res: (col, row)
		assert(v_out_res == (28, 28) or v_out_res == (56, 56))

		# Parameters transferred in
		self.max_seq_len = max_seq_len
		self.lstm_out_channel = lstm_out_channel
		self.v_out_res = v_out_res
		self.train_batch_size = train_batch_size
		self.pred_batch_size = pred_batch_size

		# Parameters computed
		self.res_num = self.v_out_res[1] * self.v_out_res[0]
		self.lstm_in_channel = [133] + lstm_out_channel[: -1]

		# Create multi-layer LSTM and inital state
		self.stacked_lstm = tf.contrib.rnn.MultiRNNCell(
			[self.ConvLSTMCell(in_c, out_c) for in_c, out_c in zip(self.lstm_in_channel, self.lstm_out_channel)]
		)
		self.lstm_init_state = []
		for i, c_out in enumerate(lstm_out_channel):
			self.lstm_init_state.append(tf.get_variable('conv_lstm_cell_%d_c_h' % i, [2, self.v_out_res[1], self.v_out_res[0], c_out]))

		# Create vertex pool for prediction
		self.vertex_pool = []
		for i in range(v_out_res[1]):
			for j in range(v_out_res[0]):
				self.vertex_pool.append(np.zeros((v_out_res[1], v_out_res[0]), dtype = np.float32))
				self.vertex_pool[i * v_out_res[0] + j][i, j] = 1.0
		self.vertex_pool.append(np.zeros((v_out_res[1], v_out_res[0]), dtype = np.float32))
		self.vertex_pool = np.array(self.vertex_pool)

	def ConvLSTMCell(self, input_channels, output_channels):
		return tf.contrib.rnn.ConvLSTMCell(
			conv_ndims = 2,
			input_shape = [self.v_out_res[1], self.v_out_res[0], input_channels],
			output_channels = output_channels,
			kernel_shape = [3, 3]
		)

	def ModifiedVGG16For28(self, x, reuse = None):
		with tf.variable_scope('ModifiedVGG16For28', reuse = reuse):
			conv1_1 = tf.layers.conv2d(
				inputs = x,
				filters = 64,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv1_2 = tf.layers.conv2d(
				inputs = conv1_1,
				filters = 64,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			pool1 = tf.layers.max_pooling2d(
				inputs = conv1_2,
				pool_size = (2, 2),
				strides = 2
			)
			conv2_1 = tf.layers.conv2d(
				inputs = pool1,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv2_2 = tf.layers.conv2d(
				inputs = conv2_1,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			pool2 = tf.layers.max_pooling2d(
				inputs = conv2_2,
				pool_size = (2, 2),
				strides = 2
			)
			conv3_1 = tf.layers.conv2d(
				inputs = pool2,
				filters = 256,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv3_2 = tf.layers.conv2d(
				inputs = conv3_1,
				filters = 256,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv3_3 = tf.layers.conv2d(
				inputs = conv3_2,
				filters = 256,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			pool3 = tf.layers.max_pooling2d(
				inputs = conv3_3,
				pool_size = (2, 2),
				strides = 2
			)
			conv4_1 = tf.layers.conv2d(
				inputs = pool3,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv4_2 = tf.layers.conv2d(
				inputs = conv4_1,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv4_3 = tf.layers.conv2d(
				inputs = conv4_2,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			pool4 = tf.layers.max_pooling2d(
				inputs = conv4_3,
				pool_size = (2, 2),
				strides = 2
			)
			conv5_1 = tf.layers.conv2d(
				inputs = pool4,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv5_2 = tf.layers.conv2d(
				inputs = conv5_1,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv5_3 = tf.layers.conv2d(
				inputs = conv5_2,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part1_pool = tf.layers.max_pooling2d(
				inputs = pool2,
				pool_size = (2, 2),
				strides = 2
			)
			part1 = tf.layers.conv2d(
				inputs = part1_pool,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part2 = tf.layers.conv2d(
				inputs = pool3,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part3 = tf.layers.conv2d(
				inputs = conv4_3,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part4_conv = tf.layers.conv2d(
				inputs = conv5_3,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part4 = tf.image.resize_images(
				images = part4_conv,
				size = [28, 28]
			)
			comb = tf.concat([part1, part2, part3, part4], 3)
			feature = tf.layers.conv2d(
				inputs = comb,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			return feature

	def ModifiedVGG16For56(self, x, reuse = None):
		with tf.variable_scope('ModifiedVGG16For56', reuse = reuse):
			conv1_1 = tf.layers.conv2d(
				inputs = x,
				filters = 64,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv1_2 = tf.layers.conv2d(
				inputs = conv1_1,
				filters = 64,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			pool1 = tf.layers.max_pooling2d(
				inputs = conv1_2,
				pool_size = (2, 2),
				strides = 2
			)
			conv2_1 = tf.layers.conv2d(
				inputs = pool1,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv2_2 = tf.layers.conv2d(
				inputs = conv2_1,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			pool2 = tf.layers.max_pooling2d(
				inputs = conv2_2,
				pool_size = (2, 2),
				strides = 2
			)
			conv3_1 = tf.layers.conv2d(
				inputs = pool2,
				filters = 256,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv3_2 = tf.layers.conv2d(
				inputs = conv3_1,
				filters = 256,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv3_3 = tf.layers.conv2d(
				inputs = conv3_2,
				filters = 256,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			pool3 = tf.layers.max_pooling2d(
				inputs = conv3_3,
				pool_size = (2, 2),
				strides = 2
			)
			conv4_1 = tf.layers.conv2d(
				inputs = pool3,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv4_2 = tf.layers.conv2d(
				inputs = conv4_1,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			conv4_3 = tf.layers.conv2d(
				inputs = conv4_2,
				filters = 512,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part1_pool = tf.layers.max_pooling2d(
				inputs = pool1,
				pool_size = (2, 2),
				strides = 2
			)
			part1 = tf.layers.conv2d(
				inputs = part1_pool,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part2 = tf.layers.conv2d(
				inputs = pool2,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part3 = tf.layers.conv2d(
				inputs = conv3_3,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part4_conv = tf.layers.conv2d(
				inputs = conv4_3,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			part4 = tf.image.resize_images(
				images = part4_conv,
				size = [56, 56],
				method = tf.image.ResizeMethod.BICUBIC
			)
			comb = tf.concat([part1, part2, part3, part4], 3)
			feature = tf.layers.conv2d(
				inputs = comb,
				filters = 128,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.nn.relu
			)
			return feature

	def CNN(self, img, boundary_true = None, vertices_true = None, reuse = None):
		if self.v_out_res == (28, 28):
			feature = self.ModifiedVGG16For28(img, reuse)
		if self.v_out_res == (56, 56):
			feature = self.ModifiedVGG16For56(img, reuse)
		with tf.variable_scope('CNN', reuse = reuse):
			boundary = tf.layers.conv2d(
				inputs = feature,
				filters = 1,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.sigmoid
			)
			vertices = tf.layers.conv2d(
				inputs = tf.concat([feature, boundary], 3),
				filters = 1,
				kernel_size = (3, 3),
				padding = 'same',
				activation = tf.sigmoid
			)
		if not reuse:
			loss = 0.0
			n_b = tf.reduce_sum(boundary_true) / self.train_batch_size
			n_v = tf.reduce_sum(vertices_true) / self.train_batch_size
			loss += tf.losses.log_loss(
				labels = boundary_true,
				predictions = boundary,
				weights = (boundary_true * (self.res_num - 2 * n_b) + n_b)
			)
			loss += tf.losses.log_loss(
				labels = vertices_true,
				predictions = vertices,
				weights = (vertices_true * (self.res_num - 2 * n_v) + n_v))
			loss /= 16
			return tf.concat([feature, boundary, vertices], 3), loss
		else:
			idx = tf.argmax(tf.reshape(vertices, [-1, self.res_num]), axis = 1)
			v_first = tf.gather(self.vertex_pool, idx, axis = 0)
			return tf.concat([feature, boundary, vertices], 3), v_first

	def RNN(self, feature, v_in = None, rnn_out_true = None, seq_len = None, v_first = None, reuse = None):
		if not reuse:
			feature_rep = tf.tile(
				tf.reshape(feature, [-1, 1, self.v_out_res[1], self.v_out_res[0], 130]),
				[1, self.max_seq_len, 1, 1, 1]
			)
			v_in_0 = tf.tile(v_in[:, 0: 1, ...], [1, self.max_seq_len, 1, 1, 1])
			v_in_1 = v_in
			v_in_2 = tf.stack([v_in[:, 0, ...]] + tf.unstack(v_in, axis = 1)[: -1], axis = 1)
			rnn_input = tf.concat([feature_rep, v_in_0, v_in_1, v_in_2], axis = 4)
			# v_in_0:   0 0 0 0 0 ... 0
			# v_in_1:   0 1 2 3 4 ... N - 1
			# v_in_2:   0 0 1 2 3 ... N - 2
			# rnn_out:  1 2 3 4 5 ... N
			# initial_state = self.stacked_lstm.zero_state(self.train_batch_size, tf.float32)
			initial_state = tuple([tf.contrib.rnn.LSTMStateTuple(
				c = tf.tile(self.lstm_init_state[i][0: 1], [self.train_batch_size, 1, 1, 1]),
				h = tf.tile(self.lstm_init_state[i][1: 2], [self.train_batch_size, 1, 1, 1])
			) for i in range(len(lstm_out_channel))])
			outputs, state = tf.nn.dynamic_rnn(
				cell = self.stacked_lstm,
				inputs = rnn_input,
				sequence_length = seq_len,
				initial_state = initial_state,
				dtype = tf.float32
			)
			return self.FC(outputs, rnn_out_true, seq_len)
		else:
			v = [None for i in range(self.max_seq_len)]
			state = [None for i in range(self.max_seq_len)]
			rnn_output = [None for i in range(self.max_seq_len)]
			v[0] = tf.reshape(v_first, [-1, self.v_out_res[1], self.v_out_res[0], 1])
			# state[0] = self.stacked_lstm.zero_state(self.pred_batch_size, tf.float32)
			state[0] = tuple([tf.contrib.rnn.LSTMStateTuple(
				c = tf.tile(self.lstm_init_state[i][0: 1], [self.pred_batch_size, 1, 1, 1]),
				h = tf.tile(self.lstm_init_state[i][1: 2], [self.pred_batch_size, 1, 1, 1])
			) for i in range(len(lstm_out_channel))])
			for i in range(1, self.max_seq_len):
				rnn_output[i], state[i] = self.stacked_lstm(
					inputs = tf.concat([feature, v[0], v[max(i - 1, 0)], v[max(i - 2, 0)]], 3),
					state = state[i - 1]
				)
				v[i] = tf.reshape(
					self.FC(
						rnn_output = rnn_output[i],
						reuse = True
					),
					[-1, self.v_out_res[1], self.v_out_res[0], 1]
				)
			return tf.stack(v, 1)

	def FC(self, rnn_output, rnn_out_true = None, seq_len = None, reuse = None):
		if not reuse:
			output_reshape = tf.reshape(rnn_output, [-1, self.max_seq_len, self.res_num * self.lstm_out_channel[-1]])
		else:
			output_reshape = tf.reshape(rnn_output, [-1, 1, self.res_num * self.lstm_out_channel[-1]])
		with tf.variable_scope('FC', reuse = reuse):
			logits = tf.layers.dense(
				inputs = output_reshape,
				units = self.res_num + 1,
				activation = None
			)
		if not reuse:
			loss = tf.reduce_sum(
				tf.nn.softmax_cross_entropy_with_logits(
					labels = rnn_out_true,
					logits = logits
				)
			) / tf.reduce_sum(seq_len)
			return logits, loss
		else:
			idx = tf.argmax(logits, axis = 2)
			return tf.gather(self.vertex_pool, idx, axis = 0)

	def Train(self, xx, bb, vv, ii, oo, ee, ll):
		img           = tf.reshape(xx, [-1, 224, 224, 3])
		boundary_true = tf.reshape(bb, [-1, self.v_out_res[1], self.v_out_res[0], 1])
		vertices_true = tf.reshape(vv, [-1, self.v_out_res[1], self.v_out_res[0], 1])
		v_in          = tf.reshape(ii, [-1, self.max_seq_len, self.v_out_res[1], self.v_out_res[0], 1])
		v_out_true    = tf.reshape(oo, [-1, self.max_seq_len, self.res_num])
		end_true      = tf.reshape(ee, [-1, self.max_seq_len, 1])
		seq_len       = tf.reshape(ll, [-1])
		rnn_out_true  = tf.concat([v_out_true, end_true], 2)

		feature, loss_CNN = self.CNN(img, boundary_true, vertices_true)
		logits , loss_RNN = self.RNN(feature, v_in, rnn_out_true, seq_len)
		boundary = feature[..., -2: -1]
		vertices = feature[..., -1:]

		# Return
		rnn_pred = tf.nn.softmax(logits)
		v_out_pred = tf.reshape(
			rnn_pred[..., 0: self.res_num],
			[-1, self.max_seq_len, self.v_out_res[1], self.v_out_res[0]]
		)
		end_pred = tf.reshape(
			rnn_pred[..., self.res_num],
			[-1, self.max_seq_len, 1]
		)
		return loss_CNN, loss_RNN, boundary, vertices, v_out_pred, end_pred

	def Predict(self, xx):
		img = tf.reshape(xx, [-1, 224, 224, 3])
		feature, v_first = self.CNN(img, reuse = True)
		v_out_pred = self.RNN(feature, v_first = v_first, reuse = True)
		boundary = feature[..., -2: -1]
		vertices = feature[..., -1:]
		v_out_pred = v_out_pred[..., 0]
		return boundary, vertices, v_out_pred

def overlay(img, mask, v_out_res, color = (255, 0, 0)):
	org = Image.fromarray(np.array(img * 255.0, dtype = np.uint8)).convert('RGBA')
	alpha = np.array(mask * 128.0, dtype = np.uint8)
	alpha = np.concatenate(
		(
			np.ones((v_out_res, v_out_res, 1)) * color[0],
			np.ones((v_out_res, v_out_res, 1)) * color[1],
			np.ones((v_out_res, v_out_res, 1)) * color[2],
			np.reshape(alpha, (v_out_res, v_out_res, 1))
		),
		axis = 2
	)
	alpha = Image.fromarray(np.array(alpha, dtype = np.uint8), mode = 'RGBA')
	alpha = alpha.resize((224, 224), resample = Image.BICUBIC)
	merge = Image.alpha_composite(org, alpha)
	return merge

def overlayMultiMask(img, mask, v_out_res):
	merge = Image.fromarray(np.array(img * 255.0, dtype = np.uint8)).convert('RGBA')
	merge = np.array(overlay(img, mask[0], v_out_res)) / 255.0
	for i in range(1, mask.shape[0]):
		color = (255 * (i == 1), 128 * (i == 1) + (1 - i % 2) * 255, i % 2 * 255 - 255 * (i == 1))
		merge = np.array(overlay(merge, mask[i], v_out_res, color)) / 255.0
	return Image.fromarray(np.array(merge * 255.0, dtype = np.uint8)).convert('RGBA')

def visualize(path, img, boundary, vertices, v_in, b_pred, v_pred, v_out_pred, end_pred, seq_len, v_out_res, patch_info):
	# Clear last files
	for item in glob.glob(path + '/*'):
		os.remove(item)

	# Reshape
	b_pred = b_pred[..., 0]
	v_pred = v_pred[..., 0]
	end_pred = end_pred[..., 0]
	blank = np.zeros((v_out_res, v_out_res))

	# Polygon
	polygon = [None for i in range(img.shape[0])]
	for i in range(v_out_pred.shape[0]):
		v = v_in[i, 0]
		r, c = np.unravel_index(v.argmax(), v.shape)
		polygon[i] = [(c, r)]
		for j in range(seq_len[i] - 1):
			if end_pred[i, j] <= v.max():
				v = v_out_pred[i, j]
				r, c = np.unravel_index(v.argmax(), v.shape)
				polygon[i].append((c, r))

	# 
	for i in range(img.shape[0]):
		vv = np.concatenate((v_in[i, 0: 1], v_out_pred[i, 0: seq_len[i] - 1]), axis = 0)
		overlay(img[i], blank      , v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-0-img.png' % i)
		overlay(img[i], boundary[i], v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-1-bound.png' % i)
		overlay(img[i], b_pred  [i], v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-1-bound-pred.png' % i)
		overlay(img[i], vertices[i], v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-2-vertices.png' % i)
		overlay(img[i], v_pred  [i], v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-2-vertices-pred.png' % i)
		overlayMultiMask(img[i], vv, v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-3-vertices-merge.png' % i)
		# for j in range(seq_len[i]):
		# 	overlay(img[i], vv[j], v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-3-vtx-%s.png' % (i, str(j).zfill(2)))

		link = Image.new('P', (v_out_res, v_out_res), color = 0)
		draw = ImageDraw.Draw(link)
		if len(polygon[i]) == 1:
			polygon[i].append(polygon[i][0])
		draw.polygon(polygon[i], fill = 0, outline = 255)
		link = np.array(link) / 255.0
		overlay(img[i], link, v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-4-vertices-link.png' % i)

		f = open(path + '/%d-5-end-prob.txt' % i, 'w')
		for j in range(seq_len[i]):
			f.write('%.6lf\n' % end_pred[i, j])
		f.close()

	#
	return

def visualize_pred(path, img, b_pred, v_pred, v_out_pred, v_out_res, patch_info):
	# Clear last files
	for item in glob.glob(path + '/*'):
		os.remove(item)

	# Reshape
	batch_size = img.shape[0]
	b_pred = b_pred[..., 0]
	v_pred = v_pred[..., 0]
	blank = np.zeros((v_out_res, v_out_res))

	# Sequence length and polygon
	polygon = [[] for i in range(batch_size)]
	for i in range(v_out_pred.shape[0]):
		for j in range(v_out_pred.shape[1]):
			v = v_out_pred[i, j]
			if v.sum() >= 0.5:
				r, c = np.unravel_index(v.argmax(), v.shape)
				polygon[i].append((c, r))
			else:
				break
	seq_len = [len(polygon[i]) for i in range(batch_size)]

	#
	for i in range(batch_size):
		vv = v_out_pred[i, 0: seq_len[i]]
		overlay(img[i], blank      , v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-0-img.png' % i)
		overlay(img[i], b_pred[i]  , v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-1-bound-pred.png' % i)
		overlay(img[i], v_pred[i]  , v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-2-vertices-pred.png' % i)
		overlayMultiMask(img[i], vv, v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-3-vertices-merge.png' % i)
		# for j in range(seq_len[i]):
		# 	overlay(img[i], vv[j], v_out_res).save(path + '/%d-3-vtx-%s.png' % (i, str(j).zfill(2)))
		link = Image.new('P', (v_out_res, v_out_res), color = 0)
		draw = ImageDraw.Draw(link)
		if len(polygon[i]) == 1:
			polygon[i].append(polygon[i][0])
		draw.polygon(polygon[i], fill = 0, outline = 255)
		link = np.array(link) / 255.0
		overlay(img[i], link, v_out_res).resize(size = tuple(patch_info[i][0: 2]), resample = Image.BICUBIC).rotate(-patch_info[i][2]).save(path + '/%d-4-vertices-link.png' % i)

	# 
	return

class Logger(object):

	def __init__(self, log_dir):
		self.writer = tf.summary.FileWriter(log_dir)
		return

	def log_scalar(self, tag, value, step):
		summary = tf.Summary(
			value = [
				tf.Summary.Value(
					tag = tag,
					simple_value = value
				)
			]
		)
		self.writer.add_summary(summary, step)
		return

	def close(self):
		self.writer.close()
		return

if __name__ == '__main__':
	# Create new folder
	if not os.path.exists('./tmp/'):
		os.makedirs('./tmp/')
	if not os.path.exists('./res/'):
		os.makedirs('./res/')
	if not os.path.exists('./val/'):
		os.makedirs('./val/')
	if not os.path.exists('./tes/'):
		os.makedirs('./tes/')

	# Set parameters
	n_iter = 2000000
	toy = False
	data_path = '../Chicago.zip'
	if not toy:
		lr = 0.0005
		max_seq_len = 24
		lstm_out_channel = [32, 16, 8]
		v_out_res = (28, 28)
		train_batch_size = 9
		pred_batch_size = 25
	else:
		lr = 0.0005
		max_seq_len = 12
		lstm_out_channel = [32, 16, 8] # [32, 12]
		v_out_res = (56, 56) # (28, 28)
		train_batch_size = 9
		pred_batch_size = 25

	# Create data generator
	obj = ut.DataGenerator(fake = toy, data_path = data_path, max_seq_len = max_seq_len, resolution = v_out_res)

	# Define graph
	PolyRNNGraph = PolygonRNN(
		max_seq_len = max_seq_len,
		lstm_out_channel = lstm_out_channel, 
		v_out_res = v_out_res,
		train_batch_size = train_batch_size,
		pred_batch_size = pred_batch_size
	)
	xx = tf.placeholder(tf.float32)
	bb = tf.placeholder(tf.float32)
	vv = tf.placeholder(tf.float32)
	ii = tf.placeholder(tf.float32)
	oo = tf.placeholder(tf.float32)
	ee = tf.placeholder(tf.float32)
	ll = tf.placeholder(tf.float32)
	result = PolyRNNGraph.Train(xx, bb, vv, ii, oo, ee, ll)
	pred = PolyRNNGraph.Predict(xx)

	# for v in tf.global_variables():
	# 	print(v.name)
	# quit()

	optimizer = tf.train.AdamOptimizer(learning_rate = lr)
	train = optimizer.minimize(result[0] + result[1])
	saver = tf.train.Saver(max_to_keep = 3)
	init = tf.global_variables_initializer()

	# Launch graph
	with tf.Session() as sess:
		# Create loggers
		f = open('./PolygonRNN-%d.out' % v_out_res, 'a')
		train_writer = Logger('./log/train/')
		valid_writer = Logger('./log/valid/')

		# Restore weights
		if len(sys.argv) > 1 and sys.argv[1] != None:
			saver.restore(sess, './tmp/model-%s.ckpt' % sys.argv[1])
			iter_obj = range(int(sys.argv[1]) + 1, n_iter)
		else:
			sess.run(init)
			iter_obj = range(n_iter)

		# Main loop
		for i in iter_obj:
			# Get training batch data and create feed dictionary
			img, boundary, vertices, v_in, v_out, end, seq_len, patch_info = obj.getDataBatch(train_batch_size, mode = 'train')
			feed_dict = {xx: img, bb: boundary, vv: vertices, ii: v_in, oo: v_out, ee: end, ll: seq_len}

			# Training and get result
			sess.run(train, feed_dict)
			loss_CNN, loss_RNN, b_pred, v_pred, v_out_pred, end_pred = sess.run(result, feed_dict)
			train_writer.log_scalar('Loss CNN' , loss_CNN, i)
			train_writer.log_scalar('Loss RNN' , loss_RNN, i)
			train_writer.log_scalar('Loss Full', loss_CNN + loss_RNN, i)

			# Write loss to file
			print('Train Iter %d, %.6lf, %.6lf, %.6lf' % (i, loss_CNN, loss_RNN, loss_CNN + loss_RNN))
			f.write('Train Iter %d, %.6lf, %.6lf, %.6lf\n' % (i, loss_CNN, loss_RNN, loss_CNN + loss_RNN))
			f.flush()

			# Visualize
			visualize('./res', img, boundary, vertices, v_in, b_pred, v_pred, v_out_pred, end_pred, seq_len, v_out_res, patch_info)

			# Save model
			if i % 200 == 0:
				saver.save(sess, './tmp/model-%d.ckpt' % i)

			# Cross validation
			if i % 200 == 0:
				# Get validation batch data and create feed dictionary
				img, boundary, vertices, v_in, v_out, end, seq_len, patch_info = obj.getDataBatch(pred_batch_size, mode = 'valid')
				feed_dict = {xx: img, bb: boundary, vv: vertices, ii: v_in, oo: v_out, ee: end, ll: seq_len}

				# Validation and get result
				loss_CNN, loss_RNN, b_pred, v_pred, v_out_pred, end_pred = sess.run(result, feed_dict)
				valid_writer.log_scalar('Loss CNN' , loss_CNN, i)
				valid_writer.log_scalar('Loss RNN' , loss_RNN, i)
				valid_writer.log_scalar('Loss Full', loss_CNN + loss_RNN, i)

				# Write loss to file
				print('Valid Iter %d, %.6lf, %.6lf, %.6lf' % (i, loss_CNN, loss_RNN, loss_CNN + loss_RNN))
				f.write('Valid Iter %d, %.6lf, %.6lf, %.6lf\n' % (i, loss_CNN, loss_RNN, loss_CNN + loss_RNN))
				f.flush()

				# Visualize
				visualize('./val', img, boundary, vertices, v_in, b_pred, v_pred, v_out_pred, end_pred, seq_len, v_out_res, patch_info)

				# Prediction
				b_pred, v_pred, v_out_pred = sess.run(pred, feed_dict)
				visualize_pred('./tes', img, b_pred, v_pred, v_out_pred, v_out_res, patch_info)

		# End main loop
		train_writer.close()
		valid_writer.close()
		f.close()

