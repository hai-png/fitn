/// Marketplace tab — fitness product store matching FitLife Hub design.
///
/// Features:
/// - Category filter chips (All / Apparel / Equipment / Supplements / Accessories).
/// - Search bar.
/// - Sort dropdown (Default / Price asc / Price desc / Rating).
/// - Product cards with image, name, price, rating, add-to-cart.
/// - Cart drawer with quantity controls + checkout.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../data/catalog.dart';
import '../../data/domain_types.dart';
import '../../state/app_state.dart';
import '../../ui/theme/fitn_design.dart';

class MarketplaceTab extends ConsumerStatefulWidget {
  const MarketplaceTab({super.key});

  @override
  ConsumerState<MarketplaceTab> createState() => _MarketplaceTabState();
}

class _MarketplaceTabState extends ConsumerState<MarketplaceTab> {
  String _selectedCategory = 'all';
  String _searchQuery = '';
  String _sortBy = 'default';
  bool _isCartOpen = false;
  bool _isCheckoutOpen = false;
  bool _isProcessing = false;
  bool _isOrderSuccess = false;
  final _addressCtrl = TextEditingController();
  final _cardCtrl = TextEditingController();

  List<MarketplaceProduct> get _filtered {
    var list = MarketplaceProducts.all.where((p) {
      final matchesCat = _selectedCategory == 'all' || p.category == _selectedCategory;
      final matchesSearch = _searchQuery.isEmpty ||
          p.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          p.description.toLowerCase().contains(_searchQuery.toLowerCase());
      return matchesCat && matchesSearch;
    }).toList();
    list.sort((a, b) {
      if (_sortBy == 'price-asc') return a.price.compareTo(b.price);
      if (_sortBy == 'price-desc') return b.price.compareTo(a.price);
      if (_sortBy == 'rating') return b.rating.compareTo(a.rating);
      return 0;
    });
    return list;
  }

  void _add(MarketplaceProduct p) {
    ref.read(appNotifierProvider.notifier).addToCart(CartItem(
          id: p.id,
          name: p.name,
          price: p.price,
          image: p.image,
          quantity: 1,
          type: 'marketplace',
        ));
  }

  void _checkout() {
    final appState = ref.read(appNotifierProvider).valueOrNull;
    final cart = appState?.cart.where((c) => c.type == 'marketplace').toList() ?? const [];
    if (cart.isEmpty) return;
    setState(() {
      _isCartOpen = false;
      _isCheckoutOpen = true;
    });
  }

