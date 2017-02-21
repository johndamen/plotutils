import unittest
from . import axpositioning

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(axpositioning)
    unittest.TextTestRunner(verbosity=1).run(suite)
