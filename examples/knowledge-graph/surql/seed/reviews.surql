-- Alice reviews the UltraBook Pro 14 she bought in order o001
UPSERT review:r001 SET
    text = "I've been using this laptop for three months now and it's been fantastic. The battery life easily gets me through a full workday, and the i7 handles everything I throw at it — video editing, running Docker containers, you name it. Thin and light enough to carry everywhere. Only minor gripe is the webcam could be sharper.",
    score = 4.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:alice,
    product = product:011;

-- Bob reviews the Espresso Machine from his kitchen splurge in order o004
UPSERT review:r002 SET
    text = "This machine has replaced my morning café run entirely. The 15-bar pump produces a rich, properly extracted shot and the steam wand gives me decent microfoam for lattes. Takes about 25 minutes to heat up fully which is a bit annoying, and the drip tray fills up faster than I'd like. Overall a solid mid-range machine.",
    score = 4.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:bob,
    product = product:032;

-- Carol reviews the Trail Hiking Boots from her outdoor order o006
UPSERT review:r003 SET
    text = "Wore these on a two-day backcountry trip and came back with blisters on both heels. The Vibram outsole grips rocks brilliantly and they kept my feet dry through a stream crossing, but the break-in period is brutal — at least 20+ miles before they soften up. Probably worth it long term but I wish the listing warned about that.",
    score = 3.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:carol,
    product = product:028;

-- Dave reviews the SF Giants Cap from order o007
UPSERT review:r004 SET
    text = "Perfect fit and the embroidery is sharp and clean. Wore it to three games this season and it still looks brand new. Sizing runs true — I'm a 7 3/8 and ordered accordingly with no issues.",
    score = 5.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:dave,
    product = product:001;

-- Alice reviews the NY Yankees Cap from order o002
UPSERT review:r005 SET
    text = "The snapback closure is convenient but feels a bit plasticky compared to fitted caps. Logo stitching is solid and the colorway is accurate to what's shown. Adjusts well across different head sizes. Nothing exceptional but does the job.",
    score = 3.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:alice,
    product = product:002;

-- Dave reviews the LA Dodgers Cap from order o007
UPSERT review:r006 SET
    text = "The wool blend gives it a premium feel you don't get with cheaper caps. It holds its shape really well and the fitted sizing is spot on. My only complaint is it can get warm on sunny days — this isn't a summer cap.",
    score = 4.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:dave,
    product = product:003;

-- Bob reviews the Classic Oxford Shirt
UPSERT review:r007 SET
    text = "Bought this for work and have washed it a dozen times with zero shrinkage or fading. The slim fit is genuinely slim — size up if you're between sizes. Collar holds its shape without a collar stay which is impressive at this price point.",
    score = 4.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:bob,
    product = product:004;

-- Eve reviews the Slim Chino Pants
UPSERT review:r008 SET
    text = "Bought these for my partner and the sizing is wildly inconsistent with the chart. The listed waist came out nearly an inch smaller than advertised. The fabric itself is nice and the stretch is helpful, but we had to exchange twice before getting the right fit. Frustrating process.",
    score = 2.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:eve,
    product = product:005;

-- Alice reviews the Merino Wool Sweater
UPSERT review:r009 SET
    text = "Machine washable merino that actually survives the machine wash — I was skeptical but after five cold cycles it hasn't pilled or warped at all. Soft against the skin with no itch whatsoever. Runs slightly long in the torso which I actually prefer.",
    score = 5.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:alice,
    product = product:006;

-- Eve reviews the Linen Wrap Dress from order o009
UPSERT review:r010 SET
    text = "This dress is exactly what summer dressing should be. The linen is lightweight and breathable, the wrap silhouette is flattering on multiple body types, and the tie actually stays put throughout the day. Ordered two in different colors.",
    score = 5.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:eve,
    product = product:007;

-- Eve reviews the High-Waist Jeans from order o009
UPSERT review:r011 SET
    text = "The dark indigo is rich and doesn't bleed in the wash. Straight leg hits perfectly at the ankle for my 5'6\" frame. The high waist is genuinely high — sits well above the navel. Denim is a bit stiff out of the box but softens nicely after a few wears.",
    score = 4.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:eve,
    product = product:008;

-- Alice reviews the Canvas Tote Bag from order o002
UPSERT review:r012 SET
    text = "I use this as a daily carry and it holds everything — laptop, gym clothes, lunch, groceries. The interior zipper pocket is a lifesaver for keys and cards. Handles are reinforced and show no signs of wear after months of heavy use. The canvas has a slight stiffness that I actually like.",
    score = 4.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:alice,
    product = product:009;

-- Eve reviews the Leather Backpack from order o009
UPSERT review:r013 SET
    text = "Genuinely beautiful bag that gets better with age. The leather has developed a lovely patina over a few months of daily use. The padded laptop sleeve fits my 14-inch MacBook snugly. Only downside is it's heavy before you put anything in it — definitely a style-over-weight-savings choice.",
    score = 4.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:eve,
    product = product:010;

