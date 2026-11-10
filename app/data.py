from app.models import Product

_PRODUCT_LIST = [
    Product(
        id=1,
        name="Wireless Earbuds",
        description="Bluetooth 5.3 earbuds with active noise cancellation and 30-hour battery.",
        price_paise=249900,
        image_url="https://example.com/images/earbuds.jpg",
    ),
    Product(
        id=2,
        name="Mechanical Keyboard",
        description="Tenkeyless keyboard with hot-swappable switches and RGB backlight.",
        price_paise=499900,
        image_url="https://example.com/images/keyboard.jpg",
    ),
    Product(
        id=3,
        name="27-inch Monitor",
        description="1440p IPS monitor with 165Hz refresh rate.",
        price_paise=1599900,
        image_url="https://example.com/images/monitor.jpg",
    ),
    Product(
        id=4,
        name="USB-C Hub",
        description="7-in-1 hub with HDMI, SD card reader and 100W pass-through charging.",
        price_paise=179900,
        image_url="https://example.com/images/usb-hub.jpg",
    ),
    Product(
        id=5,
        name="Portable SSD 1TB",
        description="USB 3.2 portable SSD with read speeds up to 1050 MB/s.",
        price_paise=749900,
        image_url="https://example.com/images/ssd.jpg",
    ),
    Product(
        id=6,
        name="Smartwatch",
        description="AMOLED smartwatch with heart-rate tracking and GPS.",
        price_paise=599900,
        image_url="https://example.com/images/smartwatch.jpg",
    ),
    Product(
        id=7,
        name="Bluetooth Speaker",
        description="Waterproof portable speaker with 12-hour playtime.",
        price_paise=329900,
        image_url="https://example.com/images/speaker.jpg",
    ),
]

PRODUCTS: dict[int, Product] = {product.id: product for product in _PRODUCT_LIST}

#Product ID duplication fail fast concept
if len(PRODUCTS) != len(_PRODUCT_LIST):
    raise ValueError("Duplicate product IDs are found in the _PRODUCT_LIST")