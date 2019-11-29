import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from ABCNN.abcnn import Graph
import tensorflow as tf
from utils.load_data import load_char_data
from ABCNN import args
os.environ['CUDA_VISIBLE_DEVICES'] = '3'
p, h, y = load_char_data('data/LCQMC_train.csv', data_size=None)
p_eval, h_eval, y_eval = load_char_data('data/LCQMC_dev.csv', data_size=1000)

p_holder = tf.placeholder(dtype=tf.int32, shape=(None, args.seq_length), name='p')
h_holder = tf.placeholder(dtype=tf.int32, shape=(None, args.seq_length), name='h')
y_holder = tf.placeholder(dtype=tf.int32, shape=None, name='y')

dataset = tf.data.Dataset.from_tensor_slices((p_holder, h_holder, y_holder))
dataset = dataset.batch(args.batch_size).repeat(args.epochs)
iterator = dataset.make_initializable_iterator()
next_element = iterator.get_next()

# model = Graph(False, False)
model = Graph(True, True)
saver = tf.train.Saver()

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
config.gpu_options.per_process_gpu_memory_fraction = 0.7
best_acc = 0.0
best_epoch = 0
lowest_loss = 0.0

with tf.Session(config=config)as sess:
    sess.run(tf.global_variables_initializer())
    sess.run(iterator.initializer, feed_dict={p_holder: p, h_holder: h, y_holder: y})
    steps = int(len(y) / args.batch_size)
    for epoch in range(args.epochs):
        for step in range(steps):
            p_batch, h_batch, y_batch = sess.run(next_element)
            _, loss, acc = sess.run([model.train_op, model.loss, model.acc],
                                    feed_dict={model.p: p_batch,
                                               model.h: h_batch,
                                               model.y: y_batch,
                                               model.keep_prob: args.keep_prob})
            #print('epoch:', epoch, ' step:', step, ' loss: ', loss, ' acc:', acc)

        loss_eval, acc_eval = sess.run([model.loss, model.acc],
                                       feed_dict={model.p: p_eval,
                                                  model.h: h_eval,
                                                  model.y: y_eval,
                                                  model.keep_prob: 1})
        print('epoch:', epoch, 'loss_eval: ', loss_eval, ' acc_eval:', acc_eval)
        print('\n')
        if acc_eval >= best_acc:
            saver.save(sess, f'../output/abcnn/abcnn_best.ckpt')
            best_epoch = epoch
            lowest_loss = loss_eval
            best_acc = acc_eval
    print('Best epoch:', best_epoch, 'loss_eval: ', lowest_loss, ' acc_eval:', best_acc)