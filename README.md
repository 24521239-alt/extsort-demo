# extsort-demo

Ứng dụng minh hoạ sắp xếp ngoại (External Sorting) cho file nhị phân chứa số thực float64 (8 bytes).

Cách chạy: mở terminal tại thư mục repo và chạy:
python app.py

Định dạng dữ liệu:
- File .bin gồm các số float64 liên tiếp, mỗi số 8 bytes, không có header.
- File output cũng cùng định dạng.

Chức năng chính:
- Chọn file input và file output, sắp xếp tăng dần.
- Nếu file nhỏ (<= “Giới hạn minh hoạ”), chương trình in log quá trình: tạo run và merge theo từng pass.
- Có nút tạo file mẫu, xem 20 số đầu, kiểm tra tăng dần.
