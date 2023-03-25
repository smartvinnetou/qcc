# python3
"""Example: Various Techniques for State Preparation."""

import math
import random
from typing import List

from absl import app
import numpy as np

from src.lib import circuit
from src.lib import helper
from src.lib import ops
from src.lib import state


# --------------------------------------------------------------
# State Preparation with Amplitude Amplification.
#
# This is kind of neat trick. We used the Grover operator for
# amplitude amplification, which in effect sets high probabilities
# for the states we are interested in.
#
# This technique works for cases where we want to produce a
# state with a smaller number of equal-probability states, all having
# the same probability alpha (a), eg., a state vector of the form:
#  [0.0 a 0.0 0.0 a a 0.0 0.0 ... 0.0 a 0.0]^T
# --------------------------------------------------------------

def make_f(dim: int, states: List[int]):
  """Construct function that will return 1 for each entry in states."""

  answers = np.zeros(1 << dim, dtype=np.int8)
  answers[states] = 1
  return lambda bits: answers[helper.bits2val(bits)]


def run_experiment_qaa(nbits: int, states: List[int]) -> None:
  """Run oracle-based experiment."""

  # In the following, we construct and apply the Grover operator similar to
  # what was shown in grover.py and amplitude_amplification.py. There are
  # many more comments to be found in those files.
  #
  op_zero = ops.ZeroProjector(nbits)
  reflection = op_zero * 2.0 - ops.Identity(nbits)
  f = make_f(nbits, states)
  uf = ops.OracleUf(nbits + 1, f)

  psi = state.zeros(nbits) * state.ones(1)
  for i in range(nbits + 1):
    psi.apply1(ops.Hadamard(), i)

  hn = ops.Hadamard(nbits)
  inversion = hn(reflection(hn)) * ops.Identity()
  grover = inversion(uf)

  iterations = int(math.pi / 4 * math.sqrt(2**nbits / len(states)))
  for _ in range(iterations):
    psi = grover(psi)

  # At this point amplitude amplification is done and the states of
  # interest should have meaningfully higher probabilities than any
  # of the other states. All these states' probabilities will be the same.
  #
  prob_states = []
  probability = 0.0
  rprob = 0.0
  for idx, val in enumerate(psi):
    if val > 0.09:
      bin_pattern = helper.val2bits(idx, nbits)[:-1]
      probability = np.real(val * val.conj())
      prob_states.append(helper.bits2val(bin_pattern))
      continue
    rprob = max(rprob, val)

  print(f'Prob: {probability:.3f}, Rest: {np.real(rprob * rprob.conj()):.3f} '
        f'Factor: {probability / np.real(rprob * rprob.conj()):5.1f} '
        f' {sorted(prob_states)} ')
  if sorted(prob_states) != sorted(states):
    raise AssertionError('Incorrect state preparation')


# --------------------------------------------------------------
# Single-Qubit State Preparation with Rotations.
#
# This represents amplitude encoding for a state:
#    [alpha  beta]^T
# By either specifying alpha (via arccos) or beta (via arcsin).
# --------------------------------------------------------------
def run_experiment_alpha(alpha) -> None:
  """Make a single qubit state."""

  qc = circuit.qc('single qubit')
  x = qc.reg(1, 0)
  qc.ry(0, 2 * np.arccos(alpha))
  if not np.allclose(qc.psi[0], alpha, atol=1e-5):
    raise AssertionError('Incorrect qubit preparation.')
  print(f'Single qubit (alpha: {alpha:.2f}): '
        f'[{qc.psi[0]:.2f}, {qc.psi[1]:.2f}]')


def run_experiment_beta(beta) -> None:
  """Make a single qubit state."""

  qc = circuit.qc('single qubit')
  x = qc.reg(1, 0)
  qc.ry(0, 2 * np.arcsin(beta))
  if not np.allclose(qc.psi[1], beta, atol=1e-5):
    raise AssertionError('Incorrect qubit preparation.')
  print(f'Single qubit (beta : {beta:.2f}): '
        f'[{qc.psi[0]:.2f}, {qc.psi[1]:.2f}]')


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  print('State preparation with QAA.')
  for n in range(20):
    # Factors can be be larger and larger just by increasing
    # the number of qubits.
    nbits = 8
    run_experiment_qaa(nbits, random.sample(range(10, 1 << (nbits-1)), 5 + n))

  print('Single qubit initialization via rotation.')
  for _ in range(5):
    run_experiment_alpha(random.random())
  for _ in range(5):
    run_experiment_beta(random.random())


if __name__ == '__main__':
  app.run(main)
