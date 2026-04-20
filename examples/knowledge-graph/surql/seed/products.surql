-- Top-level categories
UPSERT category:electronics SET name = "Electronics", parent = NONE;
UPSERT category:clothing SET name = "Clothing", parent = NONE;
UPSERT category:sports SET name = "Sports & Outdoors", parent = NONE;
UPSERT category:home SET name = "Home & Garden", parent = NONE;

-- Electronics subcategories
UPSERT category:computers SET name = "Computers", parent = category:electronics;
UPSERT category:smartphones SET name = "Smartphones", parent = category:electronics;
UPSERT category:audio SET name = "Audio", parent = category:electronics;
UPSERT category:tv SET name = "TVs & Displays", parent = category:electronics;

-- Computers subcategories
UPSERT category:laptops SET name = "Laptops", parent = category:computers;
UPSERT category:desktops SET name = "Desktops", parent = category:computers;
UPSERT category:tablets SET name = "Tablets", parent = category:computers;

-- Audio subcategories
UPSERT category:headphones SET name = "Headphones", parent = category:audio;
UPSERT category:speakers SET name = "Speakers", parent = category:audio;

-- Clothing subcategories
UPSERT category:mens_clothing SET name = "Men's Clothing", parent = category:clothing;
UPSERT category:womens_clothing SET name = "Women's Clothing", parent = category:clothing;
UPSERT category:accessories SET name = "Accessories", parent = category:clothing;

-- Accessories subcategories
UPSERT category:hats SET name = "Hats & Caps", parent = category:accessories;
UPSERT category:bags SET name = "Bags & Backpacks", parent = category:accessories;

-- Sports subcategories
UPSERT category:team_sports SET name = "Team Sports", parent = category:sports;
UPSERT category:outdoor_gear SET name = "Outdoor Gear", parent = category:sports;
UPSERT category:fitness SET name = "Fitness Equipment", parent = category:sports;

-- Home subcategories
UPSERT category:furniture SET name = "Furniture", parent = category:home;
UPSERT category:kitchen SET name = "Kitchen", parent = category:home;
UPSERT category:garden SET name = "Garden", parent = category:home;

-- Products: Clothing > Accessories > Hats & Caps
UPSERT product:001 SET name = "SF Giants Cap", description = "Official San Francisco Giants fitted cap with embroidered logo", category = category:hats;
UPSERT product:002 SET name = "NY Yankees Cap", description = "Official New York Yankees adjustable snapback cap", category = category:hats;
UPSERT product:003 SET name = "LA Dodgers Cap", description = "Official Los Angeles Dodgers wool blend fitted cap", category = category:hats;

-- Products: Clothing > Men's
UPSERT product:004 SET name = "Classic Oxford Shirt", description = "Men's slim-fit button-down Oxford shirt in white cotton", category = category:mens_clothing;
UPSERT product:005 SET name = "Slim Chino Pants", description = "Men's slim-fit chino pants in khaki, stretch cotton blend", category = category:mens_clothing;
UPSERT product:006 SET name = "Merino Wool Sweater", description = "Men's crewneck merino wool sweater, machine washable", category = category:mens_clothing;

-- Products: Clothing > Women's
UPSERT product:007 SET name = "Linen Wrap Dress", description = "Women's relaxed linen wrap dress with tie waist", category = category:womens_clothing;
UPSERT product:008 SET name = "High-Waist Jeans", description = "Women's high-waist straight leg jeans in dark indigo", category = category:womens_clothing;

-- Products: Clothing > Accessories > Bags
UPSERT product:009 SET name = "Canvas Tote Bag", description = "Large durable canvas tote bag with interior zipper pocket", category = category:bags;
UPSERT product:010 SET name = "Leather Backpack", description = "Genuine leather laptop backpack with padded 15\" sleeve", category = category:bags;

-- Products: Electronics > Computers > Laptops
UPSERT product:011 SET name = "UltraBook Pro 14", description = "14-inch ultrabook with Intel Core i7, 16GB RAM, 512GB SSD", category = category:laptops;
UPSERT product:012 SET name = "Developer Workstation Laptop", description = "15.6-inch laptop with AMD Ryzen 9, 32GB RAM, 1TB NVMe SSD", category = category:laptops;

-- Products: Electronics > Computers > Tablets
UPSERT product:013 SET name = "SlateTab 10", description = "10-inch Android tablet with AMOLED display and stylus support", category = category:tablets;
UPSERT product:014 SET name = "SlateTab Pro 12", description = "12.9-inch tablet with detachable keyboard and USB-C hub", category = category:tablets;

