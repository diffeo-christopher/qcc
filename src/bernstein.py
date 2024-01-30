# python3
"""Example: Bernstein-Vasirani Algorithm."""

from typing import Tuple
from absl import app
import numpy as np
from src.lib import helper
from src.lib import ops
from src.lib import state

# The goal of this experiment is as follows. There is 'secret' string
# in the Oracle Uf, such that the input bit string and this secret
# string compute a dot product modulo 2, resulting in 1. For example,
#
# Secret String: 0, 1, 0
#         |----|
# |0> --- |    |
# |1> --- | Uf | -- 0 or 1 as in (i0*o0 + i1*o1 + i1*o2) = 1
# |1> --- |    |
#         |----|
#
# On a classical computer, one would have to try one by one, with
# input strings that just have 1 bit set, thus requiring N queries.
# In the quantum case, the answer can be found in just 1 query.
#
# The code shows two ways to achieve this results, one with
# an explicit Uf construction, one using the Deutsch OracleUf.


def check_result(nbits: int, c: Tuple[int, ...], psi: state.State) -> None:
  """Check expected vs achieved results."""

  # The state with the 'flipped' bits will have probability 1.0.
  # It will be found on the very first try.
  #
  print('Expect:', c)
  for bits in helper.bitprod(nbits):
    if psi.prob(*bits) > 0.1:
      print(f'Found : {bits[:-1]}, with prob: {psi.prob(*bits):.1f}')
      assert bits[:-1] == c, 'Invalid result'


def make_c(nbits: int) -> Tuple[int, ...]:
  """Make a random constant c from {0,1}, which we try to find."""

  constant_c = [0] * nbits
  for idx in range(nbits - 1):
    constant_c[idx] = int(np.random.random() < 0.5)
  return tuple(constant_c)


def make_u(nbits: int, constant_c: Tuple[int, ...]) -> ops.Operator:
  """Make general Bernstein Oracle."""

  # For each '1' at index i in the constant_c, build a Cnot from
  # bit 0 to the bottom bit. For example for string |101>
  #
  # |0> --- H --- o--------
  # |0> --- H ----|--------
  # |0> --- H ----|-- o ---
  #               |   |
  # |1> --- H --- X - X ---
  #
  op = ops.Identity(nbits)
  for idx in range(nbits - 1):
    if constant_c[idx]:
      op = ops.Identity(idx) * ops.Cnot(idx, nbits - 1) @ op

      # Note that in the |+> basis, a cnot is the same as a single Z-gate.
      # Hence, this would also work:
      #   op = (ops.Identity(idx) * ops.PauliZ() *
      #         ops.Identity(nbits - 1 - idx))  @ op

  assert op.is_unitary(), 'Constructed non-unitary operator.'
  return op


def run_experiment(nbits: int) -> None:
  """Run full experiment for a given number of bits."""

  c = make_c(nbits - 1)
  u = make_u(nbits, c)

  psi = state.zeros(nbits - 1) * state.ones(1)
  psi = ops.Hadamard(nbits)(psi)
  psi = u(psi)
  psi = ops.Hadamard(nbits)(psi)

  check_result(nbits, c, psi)


# Alternative way to achieve the same result, using the
# Deutsch Oracle Uf.
#
def make_oracle_f(c: Tuple[int, ...]) -> ops.Operator:
  """Return a function computing the dot product mod 2 of bits, c."""

  def f(bit_string: Tuple[int, ...]) -> int:
    val = 0
    for idx, v in enumerate(bit_string):
      val += c[idx] * v
    return val % 2

  return f


def run_oracle_experiment(nbits: int) -> None:
  """Run full experiment for a given number of nbits bits."""

  c = make_c(nbits - 1)
  f = make_oracle_f(c)
  u = ops.OracleUf(nbits, f)

  psi = state.zeros(nbits - 1) * state.ones(1)
  psi = ops.Hadamard(nbits)(psi)
  psi = u(psi)
  psi = ops.Hadamard(nbits)(psi)

  check_result(nbits, c, psi)


def main(argv):
  assert len(argv) <= 1, 'Too many command-line parameters'

  for _ in range(5):
    run_experiment(8)
    run_oracle_experiment(8)


if __name__ == '__main__':
  app.run(main)
