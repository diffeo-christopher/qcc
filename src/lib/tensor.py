# python3
# pylint: disable=invalid-name

"""Implementation of Tensor base class."""

# This file contains the implementation of the base "tensor" class for all the
# math in this compiler/simulator. This wrapping is not a unique idea,
# many open-source implementations wrap a limted set of core numpy
# functions this way, which should make compilation to, eg., TPU
# much more straight-forward.

import math

import numpy as np


# All math in this package will use this base type.
# Valid values can be np.complex128 or np.complex64
tensor_type = np.complex64

# Computed from tensor_type.
tensor_width = 128 if tensor_type == np.complex128 else 64


def accuracy_float():
  global tensor_type
  tensor_type = np.complex64


class Tensor(np.ndarray):
  """Tensor is a numpy array representing a state or operator."""

  def __new__(cls, input_array):
    return np.asarray(input_array, dtype=tensor_type).view(cls)

  def __array_finalize__(self, obj):
    if obj is None: return
    # np.ndarray has complex construction patterns. Because of this,
    # if new attributes are needed, this is the place to add them, like this:
    #    self.info = getattr(obj, 'info', None)

  @property
  def nbits(self):
    return int(math.log2(self.shape[0]))

  def is_close(self, arg):
    """Check that a 1D or 2D tensor is numerically close to arg."""

    return np.allclose(self, arg, atol=1e-6)

  def is_hermitian(self):
    """Check if this tensor is hermitian - Udag = U."""

    if len(self.shape) != 2:
      return False
    if self.shape[0] != self.shape[1]:
      return False
    return self.is_close(np.conj(self.transpose()))

  def is_unitary(self):
    """Check if this tensor is unitary - Udag*U = I."""

    return Tensor(np.matmul(np.conj(self.transpose()), self)).is_close(
        Tensor(np.eye(self.shape[0])))

  def is_density(self):
    """Check if this tensor is a density operator."""

    if not self.is_hermitian():
      return False
    if np.trace(self) - 1.0 > 1e-6:
      return False
    return True

  def is_pure(self):
    """Check if this tensor describes a pure state (else it is mixed)."""

    if not self.is_density():
      raise ValueError('ispure() can only be applied to a density matrix.')

    tr_rho2 = np.real(np.trace(np.matmul(self, self)))
    return np.allclose(tr_rho2, 1.0)

  def is_permutation(self):
    x = self #np.asanyarray(self)
    return int(x.ndim == 2 and x.shape[0] == x.shape[1] and
               (x.sum(axis=0) == 1).all() and
               (x.sum(axis=1) == 1).all() and
               ((x == 1) | (x == 0)).all())

  def kron(self, arg):
    """Return the kronecker product of this object with arg."""

    return self.__class__(np.kron(self, arg))

  def __mul__(self, arg):
    """Inline * operator maps to kronecker product."""
    return self.kron(arg)

  def pow(self, n):
    """Return the tensor product of this object with itself `n` times."""

    if n == 0:
      return 1.0

    t = self
    for _ in range(n - 1):
      t = np.kron(t, self)
    return self.__class__(t)

  def __pow__(self, n):
    """Inline operator ** maps to pow()."""
    return self.pow(n)
