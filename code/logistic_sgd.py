"""
This tutorial introduces logistic regression using Theano and stochastic 
gradient descent.  

Logistic regression is a probabilistic, linear classifier. It is parametrized
by a weight matrix :math:`W` and a bias vector :math:`b`. Classification is
done by projecting data points onto a set of hyperplanes, the distance to
which is used to determine a class membership probability. 

Mathematically, this can be written as:

.. math::
  P(Y=i|x, W,b) &= softmax_i(W x + b) \\
                &= \frac {e^{W_i x + b_i}} {\sum_j e^{W_j x + b_j}}


The output of the model or prediction is then done by taking the argmax of 
the vector whose i'th element is P(Y=i|x).

.. math::

  y_{pred} = argmax_i P(Y=i|x,W,b)


This tutorial presents a stochastic gradient descent optimization method 
suitable for large datasets, and a conjugate gradient optimization method 
that is suitable for smaller datasets.


References:

    - textbooks: "Pattern Recognition and Machine Learning" - 
                 Christopher M. Bishop, section 4.3.2

"""
__docformat__ = 'restructedtext en'

import time, cPickle, gzip

import numpy, theano
import theano.tensor as T
import theano.tensor.nnet


class LogisticRegression(object):
    """Multi-class Logistic Regression Class

    The logistic regression is fully described by a weight matrix :math:`W` 
    and bias vector :math:`b`. Classification is done by projecting data 
    points onto a set of hyperplanes, the distance to which is used to 
    determine a class membership probability. 
    """




    def __init__(self, input, n_in, n_out):
        """ Initialize the parameters of the logistic regression

        :param input: symbolic variable that describes the input of the 
        architecture (one minibatch)

        :param n_in: number of input units, the dimension of the space in 
        which the datapoints lie

        :param n_out: number of output units, the dimension of the space in 
        which the labels lie

        """ 

        # initialize with 0 the weights W as a matrix of shape (n_in, n_out) 
        self.W = theano.shared(value=numpy.zeros((n_in,n_out), dtype = theano.config.floatX),
                                name='W')
        # initialize the baises b as a vector of n_out 0s
        self.b = theano.shared(value=numpy.zeros((n_out,), dtype = theano.config.floatX),
                               name='b')


        # compute vector of class-membership probabilities in symbolic form
        self.p_y_given_x = T.nnet.softmax(T.dot(input, self.W)+self.b)

        # compute prediction as class whose probability is maximal in 
        # symbolic form
        self.y_pred=T.argmax(self.p_y_given_x, axis=1)





    def negative_log_likelihood(self, y):
        """Return the mean of the negative log-likelihood of the prediction
        of this model under a given target distribution.

        .. math::

            \frac{1}{|\mathcal{D}|} \mathcal{L} (\theta=\{W,b\}, \mathcal{D}) =
            \frac{1}{|\mathcal{D}|} \sum_{i=0}^{|\mathcal{D}|} \log(P(Y=y^{(i)}|x^{(i)}, W,b)) \\
                \ell (\theta=\{W,b\}, \mathcal{D})


        :param y: corresponds to a vector that gives for each example the
        :correct label

        Note: we use the mean instead of the sum so that
        the learning rate is less dependent on the batch size
        """
        return -T.mean(T.log(self.p_y_given_x)[T.arange(y.shape[0]),y])
        #return -T.sum(T.log(self.p_y_given_x)[T.arange(y.shape[0]),y])/200





    def errors(self, y):
        """Return a float representing the number of errors in the minibatch 
        over the total number of examples of the minibatch ; zero one
        loss over the size of the minibatch
        """

        # check if y has same dimension of y_pred 
        if y.ndim != self.y_pred.ndim:
            raise TypeError('y should have the same shape as self.y_pred', 
                ('y', target.type, 'y_pred', self.y_pred.type))
        # check if y is of the correct datatype        
        if y.dtype.startswith('int'):
            # the T.neq operator returns a vector of 0s and 1s, where 1
            # represents a mistake in prediction
            return T.mean(T.neq(self.y_pred, y))
        else:
            raise NotImplementedError()


