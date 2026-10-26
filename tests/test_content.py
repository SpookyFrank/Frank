import unittest
from bot.content import choose_fact, video_metadata
class ContentTests(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(choose_fact('2026-10-25'),choose_fact('2026-10-25'))
    def test_marker(self):
        self.assertIn('science-shorts:2026-10-25',video_metadata(choose_fact('2026-10-25'),'2026-10-25')['marker'])
if __name__=='__main__': unittest.main()
