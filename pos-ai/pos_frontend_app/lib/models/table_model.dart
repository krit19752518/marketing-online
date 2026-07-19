class TableModel {
  final String id;
  final String number;
  final String status; // 'VACANT', 'OCCUPIED', 'BILLING'

  TableModel({
    required this.id,
    required this.number,
    required this.status,
  });

  factory TableModel.fromJson(Map<String, dynamic> json) {
    return TableModel(
      id: json['id'],
      number: json['number'],
      status: json['status'] ?? 'VACANT',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'number': number,
      'status': status,
    };
  }
}