-- Bob reviews the Developer Workstation Laptop from order o003
UPSERT review:r014 SET
    text = "This machine is an absolute beast. Running Kubernetes clusters locally, compiling large codebases, running multiple VMs — it handles everything without breaking a sweat. The Ryzen 9 paired with 32GB RAM means I never hit a ceiling. Fan noise under heavy load is noticeable but tolerable. Battery life is average at best, but with a workstation chip that's expected.",
    score = 4.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:bob,
    product = product:012;

-- Carol reviews the StudioSound ANC Headphones
UPSERT review:r015 SET
    text = "The ANC is genuinely impressive — kills HVAC hum and open office chatter completely. Sound signature leans warm which I enjoy for long listening sessions. 30-hour battery claim holds up in real use; I charge about once a week. Clamping force is a touch high straight out of the box but eases after a week of use.",
    score = 4.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:carol,
    product = product:017;

-- Dave reviews the BoomBox Portable from order o008
UPSERT review:r016 SET
    text = "Brought this to a beach day and it was the hit of the group. The 360-degree sound claim is accurate — no matter where you're sitting relative to the speaker it sounds full. Twelve hours of battery is conservative; I got closer to 14 at moderate volume. Pairs instantly and the connection holds at a solid distance.",
    score = 5.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:dave,
    product = product:019;

-- Dave reviews the Vista 55 QLED from order o008
UPSERT review:r017 SET
    text = "Picture quality is stunning — QLED panels at this size are hard to beat for the price. HDR10+ content looks spectacular and the 120Hz mode makes gaming incredibly smooth. The smart TV interface is sluggish and the built-in apps feel like an afterthought, but I use an external device anyway so it barely matters.",
    score = 4.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:dave,
    product = product:021;

-- Carol reviews the Adjustable Dumbbell Set from order o005
UPSERT review:r018 SET
    text = "Replaced an entire rack of fixed dumbbells with this one set. The adjustment mechanism is smooth and locks in solidly — no rattling mid-rep. The weight increments are fine enough for progressive overload. Footprint is tiny compared to traditional sets. Worth every penny for a home gym.",
    score = 5.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:carol,
    product = product:025;

-- Carol reviews the Yoga Mat Pro from order o005
UPSERT review:r019 SET
    text = "Non-slip is not an exaggeration — this mat grips the floor and my hands equally well even in sweaty hot yoga sessions. The 6mm thickness is the sweet spot between cushioning and stability for balance poses. TPE material doesn't have the chemical smell that cheaper PVC mats have. The carrying strap is a bit flimsy but functional.",
    score = 4.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:carol,
    product = product:026;

-- Carol reviews the Resistance Band Kit from order o005
UPSERT review:r020 SET
    text = "Bands themselves are solid and the tension levels are well-spaced for progressive training. The door anchor snapped on the second use which was frustrating. Replacement was easy to source but it shouldn't have failed that quickly. If you can overlook the cheap anchor hardware the actual bands are worth it.",
    score = 3.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:carol,
    product = product:027;

-- Bob reviews the Chef's Knife from order o004
UPSERT review:r021 SET
    text = "Sharpest knife I've ever pulled out of the box. Held its edge through months of daily prep before needing a hone. The ergonomic handle is well-balanced — no wrist fatigue even after long sessions. German steel sharpens easily compared to harder Japanese steels. An outstanding workhorse knife.",
    score = 5.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:bob,
    product = product:030;

-- Bob reviews the Cast Iron Skillet from order o004
UPSERT review:r022 SET
    text = "Pre-seasoning is decent but I added two more layers before serious use — standard practice with cast iron. Now it's nearly non-stick and sears a steak better than anything else I own. Oven safe claim is solid; I've pushed it to 475F with no issues. Heavy, obviously, but that's cast iron. A kitchen essential.",
    score = 5.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:bob,
    product = product:031;

-- Bob reviews the Yoga Mat Pro from order o003
UPSERT review:r024 SET
    text = "I bought this primarily for stretching and cool-down after lifting sessions rather than yoga proper. It does that job perfectly — thick enough that kneeling on a hard floor is comfortable, and it doesn't slide even on polished concrete. Rolled up it's compact enough to slip under my desk. No complaints whatsoever.",
    score = 5.0,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:bob,
    product = product:026;

-- Bob reviews the Ergonomic Office Chair from order o003
UPSERT review:r023 SET
    text = "My back pain after long coding sessions is basically gone since switching to this chair. The lumbar support is adjustable enough to dial in exactly where you need it. Armrests move in four directions which sounds like a gimmick but makes a real difference. Assembly took about 45 minutes alone — doable but a second pair of hands helps.",
    score = 4.5,
    sentiment = NONE,
    flow_sentiment = NONE,
    user = user:bob,
    product = product:035;
