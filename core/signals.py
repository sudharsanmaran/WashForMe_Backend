import logging

from django.dispatch import receiver, Signal

from .cron import delete_shop_timeslots, update_timeslots

logger = __import__("logging").getLogger(__name__)
logging.basicConfig(level=logging.INFO)

create_shop_timeslots_signal = Signal()
delete_shop_timeslots_signal = Signal()


@receiver(create_shop_timeslots_signal)
def handle_create_shop_timeslots_signal(sender, **kwargs):
    shop = kwargs.get('shop')
    update_timeslots(shop.id)
    logger.info(f'new timeslots are updated for {shop.name}')


@receiver(delete_shop_timeslots_signal)
def handle_delete_shop_timeslots_signal(sender, **kwargs):
    shop = kwargs.get('shop')
    delete_shop_timeslots(shop.id)
    logger.info(f'timeslots are deleted for {shop.name}')


payment_success_signal = Signal()


@receiver(payment_success_signal)
def handle_payment_success_signal(sender, **kwargs):
    logger.info(f'handle_payment_success_signal')
    pass