def sgd_optimization_mnist(learning_rate=0.13, n_iter=100, mnist_pkl_gz='mnist.pkl.gz'):
    """
    Demonstrate stochastic gradient descent optimization of a log-linear 
    model

    This is demonstrated on MNIST.
    
    :param learning_rate: learning rate used (factor for the stochastic 
    gradient

    :param n_iter: maximal number of iterations ot run the optimizer 

    :param mnist_pkl_gz: the path of the mnist training file from 
                         http://www.iro.umontreal.ca/~lisa/deep/data/mnist/mnist.pkl.gz

    """

    # Load the dataset 
    f = gzip.open(mnist_pkl_gz,'rb')
    train_set, valid_set, test_set = cPickle.load(f)
    f.close()


    def shared_dataset(data_xy):
        data_x, data_y = data_xy
        shared_x = theano.shared(numpy.asarray(data_x, dtype=theano.config.floatX))
        shared_y = theano.shared(numpy.asarray(data_y, dtype=theano.config.floatX))
        return shared_x, T.cast(shared_y, 'int32')

    test_set_x, test_set_y = shared_dataset(test_set)
    valid_set_x, valid_set_y = shared_dataset(valid_set)
    train_set_x, train_set_y = shared_dataset(train_set)

    batch_size = 500    # sized of the minibatch

    n_minibatches = train_set_x.value.shape[0]/batch_size

    # allocate symbolic variables for the data
    minibatch_offset = T.lscalar() # offset to the start of a [mini]batch 
    x = T.matrix('x')  # the data is presented as rasterized images
    y = T.ivector('y') # the labels are presented as 1D vector of 
                       # [int] labels

    # construct the logistic regression class
    # Each MNIST image has size 28*28
    classifier = LogisticRegression(
            input=x.reshape((batch_size,28*28)),
            n_in=28*28,
            n_out=10)

    # the cost we minimize during training is the negative log likelihood of 
    # the model in symbolic format
    cost = classifier.negative_log_likelihood(y) 

    # compiling a Theano function that computes the mistakes that are made by 
    # the model on a minibatch
    test_model = theano.function([minibatch_offset], classifier.errors(y),
            givens={
                x:test_set_x[minibatch_offset:minibatch_offset+batch_size],
                y:test_set_y[minibatch_offset:minibatch_offset+batch_size]})

    validate_model = theano.function([minibatch_offset], classifier.errors(y),
            givens={
                x:valid_set_x[minibatch_offset:minibatch_offset+batch_size],
                y:valid_set_y[minibatch_offset:minibatch_offset+batch_size]})

    # compute the gradient of cost with respect to theta = (W,b) 
    g_W = T.grad(cost, classifier.W)
    g_b = T.grad(cost, classifier.b)

    # specify how to update the parameters of the model as a dictionary
    updates ={classifier.W: classifier.W - learning_rate*g_W,\
              classifier.b: classifier.b - learning_rate*g_b}

    # compiling a Theano function `train_model` that returns the cost, but in 
    # the same time updates the parameter of the model based on the rules 
    # defined in `updates`
    train_model = theano.function([minibatch_offset], cost, updates = updates,
            givens={
                x:train_set_x[minibatch_offset:minibatch_offset+batch_size],
                y:train_set_y[minibatch_offset:minibatch_offset+batch_size]})

    # early-stopping parameters
    patience              = 5000  # look as this many examples regardless
    patience_increase     = 2     # wait this much longer when a new best is 
                                  # found
    improvement_threshold = 0.995 # a relative improvement of this much is 
                                  # considered significant
    validation_frequency  = n_minibatches  # go through this many 
                                  # minibatche before checking the network 
                                  # on the validation set; in this case we 
                                  # check every epoch 

    best_params          = None
    best_validation_loss = float('inf')
    test_score           = 0.
    start_time = time.clock()
    # have a maximum of `n_iter` iterations through the entire dataset
    for iter in xrange(n_iter* n_minibatches):

        # get epoch and minibatch index for training set
        epoch           = iter / n_minibatches
        minibatch_index =  iter % n_minibatches
        minibatch_offset = minibatch_index * batch_size

        # get the minibatches corresponding to `iter` modulo
        # `len(train_batches)`
        cost_ij = train_model(minibatch_offset)

        if (iter+1) % validation_frequency == 0: 
            # compute zero-one loss on validation set 
            n_valid_batches = valid_set_x.value.shape[0] / batch_size
            validation_losses = [validate_model(i*batch_size) for i in xrange(n_valid_batches)]
            this_validation_loss = numpy.mean(validation_losses)

            print('epoch %i, minibatch %i/%i, validation error %f %%' % \
                 (epoch, minibatch_index+1,n_minibatches, \
                  this_validation_loss*100.))


            # if we got the best validation score until now
            if this_validation_loss < best_validation_loss:
                #improve patience if loss improvement is good enough
                if this_validation_loss < best_validation_loss *  \
                       improvement_threshold :
                    patience = max(patience, iter * patience_increase)

                best_validation_loss = this_validation_loss
                # test it on the test set

                n_test_batches = test_set_x.value.shape[0] / batch_size
                test_losses = [test_model(i*batch_size) for i in xrange(n_test_batches)]
                test_score = numpy.mean(test_losses)

                print(('     epoch %i, minibatch %i/%i, test error of best ' 
                       'model %f %%') % \
                  (epoch, minibatch_index+1, n_minibatches,test_score*100.))

        if patience <= iter :
                break

    end_time = time.clock()
    print(('Optimization complete with best validation score of %f %%,'
           'with test performance %f %%') %  
                 (best_validation_loss * 100., test_score*100.))
    print ('The code ran for %f minutes' % ((end_time-start_time)/60.))

    print "THIS [output above] IS NOT WHAT THE DOCS SAY!"
    print "Remember to update the RST files before merging to trunk"

if __name__ == '__main__':
    sgd_optimization_mnist()