-- Products: Electronics > Smartphones
UPSERT product:015 SET name = "Nova X12", description = "Flagship smartphone with 6.7-inch OLED display and triple camera system", category = category:smartphones;
UPSERT product:016 SET name = "Nova X12 Mini", description = "Compact flagship smartphone with 5.4-inch OLED display", category = category:smartphones;

-- Products: Electronics > Audio > Headphones
UPSERT product:017 SET name = "StudioSound ANC", description = "Over-ear headphones with active noise cancellation and 30-hour battery", category = category:headphones;
UPSERT product:018 SET name = "SportBuds Pro", description = "True wireless earbuds with IPX5 water resistance and ear hooks", category = category:headphones;

-- Products: Electronics > Audio > Speakers
UPSERT product:019 SET name = "BoomBox Portable", description = "Portable Bluetooth speaker with 360-degree sound and 12-hour battery", category = category:speakers;
UPSERT product:020 SET name = "HomeSound Tower", description = "Floor-standing smart speaker with built-in voice assistant", category = category:speakers;

-- Products: Electronics > TVs
UPSERT product:021 SET name = "Vista 55 QLED", description = "55-inch QLED 4K TV with 120Hz refresh rate and HDR10+", category = category:tv;
UPSERT product:022 SET name = "Vista 75 OLED", description = "75-inch OLED 4K TV with Dolby Vision and 144Hz gaming mode", category = category:tv;

-- Products: Sports > Team Sports
UPSERT product:023 SET name = "Pro Basketball", description = "Official size and weight indoor/outdoor basketball, composite leather", category = category:team_sports;
UPSERT product:024 SET name = "Soccer Training Set", description = "5-piece soccer training set with cones, ball, and pump", category = category:team_sports;

-- Products: Sports > Fitness Equipment
UPSERT product:025 SET name = "Adjustable Dumbbell Set", description = "Pair of adjustable dumbbells ranging from 5 to 52.5 lbs each", category = category:fitness;
UPSERT product:026 SET name = "Yoga Mat Pro", description = "6mm thick non-slip yoga mat with carrying strap, eco-friendly TPE", category = category:fitness;
UPSERT product:027 SET name = "Resistance Band Kit", description = "Set of 5 resistance bands with varying tension levels and door anchor", category = category:fitness;

-- Products: Sports > Outdoor Gear
UPSERT product:028 SET name = "Trail Hiking Boots", description = "Waterproof mid-cut hiking boots with Vibram outsole", category = category:outdoor_gear;
UPSERT product:029 SET name = "Camping Tent 4-Person", description = "Freestanding 4-person dome tent with double-wall design and rainfly", category = category:outdoor_gear;

-- Products: Home > Kitchen
UPSERT product:030 SET name = "Chef's Knife 8-inch", description = "High-carbon German steel chef's knife with ergonomic handle", category = category:kitchen;
UPSERT product:031 SET name = "Cast Iron Skillet 12-inch", description = "Pre-seasoned cast iron skillet, oven safe to 500F", category = category:kitchen;
UPSERT product:032 SET name = "Espresso Machine", description = "15-bar pump espresso machine with steam wand and cup warmer", category = category:kitchen;

-- Products: Home > Garden
UPSERT product:033 SET name = "Garden Tool Set", description = "5-piece stainless steel garden tool set with ergonomic grips", category = category:garden;
UPSERT product:034 SET name = "Raised Garden Bed Kit", description = "Cedar raised garden bed kit, 4x8 ft, easy assembly", category = category:garden;

-- Products: Home > Furniture
UPSERT product:035 SET name = "Ergonomic Office Chair", description = "Fully adjustable ergonomic office chair with lumbar support and armrests", category = category:furniture;
UPSERT product:036 SET name = "Standing Desk Converter", description = "Height-adjustable standing desk converter with dual monitor support", category = category:furniture;

-- =============================================================================
-- Users

UPSERT user:alice SET name = "Alice Chen", email = "alice.chen@example.com";
UPSERT user:bob SET name = "Bob Martinez", email = "bob.martinez@example.com";
UPSERT user:carol SET name = "Carol Johnson", email = "carol.johnson@example.com";
UPSERT user:dave SET name = "Dave Kim", email = "dave.kim@example.com";
UPSERT user:eve SET name = "Eve Patel", email = "eve.patel@example.com";

