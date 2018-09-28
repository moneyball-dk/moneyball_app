#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Match, UserMatch

class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        u = User(username='kasper')
        u.set_password('correct-horse')
        self.assertFalse(u.check_password('zebra'))
        self.assertTrue(u.check_password('correct-horse'))

    def test_user_match(self):
        u1 = User(username='kasper')
        u2 = User(username='felipe')
        m1 = Match()
        m2 = Match()

        db.session.add(u1)
        db.session.add(u2)
        db.session.add(m1)
        db.session.add(m2)

        db.session.commit()

        u1m1 = UserMatch(user_id=u1.id, match_id=m1.id, win=True)
        u2m1 = UserMatch(user_id=u2.id, match_id=m1.id, win=False)
        u1m2 = UserMatch(user_id=u1.id, match_id=m2.id, win=False)
        u2m2 = UserMatch(user_id=u2.id, match_id=m2.id, win=True)

        db.session.add(u1m1)
        db.session.add(u1m2)
        db.session.add(u2m1)
        db.session.add(u2m2)
        db.session.commit()

        self.assertEqual(u1.matches, [m1, m2])
        self.assertEqual(u1.won_matches, [m1])
        self.assertNotEqual(u1.lost_matches, [m1])
        self.assertEqual(u2.lost_matches, [m1])
        self.assertEqual(u2.matches, [m1, m2])
        self.assertEqual(u1.won_matches, u2.lost_matches)

        self.assertEqual(m1.players, [u1, u2])
        self.assertEqual(m1.winning_players, [u1])
        self.assertEqual(m1.losing_players, [u2])

        self.assertEqual(u1m1.user.id, u1m1.user_id)

if __name__ == '__main__':
    unittest.main(verbosity=2)