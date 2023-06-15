from datetime import time
from enum import Enum

""""ENUMS"""


class BookingType(Enum):
    PICK_UP = 'pickup'
    DELIVERY = 'delivery'


class PaymentSource(Enum):
    CARD = 'card'
    BANK_TRANSACTION = 'bank_transaction'
    UPI = 'upi'


class PaymentStatus(Enum):
    FAILED = 'failed'
    PENDING = 'pending'
    SUCCESS = 'success'


class OrderStatus(Enum):
    PAYMENT_PENDING = 'payment_pending'
    PLACED = 'placed'
    PICKED = 'picked'
    DELIVERED = 'delivered'


"""configs"""
TIMESLOTS_DAYS = 7

"""messages"""

"""default db values"""
# (name, extra_amount)
DEFAULT_WASH_CATEGORIES = [
    ('Rinse wash', 0),
    ('Resin wash', 0),
    ('Softener Silicon wash', 3),
    ('Normal wash', 0),
    ('Bleaching wash', 2),
    ('Acid wash', 5),
    ('Towel bleach wash', 1),
]

# (name, url, amount)
DEFAULT_ITEMS = [
    ('Shirt', 'media/shirt.png', 10),
    ('T-shirt', 'media/football-shirt.png', 10),
    ('Sweater', 'media/coat.png', 17),
    ('Jacket', 'media/denim-jacket.png', 17),
    ('Hoodie', 'media/hoodie.png', 17),
    ('Pant', 'media/pants.png', 14),
    ('Jeans', 'media/jeans.png', 15),
    ('Normal Saree', 'media/saree.png', 25),
    ('Skirt', 'media/skirt.png', 15),
    ('Bra', 'media/bra.png', 5),
    ('Shorts', 'media/shorts.png', 8),
    ('Cap', 'media/baseball-cap.png', 3),
    ('Gloves', 'media/glove.png', 6),
    ('Socks', 'media/socks.png', 5),
    ('Gym clothes', 'media/clothes.png', 30),
    ('Shoes', 'media/shoe.png', 20),
    ('Duppatta', 'media/blanket.png', 35),
    ('Dress', 'media/dress.png', 20),
    ('Towel', 'media/towel.png', 15),
    ('Plain Kurta', 'media/kurta.png', 10),
    ('Blouse', 'media/blouse.png', 9),
    ('Pajamas', 'media/pajamas.png', 10),
    ('Printed / Designer Saree', 'media/saree.png', 28),
    ('Saree', 'media/saree.png', 28),
    ('Printed/Designer Gown', 'media/gown.png', 45),
    ('Suit / Blazzer', 'media/suit.png', 27),
    ('Sherwani/ Designed Sherwani', 'media/shervani.png', 100),
    ('Anarkali', 'media/woman-clothes.png', 27),
    ('Designer Skirt', 'media/clothes.png', 27),
    ('Silk Vesti', 'media/dhoti.png', 27),
    ('Normal Vesti', 'media/dhoti.png', 17),
    ('Set of Pillow Covers (2)', 'media/pillows.png', 10),
    ('Normal Skirt', 'media/clothes.png', 17),
    ('Bedsheet', 'media/blanket.png', 20),
    ('kid T-shirt', 'media/baby-clothes.png', 7),
    ('Kid Pant', 'media/tshirt.png', 7),
    ('kid Skirt', 'media/girl-cloth.png', 7),
    ('Carpet', 'media/adornment.png', 30),
    ('Mat', 'media/adornment.png', 25),
    ('Waist Coat', 'media/summer.png', 20),
]

DEFAULT_USER = {
    'phone': '+919999999999',
    'password': 'admin',
    'first_name': 'John',
    'last_name': 'Doe',
    'email': 'john.doe@example.com',
    'is_phone_verified': True,
    'is_staff': True,
    'is_superuser': True,
    'other_details': {'availability': 'Yes', 'notifications': 'On', 'language': 'English', 'dark_mode': 'No'},
}

DEFAULT_ADDRESS = {
    'address_line_1': '123 Main Street',
    'address_line_2': '',
    'city': 'Chennai',
    'country': 'India',
    'pincode': 123456,
    'type': 'Home',
}

DEFAULT_SHOP = {
    'name': 'My Shop',
    'opening_time': time(10, 0),
    'closing_time': time(19, 0),
    'active': True,
    'max_user_limit_per_time_slot': 10,
}
