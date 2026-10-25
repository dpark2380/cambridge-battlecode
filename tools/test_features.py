import unittest

import features


class FeatureTest(unittest.TestCase):
    def test_at_round(self):
        runs = [{"duration": 10, "value": "0"}, {"duration": 5, "value": "7"}, {"duration": 100, "value": "9"}]
        self.assertEqual([features.at_round(runs, r) for r in (0, 9, 10, 14, 15, 500)], [0, 0, 7, 7, 9, 9])

    def test_signatures(self):
        base = {"gems": 500, "their_gems": 1000, "rounds": 1500, "deaths": 10, "their_deaths": 10}
        self.assertEqual(features.signatures(base), ["race"])
        self.assertEqual(features.signatures(base | {"gems": 50, "deaths": 5}), ["frozen", "race"])
        self.assertIn("spiral", features.signatures(base | {"deaths": 40, "their_deaths": 15}))
        trap = base | {"deaths": 20, "deaths_by": {"camp": 15, "champion": 5}, "camp_hotspot_deaths": 9,
                       "fuel_exhausted": 0, "faults": 0}
        self.assertIn("camp_trap", features.signatures(trap))


if __name__ == "__main__":
    unittest.main()