-- =============================================================================
-- Orders

-- Alice: bought a laptop and headphones
UPSERT order:o001 SET user = user:alice, created_at = d"2025-11-03T09:14:00Z";
RELATE product:011 -> REL_PRODUCT_IN_ORDER -> order:o001 SET qty = 1;
RELATE product:017 -> REL_PRODUCT_IN_ORDER -> order:o001 SET qty = 1;

-- Alice: follow-up order for accessories
UPSERT order:o002 SET user = user:alice, created_at = d"2025-12-18T14:32:00Z";
RELATE product:009 -> REL_PRODUCT_IN_ORDER -> order:o002 SET qty = 2;
RELATE product:002 -> REL_PRODUCT_IN_ORDER -> order:o002 SET qty = 1;

-- Bob: home office setup
UPSERT order:o003 SET user = user:bob, created_at = d"2025-10-07T11:05:00Z";
RELATE product:035 -> REL_PRODUCT_IN_ORDER -> order:o003 SET qty = 1;
RELATE product:036 -> REL_PRODUCT_IN_ORDER -> order:o003 SET qty = 1;
RELATE product:012 -> REL_PRODUCT_IN_ORDER -> order:o003 SET qty = 1;
RELATE product:026 -> REL_PRODUCT_IN_ORDER -> order:o003 SET qty = 1;

-- Bob: kitchen splurge
UPSERT order:o004 SET user = user:bob, created_at = d"2026-01-22T16:48:00Z";
RELATE product:030 -> REL_PRODUCT_IN_ORDER -> order:o004 SET qty = 1;
RELATE product:031 -> REL_PRODUCT_IN_ORDER -> order:o004 SET qty = 1;
RELATE product:032 -> REL_PRODUCT_IN_ORDER -> order:o004 SET qty = 1;

-- Carol: sports & fitness haul
UPSERT order:o005 SET user = user:carol, created_at = d"2025-09-15T08:20:00Z";
RELATE product:025 -> REL_PRODUCT_IN_ORDER -> order:o005 SET qty = 1;
RELATE product:026 -> REL_PRODUCT_IN_ORDER -> order:o005 SET qty = 2;
RELATE product:027 -> REL_PRODUCT_IN_ORDER -> order:o005 SET qty = 1;

-- Carol: outdoor adventure gear
UPSERT order:o006 SET user = user:carol, created_at = d"2026-02-10T10:00:00Z";
RELATE product:028 -> REL_PRODUCT_IN_ORDER -> order:o006 SET qty = 1;
RELATE product:029 -> REL_PRODUCT_IN_ORDER -> order:o006 SET qty = 1;

-- Dave: baseball fan order
UPSERT order:o007 SET user = user:dave, created_at = d"2025-08-04T13:55:00Z";
RELATE product:001 -> REL_PRODUCT_IN_ORDER -> order:o007 SET qty = 1;
RELATE product:003 -> REL_PRODUCT_IN_ORDER -> order:o007 SET qty = 1;

-- Dave: electronics upgrade
UPSERT order:o008 SET user = user:dave, created_at = d"2025-11-29T19:30:00Z";
RELATE product:015 -> REL_PRODUCT_IN_ORDER -> order:o008 SET qty = 1;
RELATE product:021 -> REL_PRODUCT_IN_ORDER -> order:o008 SET qty = 1;
RELATE product:019 -> REL_PRODUCT_IN_ORDER -> order:o008 SET qty = 1;

-- Eve: wardrobe refresh
UPSERT order:o009 SET user = user:eve, created_at = d"2026-01-05T12:10:00Z";
RELATE product:007 -> REL_PRODUCT_IN_ORDER -> order:o009 SET qty = 2;
RELATE product:008 -> REL_PRODUCT_IN_ORDER -> order:o009 SET qty = 1;
RELATE product:010 -> REL_PRODUCT_IN_ORDER -> order:o009 SET qty = 1;

-- Eve: garden project
UPSERT order:o010 SET user = user:eve, created_at = d"2026-03-20T09:45:00Z";
RELATE product:033 -> REL_PRODUCT_IN_ORDER -> order:o010 SET qty = 1;
RELATE product:034 -> REL_PRODUCT_IN_ORDER -> order:o010 SET qty = 2;
RELATE product:009 -> REL_PRODUCT_IN_ORDER -> order:o010 SET qty = 1;
