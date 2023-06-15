from django.core.management import BaseCommand

from core.constants import (DEFAULT_WASH_CATEGORIES,
                            DEFAULT_ITEMS,
                            DEFAULT_USER,
                            DEFAULT_ADDRESS,
                            DEFAULT_SHOP)
from core.models import WashCategory, Item, User, Address, Shop


class Command(BaseCommand):
    help = 'Populate default values in the database'

    def handle(self, *args, **options):
        # Write your code to populate default values here
        for name, extra_per_item in DEFAULT_WASH_CATEGORIES:
            obj, created = WashCategory.objects.update_or_create(
                name=name,
                defaults={'extra_per_item': extra_per_item}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'WashCategory updated: {name}'))

        for name, image, price in DEFAULT_ITEMS:
            obj, created = Item.objects.update_or_create(
                name=name,
                defaults={'image': image, 'price': price}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Item updated: {name}'))

        user = User.objects.create_user(**DEFAULT_USER)
        self.stdout.write(self.style.SUCCESS('Default user created'))

        address, created = Address.objects.update_or_create(user=user, defaults=DEFAULT_ADDRESS)
        self.stdout.write(self.style.SUCCESS('Default address created'))

        shop, created = Shop.objects.update_or_create(user=user, defaults=DEFAULT_SHOP)
        self.stdout.write(self.style.SUCCESS('Default shop created'))

        self.stdout.write(self.style.SUCCESS('Default values populated successfully'))
