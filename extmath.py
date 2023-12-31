"""
Extended math utilities.
Source:
https://github.com/scikit-learn/scikit-learn/blob/babe4a5d0637ca172d47e1dfdd2f6f3c3ecb28db/scikits/learn/utils/extmath.py#L105
"""
# Authors: G. Varoquaux, A. Gramfort, A. Passos, O. Grisel
# License: BSD

import math

import numpy as np

##from scipy import linalg
##from scipy import sparse
import scipy.sparse
import scipy.linalg
from functools import reduce

def check_random_state(seed):
    """Turn seed into a np.random.RandomState instance

    If seed is None, return the RandomState singleton used by np.random.
    If seed is an int, return a new RandomState instance seeded with seed.
    If seed is already a RandomState instance, return it.
    Otherwise raise ValueError.
    """
    if seed is None or seed is np.random:
        return np.random.mtrand._rand
    if isinstance(seed, int):
        return np.random.RandomState(seed)
    if isinstance(seed, np.random.RandomState):
        return seed
    raise ValueError('%r cannot be used to seed a numpy.random.RandomState'
                     ' instance' % seed)

def qr_economic(A, **kwargs):
    """Compat function for the QR-decomposition in economic mode

    Scipy 0.9 changed the keyword econ=True to mode='economic'
    """
    # trick: triangular solve has introduced in 0.9
    if hasattr(scipy.linalg, 'solve_triangular'):
        return scipy.linalg.qr(A, mode='economic', **kwargs)
    else:
        return scipy.linalg.qr(A, econ=True, **kwargs)

def norm(v):
    v = np.asarray(v)
    __nrm2, = linalg.get_blas_funcs(['nrm2'], [v])
    return __nrm2(v)

def _fast_logdet(A):
    """
    Compute log(det(A)) for A symmetric
    Equivalent to : np.log(np.linalg.det(A))
    but more robust
    It returns -Inf if det(A) is non positive or is not defined.
    """
    # XXX: Should be implemented as in numpy, using ATLAS
    # http://projects.scipy.org/numpy/browser/trunk/numpy/linalg/linalg.py#L1559
    ld = np.sum(np.log(np.diag(A)))
    a = np.exp(ld / A.shape[0])
    d = np.linalg.det(A / a)
    ld += np.log(d)
    if not np.isfinite(ld):
        return -np.inf
    return ld

def _fast_logdet_numpy(A):
    """
    Compute log(det(A)) for A symmetric
    Equivalent to : np.log(nl.det(A))
    but more robust
    It returns -Inf if det(A) is non positive or is not defined.
    """
    sign, ld = np.linalg.slogdet(A)
    if not sign > 0:
        return -np.inf
    return ld

# Numpy >= 1.5 provides a fast logdet
if hasattr(np.linalg, 'slogdet'):
    fast_logdet = _fast_logdet_numpy
else:
    fast_logdet = _fast_logdet

try:
    import math
    factorial = math.factorial
except AttributeError:
    # math.factorial is only available in Python >= 2.6
    import operator
    def factorial(x):
        return reduce(operator.mul, range(2, x+1), 1)

try:
    import itertools
    combinations = itertools.combinations
except AttributeError:
    def combinations(seq, r=None):
        """Generator returning combinations of items from sequence <seq>
        taken <r> at a time. Order is not significant. If <r> is not given,
        the entire sequence is returned.
        """
        if r == None:
            r = len(seq)
        if r <= 0:
            yield []
        else:
            for i in range(len(seq)):
                for cc in combinations(seq[i+1:], r-1):
                    yield [seq[i]]+cc

def density(w, **kwargs):
    """Compute density of a sparse vector

    Return a value between 0 and 1
    """
    d = 0 if w is None else float((w != 0).sum()) / w.size
    return d

def safe_sparse_dot(a, b, dense_output=False):
    """Dot product that handle the sparse matrix case correctly"""
    if scipy.sparse.issparse(a) or scipy.sparse.issparse(b):
        ret = a * b
        if dense_output and hasattr(ret, "toarray"):
            ret = ret.toarray()
        return ret
    else:
        return np.dot(a,b)

def fast_svd(M, k, p=None, q=0, transpose='auto', random_state=0):
    """Computes the k-truncated randomized SVD

    Parameters
    ===========
    M: ndarray or sparse matrix
        Matrix to decompose

    k: int
        Number of singular values and vectors to extract.

    p: int (default is k)
        Additional number of samples of the range of M to ensure proper
        conditioning. See the notes below.

    q: int (default is 0)
        Number of power iterations (can be used to deal with very noisy
        problems).

    transpose: True, False or 'auto' (default)
        Whether the algorithm should be applied to M.T instead of M. The
        result should approximately be the same. The 'auto' mode will
        trigger the transposition if M.shape[1] > M.shape[0] since this
        implementation of randomized SVD tend to be a little faster in that
        case).

    random_state: RandomState or an int seed (0 by default)
        A random number generator instance to make behavior

    Notes
    =====
    This algorithm finds the exact truncated singular values decomposition
    using randomization to speed up the computations. It is particularly
    fast on large matrices on which you whish to extract only a small
    number of components.

    (k + p) should be strictly higher than the rank of M. This can be
    checked by ensuring that the lowest extracted singular value is on
    the order of the machine precision of floating points.

    References
    ==========
    Finding structure with randomness: Stochastic algorithms for constructing
    approximate matrix decompositions
    Halko, et al., 2009 (arXiv:909)

    A randomized algorithm for the decomposition of matrices
    Per-Gunnar Martinsson, Vladimir Rokhlin and Mark Tygert
    """
    if p == None:
        p = k

    random_state = check_random_state(random_state)
    n_samples, n_features = M.shape

    if transpose == 'auto' and n_samples > n_features:
        transpose = True
    if transpose:
        # this implementation is a bit faster with smaller shape[1]
        M = M.T

   # generating random gaussian vectors r with shape: (M.shape[1], k + p)
    r = random_state.normal(size=(M.shape[1], k + p))

    # sampling the range of M using by linear projection of r
    Y = safe_sparse_dot(M, r)
    del r

    # apply q power iterations on Y to make to further 'imprint' the top
    # singular values of M in Y
    for i in range(q):
        Y = safe_sparse_dot(M, safe_sparse_dot(M.T, Y))

    # extracting an orthonormal basis of the M range samples
##    from .fixes import qr_economic
    Q, R = qr_economic(Y)
    del R

    # project M to the (k + p) dimensional space using the basis vectors
    B = safe_sparse_dot(Q.T, M)

    # compute the SVD on the thin matrix: (k + p) wide
    Uhat, s, V = scipy.linalg.svd(B, full_matrices=False)
    del B
    U = np.dot(Q, Uhat)

    if transpose:
        # transpose back the results according to the input convention
        return V[:k, :].T, s[:k], U[:, :k].T
    else:
        return U[:, :k], s[:k], V[:k, :]
