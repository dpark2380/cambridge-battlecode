import random
import unittest

import gate


class GateTest(unittest.TestCase):
    def decide(self, p, s0, s1, rng, cap=4000, batch=40):
        """Simulate batches of pairs (one pair per map, as gate.py plays them) until the SPRT decides."""
        scores = []
        while len(scores) < cap:
            scores += [((rng.random() < p) + (rng.random() < p)) / 2 for _ in range(batch)]
            value = gate.llr(scores, s0, s1)
            if abs(value) >= gate.BOUND:
                return value > 0
        return None

    def test_error_rates(self):
        rng = random.Random(1)
        # A truly 55% candidate should pass a 50-vs-55 gain test most of the time; a 50% one rarely.
        good = [self.decide(0.55, 0.50, 0.55, rng) for _ in range(200)]
        null = [self.decide(0.50, 0.50, 0.55, rng) for _ in range(200)]
        self.assertGreater(sum(r is True for r in good) / 200, 0.90)
        self.assertLess(sum(r is True for r in null) / 200, 0.07)


if __name__ == "__main__":
    unittest.main()
