import datetime

from django.test import TestCase, Client
from django.test.utils import setup_test_environment
from django.utils import timezone

from clubadm.models import Season, Member


setup_test_environment()

client = Client()


class SeasonMethodTests(TestCase):
    def get_future_date(self):
        time = timezone.now() + datetime.timedelta(days=1)
        return time.date()

    def get_past_date(self):
        time = timezone.now() - datetime.timedelta(days=1)
        return time.date()

    def get_present_date(self):
        return timezone.now().date()

    def test_is_closed(self):
        season = Season(ship_by=self.get_future_date())
        self.assertEqual(season.is_closed(), False)

        season = Season(ship_by=self.get_past_date())
        self.assertEqual(season.is_closed(), True)

        season = Season(ship_by=self.get_present_date())
        self.assertEqual(season.is_closed(), False)

    def test_is_participatable(self):
        season = Season(signups_start=self.get_future_date(),
                        signups_end=self.get_future_date())
        self.assertEqual(season.is_participatable(), False)

        season = Season(signups_start=self.get_future_date(),
                        signups_end=self.get_past_date())
        self.assertEqual(season.is_participatable(), False)

        season = Season(signups_start=self.get_future_date(),
                        signups_end=self.get_present_date())
        self.assertEqual(season.is_participatable(), False)

        season = Season(signups_start=self.get_past_date(),
                        signups_end=self.get_future_date())
        self.assertEqual(season.is_participatable(), True)

        season = Season(signups_start=self.get_past_date(),
                        signups_end=self.get_past_date())
        self.assertEqual(season.is_participatable(), False)

        season = Season(signups_start=self.get_past_date(),
                        signups_end=self.get_present_date())
        self.assertEqual(season.is_participatable(), False)

        season = Season(signups_start=self.get_present_date(),
                        signups_end=self.get_future_date())
        self.assertEqual(season.is_participatable(), True)

        season = Season(signups_start=self.get_present_date(),
                        signups_end=self.get_past_date())
        self.assertEqual(season.is_participatable(), False)

        season = Season(signups_start=self.get_present_date(),
                        signups_end=self.get_present_date())
        self.assertEqual(season.is_participatable(), False)


class MemberMethodTests(TestCase):
    def test_is_gift_sent(self):
        member = Member(gift_sent=None)
        self.assertEqual(member.is_gift_sent(), False)

        member = Member(gift_sent=timezone.now())
        self.assertEqual(member.is_gift_sent(), True)

    def test_is_gift_received(self):
        member = Member(gift_received=None)
        self.assertEqual(member.is_gift_received(), False)

        member = Member(gift_received=timezone.now())
        self.assertEqual(member.is_gift_received(), True)


class IndexViewTests(TestCase):
    def test_jsdata(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'var jsdata={')
        self.assertIsNotNone(response.context['jsdata'])


class OldProfileViewTests(TestCase):
    def test_adm2012(self):
        response = self.client.get(
            '/profile?id=1&hash=d5c768022c7a512815653d9ae541964b')
        self.assertRedirects(response, '/#/2012/profile')

    def test_adm2013(self):
        response = self.client.get('/profile')
        self.assertRedirects(response, '/#/2013/profile')

    def test_adm2014(self):
        response = self.client.get('/2014/profile')
        self.assertRedirects(response, '/#/2014/profile')