  void _placeOrder() {
    if (_addressCtrl.text.trim().isEmpty || _cardCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please complete delivery address and card details.')),
      );
      return;
    }
    setState(() => _isProcessing = true);
    Future.delayed(const Duration(seconds: 2), () {
      final appState = ref.read(appNotifierProvider).valueOrNull;
      final cart = appState?.cart.where((c) => c.type == 'marketplace').toList() ?? const [];
      final total = cart.fold(0.0, (s, c) => s + c.price * c.quantity);
      final order = Order(
        id: 'mkt-${DateTime.now().millisecondsSinceEpoch}',
        items: cart,
        total: total,
        date: DateTime.now().toIso8601String().split('T')[0],
        status: 'processing',
        deliveryAddress: _addressCtrl.text,
      );
      ref.read(appNotifierProvider.notifier).checkout(order);
      setState(() {
        _isProcessing = false;
        _isOrderSuccess = true;
      });
      Future.delayed(const Duration(milliseconds: 3200), () {
        if (mounted) {
          setState(() {
            _isOrderSuccess = false;
            _isCheckoutOpen = false;
            _addressCtrl.clear();
            _cardCtrl.clear();
          });
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final cartCount = appState?.cart
            .where((c) => c.type == 'marketplace')
            .fold(0, (s, c) => s + c.quantity) ??
        0;
    final cartTotal = appState?.cart
            .where((c) => c.type == 'marketplace')
            .fold(0.0, (s, c) => s + c.price * c.quantity) ??
        0.0;

    return Scaffold(
      backgroundColor: FitnColors.cream,
      body: SafeArea(
        child: Stack(
          children: [
            ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
              children: [
                // Title.
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          FitnSectionLabel('04 — Performance Marketplace'),
                          Text('Curated Gear & Supplements',
                              style: FitnText.headline.copyWith(fontSize: 28)),
                        ],
                      ),
                    ),
                    GestureDetector(
                      onTap: () => setState(() => _isCartOpen = true),
                      child: Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: FitnColors.ink,
                          shape: BoxShape.circle,
                        ),
                        child: Stack(
                          children: [
                            Icon(LucideIcons.shoppingBag,
                                size: 18, color: Colors.white),
                            if (cartCount > 0)
                              Positioned(
                                right: -4,
                                top: -4,
                                child: Container(
                                  padding: const EdgeInsets.all(3),
                                  decoration: const BoxDecoration(
                                    color: FitnColors.accent,
                                    shape: BoxShape.circle,
                                  ),
                                  child: Text('$cartCount',
                                      style: GoogleFonts.inter(
                                          fontSize: 8,
                                          fontWeight: FontWeight.w700,
                                          color: Colors.white)),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                // Search.
                TextField(
                  decoration: InputDecoration(
                    hintText: 'Search products...',
                    prefixIcon: Icon(LucideIcons.search, size: 16),
                    isDense: true,
                  ),
                  onChanged: (v) => setState(() => _searchQuery = v),
                ),
                const SizedBox(height: 12),
                // Category chips + sort.
                Row(
                  children: [
                    Expanded(
                      child: SizedBox(
                        height: 36,
                        child: ListView(
                          scrollDirection: Axis.horizontal,
                          children: [
                            'all',
                            'apparel',
                            'equipment',
                            'supplements',
                            'accessories'
                          ].map((c) {
                            final selected = _selectedCategory == c;
                            return Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: GestureDetector(
                                onTap: () =>
                                    setState(() => _selectedCategory = c),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 12, vertical: 8),
                                  decoration: BoxDecoration(
                                    color: selected
                                        ? FitnColors.ink
                                        : Colors.white,
                                    border: Border.all(
                                        color: selected
                                            ? FitnColors.ink
                                            : FitnColors.ink10,
                                        width: 1),
                                  ),
                                  child: Text(
                                    c.toUpperCase(),
                                    style: GoogleFonts.inter(
                                        fontSize: 9,
                                        fontWeight: FontWeight.w700,
                                        letterSpacing: 1.0,
                                        color: selected
                                            ? Colors.white
                                            : FitnColors.ink60),
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding:
                          const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        border: Border.all(color: FitnColors.ink15, width: 1),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: _sortBy,
                          style: GoogleFonts.inter(
                              fontSize: 10, color: FitnColors.ink),
                          items: const [
                            DropdownMenuItem(
                                value: 'default', child: Text('Sort: Default')),
                            DropdownMenuItem(
                                value: 'price-asc',
                                child: Text('Price: Low → High')),
                            DropdownMenuItem(
                                value: 'price-desc',
                                child: Text('Price: High → Low')),
                            DropdownMenuItem(
                                value: 'rating', child: Text('Top Rated')),
                          ],
                          onChanged: (v) =>
                              setState(() => _sortBy = v ?? 'default'),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                // Products grid.
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 0.62,
                  ),
                  itemCount: _filtered.length,
                  itemBuilder: (context, idx) {
                    final p = _filtered[idx];
                    return _ProductCard(
                      product: p,
                      onAdd: () {
                        _add(p);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                              content: Text('${p.name} added to cart'),
                              duration: const Duration(seconds: 1)),
                        );
                      },
                    );
                  },
                ),
              ],
            ),
            if (_isCartOpen) _buildCartDrawer(cartTotal),
            if (_isCheckoutOpen) _buildCheckoutModal(cartTotal),
            if (_isOrderSuccess) _buildSuccessOverlay(),
          ],
        ),
      ),
    );
  }

  Widget _buildCartDrawer(double total) {
    final appState = ref.watch(appNotifierProvider).valueOrNull;
    final cart = appState?.cart.where((c) => c.type == 'marketplace').toList() ?? const [];
    return Container(
      color: Colors.black54,
      child: Align(
        alignment: Alignment.centerRight,
        child: Container(
          width: 320,
          margin: const EdgeInsets.only(left: 80),
          color: FitnColors.cream,
          child: SafeArea(
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: FitnColors.ink,
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('YOUR CART',
                          style: GoogleFonts.inter(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.4,
                              color: Colors.white)),
                      IconButton(
                        icon: Icon(LucideIcons.x, size: 16, color: Colors.white),
                        onPressed: () => setState(() => _isCartOpen = false),
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: cart.isEmpty
                      ? Center(
                          child: Text('Cart is empty',
                              style: FitnText.serifItalic),
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.all(12),
                          itemCount: cart.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 8),
                          itemBuilder: (context, idx) {
                            final c = cart[idx];
                            return Container(
                              padding: const EdgeInsets.all(8),
                              color: Colors.white,
                              child: Row(
                                children: [
                                  ClipRRect(
                                    child: Image.network(c.image,
                                        width: 48, height: 48, fit: BoxFit.cover,
                                        errorBuilder: (_, __, ___) => Container(
                                            width: 48,
                                            height: 48,
                                            color: FitnColors.ink05,
                                            child: Icon(LucideIcons.package,
                                                size: 18))),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(c.name,
                                            maxLines: 2,
                                            overflow: TextOverflow.ellipsis,
                                            style: GoogleFonts.inter(
                                                fontSize: 10,
                                                fontWeight: FontWeight.w700)),
                                        Text('\$${c.price.toStringAsFixed(2)}',
                                            style: FitnText.mono.copyWith(
                                                fontSize: 10,
                                                color: FitnColors.accent)),
                                      ],
                                    ),
                                  ),
                                  Column(
                                    children: [
                                      InkWell(
                                        onTap: () => ref
                                            .read(appNotifierProvider.notifier)
                                            .updateCartQty(c.id, c.quantity + 1),
                                        child: Icon(LucideIcons.plus,
                                            size: 12, color: FitnColors.ink),
                                      ),
                                      Padding(
                                        padding: const EdgeInsets.symmetric(
                                            vertical: 4),
                                        child: Text('${c.quantity}',
                                            style: FitnText.mono.copyWith(
                                                fontSize: 11,
                                                fontWeight: FontWeight.w700)),
                                      ),
                                      InkWell(
                                        onTap: () => ref
                                            .read(appNotifierProvider.notifier)
                                            .updateCartQty(c.id, c.quantity - 1),
                                        child: Icon(LucideIcons.minus,
                                            size: 12, color: FitnColors.ink),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                ),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border(top: BorderSide(color: FitnColors.ink10, width: 1)),
                  ),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('TOTAL',
                              style: FitnText.microLabel),
                          Text('\$${total.toStringAsFixed(2)}',
                              style: FitnText.mono.copyWith(
                                  fontSize: 16,
                                  color: FitnColors.accent,
                                  fontWeight: FontWeight.w700)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: cart.isEmpty ? null : _checkout,
                          style: ElevatedButton.styleFrom(
                              backgroundColor: FitnColors.accent),
                          child: Text('CHECKOUT', style: FitnText.buttonLabel),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCheckoutModal(double total) {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(20),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: FitnColors.cream,
            border: Border.all(color: FitnColors.ink, width: 1),
          ),
          child: _isProcessing
              ? Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(color: FitnColors.accent),
                    const SizedBox(height: 16),
                    Text('Processing payment...', style: FitnText.bodyItalic),
                  ],
                )
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('CHECKOUT', style: FitnText.microLabel),
                        IconButton(
                          icon: Icon(LucideIcons.x, size: 16),
                          onPressed: () => setState(() => _isCheckoutOpen = false),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text('Total: \$${total.toStringAsFixed(2)}',
                        style: FitnText.headline.copyWith(fontSize: 22)),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _addressCtrl,
                      decoration: const InputDecoration(labelText: 'Delivery Address'),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _cardCtrl,
                      decoration: const InputDecoration(labelText: 'Card Details'),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _placeOrder,
                      style: ElevatedButton.styleFrom(backgroundColor: FitnColors.accent),
                      child: Text('PLACE ORDER • \$${total.toStringAsFixed(2)}',
                          style: FitnText.buttonLabel),
                    ),
                  ],
                ),
        ),
      ),
    );
  }

  Widget _buildSuccessOverlay() {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(40),
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: FitnColors.cream,
            border: Border.all(color: FitnColors.accent, width: 2),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(LucideIcons.truck, size: 48, color: FitnColors.accent),
              const SizedBox(height: 16),
              Text('ORDER CONFIRMED!', style: FitnText.headline.copyWith(fontSize: 20)),
              const SizedBox(height: 8),
              Text('Your gear is on the way.', style: FitnText.serifItalic),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProductCard extends StatelessWidget {
  const _ProductCard({required this.product, required this.onAdd});
  final MarketplaceProduct product;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    return FitnCard(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            children: [
              SizedBox(
                height: 140,
                width: double.infinity,
                child: Image.network(product.image,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                        color: FitnColors.ink05,
                        child: const Icon(LucideIcons.image, size: 40))),
              ),
              if (product.badge != null)
                Positioned(
                  top: 8,
                  left: 8,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    color: FitnColors.accent,
                    child: Text(
                      product.badge!.toUpperCase(),
                      style: GoogleFonts.inter(
                          fontSize: 8,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.0,
                          color: Colors.white),
                    ),
                  ),
                ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.all(10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(LucideIcons.star, size: 10, color: FitnColors.accent),
                    const SizedBox(width: 4),
                    Text(product.rating.toStringAsFixed(1),
                        style: FitnText.monoSmall.copyWith(
                            fontSize: 9, color: FitnColors.ink60)),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  product.name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.inter(
                      fontSize: 10, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 4),
                Text(
                  '\$${product.price.toStringAsFixed(2)}',
                  style: FitnText.mono.copyWith(
                      fontSize: 13,
                      color: FitnColors.ink,
                      fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: onAdd,
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(0, 28),
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(LucideIcons.plus, size: 12, color: FitnColors.ink),
                        const SizedBox(width: 4),
                        Text('ADD',
                            style: GoogleFonts.inter(
                                fontSize: 9,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.0,
                                color: FitnColors.ink)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
