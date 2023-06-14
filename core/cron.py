import time
from datetime import timedelta, datetime, date

from django.utils.timezone import make_aware

from core.constans import TIMESLOTS_DAYS
from core.models import Shop, Timeslot


def generate_timeslots(opening_time: time, closing_time: time, timeslot_duration: timedelta, start_date: date):
    timeslots = []
    current_date = start_date
    current_datetime = datetime.combine(current_date, opening_time)

    for _ in range(TIMESLOTS_DAYS):
        while current_datetime.time() < closing_time:
            end_datetime = current_datetime + timeslot_duration

            if end_datetime.time() > closing_time:
                break

            timeslots.append((current_datetime, end_datetime))
            current_datetime = end_datetime

        current_date += timedelta(days=1)
        current_datetime = datetime.combine(current_date, opening_time)

    return timeslots


def delete_shop_timeslots(shop_id: int) -> None:
    Timeslot.objects.filter(shop_id=shop_id).delete()


def delete_older_time_slots():
    pass


def generate_unique_id(int_timestamp: int, shop_id: int) -> int:
    return int(str(int_timestamp) + str(shop_id))


def update_timeslots(shop_id: int = None):
    if shop_id:
        shops = Shop.objects.filter(pk=shop_id)
    else:
        shops = Shop.objects.all()
    for shop in shops:
        timeslots = generate_timeslots(shop.opening_time, shop.closing_time, shop.time_slot_duration,
                                       datetime.now().date())
        # generate unique id based on start datetime to ignore conflicts
        timeslots_objects = [Timeslot(
            id=generate_unique_id(int(time.mktime(timeslot[0].timetuple())), shop.id),
            start_datetime=make_aware(timeslot[0]),
            end_datetime=make_aware(timeslot[1]),
            pickup_available_quota=shop.max_user_limit_per_time_slot,
            delivery_available_quota=shop.max_user_limit_per_time_slot,
            shop=shop
        ) for timeslot in timeslots]

        Timeslot.objects.bulk_create(timeslots_objects, ignore_conflicts=True, unique_fields=['id'])
    return
