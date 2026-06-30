/// Marketplace + meal product catalog. Ported from fitness-app.
library;

import 'domain_types.dart';


class MarketplaceProducts {
  MarketplaceProducts._();

  static List<MarketplaceProduct> all = [
    // APPAREL
    MarketplaceProduct(
      id: 'prod-apparel-1',
      name: 'Ultra-Flex DryFit Active Shirt',
      description:
          'Premium moisture-wicking and sweat-repelling stretch shirt designed for high-intensity training. Ergonomic flatlock seams prevent chafing.',
      price: 29.99,
      rating: 4.8,
      image:
          'https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=500&auto=format&fit=crop&q=80',
      category: 'apparel',
      badge: 'Best Seller',
    ),
    MarketplaceProduct(
      id: 'prod-apparel-2',
      name: 'AeroShield Lightweight Workout Hoodie',
      description:
          'Lightweight, breathable, and highly flexible knit fabric designed to regulate core temperatures during warmups and outdoor training sessions.',
      price: 49.99,
      rating: 4.7,
      image:
          'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500&auto=format&fit=crop&q=80',
      category: 'apparel',
    ),
    MarketplaceProduct(
      id: 'prod-apparel-3',
      name: 'Apex Compression Gym Shorts (7")',
      description:
          'Features built-in phone pocket and double-layer compressive liner for muscle support during deep barbell squats and dynamic runs.',
      price: 34.99,
      rating: 4.9,
      image:
          'https://images.unsplash.com/photo-1539185441755-769473a23570?w=500&auto=format&fit=crop&q=80',
      category: 'apparel',
      badge: 'Premium',
    ),
    MarketplaceProduct(
      id: 'prod-apparel-4',
      name: 'Apex Grip Athletic Cross-Trainers',
      description:
          'Flat-sole lightweight gym trainers designed specifically for squat stability, deadlift force transmission, and agility movements.',
      price: 119.99,
      rating: 4.8,
      image:
          'https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=500&auto=format&fit=crop&q=80',
      category: 'apparel',
      badge: 'Top Rated',
    ),
    // EQUIPMENT
    MarketplaceProduct(
      id: 'prod-equip-1',
      name: 'ProSeries Olympic Barbell (20kg)',
      description:
          'IWF-spec 220,000 PSI tensile steel barbell with dual knurl marks and bronze bushings for smooth sleeve rotation.',
      price: 249.99,
      rating: 4.9,
      image:
          'https://images.unsplash.com/photo-1534258936925-c58bed479fcb?w=500&auto=format&fit=crop&q=80',
      category: 'equipment',
      badge: 'Pro Grade',
    ),
    MarketplaceProduct(
      id: 'prod-equip-2',
      name: 'Adjustable Dumbbell Pair (5-52.5kg)',
      description:
          'Space-saving dial-adjustable dumbbell pair replacing 15 sets. Quick-select weight mechanism for fast drop-sets.',
      price: 499.99,
      rating: 4.7,
      image:
          'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&auto=format&fit=crop&q=80',
      category: 'equipment',
    ),
    MarketplaceProduct(
      id: 'prod-equip-3',
      name: 'Wearable Weighted Vest (20kg)',
      description:
          'Premium adjustable weighted vest with even weight distribution, breathable mesh, and reflective trim for outdoor training.',
      price: 79.99,
      rating: 4.6,
      image:
          'https://images.unsplash.com/photo-1593079831268-3381b0db4a77?w=500&auto=format&fit=crop&q=80',
      category: 'equipment',
    ),
    // SUPPLEMENTS
    MarketplaceProduct(
      id: 'prod-supp-1',
      name: 'Gold Whey Isolate (2kg, Chocolate)',
      description:
          '27g protein per scoop, 5.5g BCAAs, lactase-enzymated for easy digestion. Third-party lab-verified purity.',
      price: 59.99,
      rating: 4.9,
      image:
          'https://images.unsplash.com/photo-1620207418302-439b387441b0?w=500&auto=format&fit=crop&q=80',
      category: 'supplements',
      badge: 'Editor\'s Choice',
    ),
    MarketplaceProduct(
      id: 'prod-supp-2',
      name: 'Plant Performance Vegan Protein (1kg)',
      description:
          'Pea-rice-hemp protein blend with added B12 and iron. 24g protein per scoop, smooth texture, no grit.',
      price: 44.99,
      rating: 4.6,
      image:
          'https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=500&auto=format&fit=crop&q=80',
      category: 'supplements',
    ),
    MarketplaceProduct(
      id: 'prod-supp-3',
      name: 'Pre-Workout Ignition Matrix (300g)',
      description:
          '200mg caffeine, 6g citrulline malate, 2g beta-alanine, and L-tyrosine for clean sustained energy and pump.',
      price: 39.99,
      rating: 4.7,
      image:
          'https://images.unsplash.com/photo-1610725663727-08695a1ac3ff?w=500&auto=format&fit=crop&q=80',
      category: 'supplements',
    ),
    MarketplaceProduct(
      id: 'prod-supp-4',
      name: 'Omega-3 EPA/DHA Fish Oil (90 softgels)',
      description:
          'Ultra-pure molecularly-distilled fish oil with 800mg EPA + 400mg DHA per serving. Burp-free enteric coating.',
      price: 24.99,
      rating: 4.5,
      image:
          'https://images.unsplash.com/photo-1550572017-edd951b55104?w=500&auto=format&fit=crop&q=80',
      category: 'supplements',
    ),
    // ACCESSORIES
    MarketplaceProduct(
      id: 'prod-acc-1',
      name: 'PowerLift Leather Lifting Belt (10mm)',
      description:
          'Suede-lined genuine leather lifting belt with seamless steel roller buckle. IPF-approved for competition.',
      price: 89.99,
      rating: 4.9,
      image:
          'https://images.unsplash.com/photo-1576678927484-cc907957088c?w=500&auto=format&fit=crop&q=80',
      category: 'accessories',
      badge: 'IPF Approved',
    ),
    MarketplaceProduct(
      id: 'prod-acc-2',
      name: 'Wrist Wraps (24", Elastic Loop)',
      description:
          'Heavy-duty IPF-approved wrist wraps with thumb loop and velcro closure. Provides maximum wrist stability for heavy presses.',
      price: 24.99,
      rating: 4.7,
      image:
          'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=500&auto=format&fit=crop&q=80',
      category: 'accessories',
    ),
    MarketplaceProduct(
      id: 'prod-acc-3',
      name: 'Resistance Band Kit (5-Pack)',
      description:
          'Color-coded progressive resistance bands (5kg-25kg) with door anchor, handles, and carry bag for home training.',
      price: 34.99,
      rating: 4.5,
      image:
          'https://images.unsplash.com/photo-1583454152894-3ce0c1d1f1f7?w=500&auto=format&fit=crop&q=80',
      category: 'accessories',
    ),
  ];
}
