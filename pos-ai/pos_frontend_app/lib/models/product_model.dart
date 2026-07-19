class ProductOptionModel {
  final String id;
  final String name;
  final double price;

  ProductOptionModel({
    required this.id,
    required this.name,
    required this.price,
  });

  factory ProductOptionModel.fromJson(Map<String, dynamic> json) {
    return ProductOptionModel(
      id: json['id'],
      name: json['name'],
      price: (json['price'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'price': price,
    };
  }
}

class ProductModel {
  final String id;
  final String name;
  final double price;
  final String? imageUrl;
  final String categoryId;
  final List<ProductOptionModel> options;

  ProductModel({
    required this.id,
    required this.name,
    required this.price,
    this.imageUrl,
    required this.categoryId,
    required this.options,
  });

  factory ProductModel.fromJson(Map<String, dynamic> json) {
    var optsList = json['options'] as List? ?? [];
    List<ProductOptionModel> parsedOpts =
        optsList.map((opt) => ProductOptionModel.fromJson(opt)).toList();

    return ProductModel(
      id: json['id'],
      name: json['name'],
      price: (json['price'] as num).toDouble(),
      imageUrl: json['imageUrl'],
      categoryId: json['categoryId'],
      options: parsedOpts,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'price': price,
      'imageUrl': imageUrl,
      'categoryId': categoryId,
      'options': options.map((opt) => opt.toJson()).toList(),
    };
  }
}
