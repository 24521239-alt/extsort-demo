"""
Ứng dụng minh hoạ sắp xếp ngoại (External Sorting) cho 1 file float64 nhị phân
- Chọn file input
- Chọn nơi lưu file output
- Nếu file nhỏ (<= giới hạn minh hoạ) thì sẽ in log các bước tạo run + merge theo pass
- Có nút tạo file mẫu, xem 20 số đầu, kiểm tra tăng dần
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

import extsort_core


class ExtSortApp(tk.Tk):
    """
    Cửa sổ chính

    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Minh hoạ sắp xếp ngoại (ExtSort)")
        self.geometry("760x460")
        self.minsize(720, 420)
        self.resizable(True, True)

        self.file_in = tk.StringVar()
        self.file_out = tk.StringVar()

        self.gioi_han_minh_hoa = tk.IntVar(value=2000)
        self.gioi_han_run = tk.IntVar(value=4096)
        self.so_phan_tu_moi_khoi = tk.IntVar(value=1024)

        self.hien_nang_cao = tk.BooleanVar(value=False)

        self._tao_giao_dien()

    def _tao_giao_dien(self) -> None:
        """Dựng giao diện"""
        khung = ttk.Frame(self, padding=10)
        khung.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        khung.columnconfigure(1, weight=1)
        khung.rowconfigure(10, weight=1)

        # Input 
        ttk.Label(khung, text="File input:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(khung, textvariable=self.file_in).grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 8))
        ttk.Button(khung, text="Chọn...", command=self._chon_file_in, width=10).grid(row=0, column=2, sticky="e", pady=4)

        # Output 
        ttk.Label(khung, text="File output:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(khung, textvariable=self.file_out).grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 8))
        ttk.Button(khung, text="Lưu...", command=self._chon_file_out, width=10).grid(row=1, column=2, sticky="e", pady=4)

        # Minh hoạ 
        ttk.Label(khung, text="Giới hạn minh hoạ (số phần tử):").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Spinbox(khung, from_=10, to=200000, textvariable=self.gioi_han_minh_hoa, width=12).grid(
            row=2, column=1, sticky="w", pady=4, padx=(8, 0)
        )

        # Tuỳ chọn nâng cao
        ttk.Checkbutton(
            khung, text="Tuỳ chọn nâng cao",
            variable=self.hien_nang_cao, command=self._doi_trang_thai_nang_cao
        ).grid(row=3, column=0, sticky="w", pady=(6, 4))

        self.khung_nang_cao = ttk.Frame(khung)
        self.khung_nang_cao.grid(row=4, column=0, columnspan=3, sticky="ew")
        self.khung_nang_cao.columnconfigure(1, weight=1)

        ttk.Label(self.khung_nang_cao, text="Giới hạn run ban đầu:").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Spinbox(self.khung_nang_cao, from_=128, to=5000000, textvariable=self.gioi_han_run, width=12).grid(
            row=0, column=1, sticky="w", pady=3, padx=(8, 0)
        )

        ttk.Label(self.khung_nang_cao, text="Số phần tử mỗi khối đọc/ghi:").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Spinbox(self.khung_nang_cao, from_=64, to=5000000, textvariable=self.so_phan_tu_moi_khoi, width=12).grid(
            row=1, column=1, sticky="w", pady=3, padx=(8, 0)
        )

        self._doi_trang_thai_nang_cao()

        # Nút
        dong_nut = ttk.Frame(khung)
        dong_nut.grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 8))

        ttk.Button(dong_nut, text="Sắp xếp", command=self._bam_sap_xep, width=10).pack(side="left")
        ttk.Button(dong_nut, text="Tạo file mẫu", command=self._tao_file_mau).pack(side="left", padx=8)
        ttk.Button(dong_nut, text="Xem 20 số đầu", command=self._xem_20_so_dau).pack(side="left")
        ttk.Button(dong_nut, text="Kiểm tra tăng dần", command=self._kiem_tra_file).pack(side="left", padx=8)
        ttk.Button(dong_nut, text="Xoá log", command=self._xoa_log).pack(side="left")

        # Log
        ttk.Label(khung, text="Log:").grid(row=6, column=0, sticky="w")

        khung_log = ttk.Frame(khung)
        khung_log.grid(row=10, column=0, columnspan=3, sticky="nsew", pady=(4, 0))
        khung.rowconfigure(10, weight=1)

        self.o_log = tk.Text(khung_log, height=10, wrap="none")
        self.o_log.grid(row=0, column=0, sticky="nsew")

        cuon_doc = ttk.Scrollbar(khung_log, orient="vertical", command=self.o_log.yview)
        cuon_doc.grid(row=0, column=1, sticky="ns")

        cuon_ngang = ttk.Scrollbar(khung_log, orient="horizontal", command=self.o_log.xview)
        cuon_ngang.grid(row=1, column=0, sticky="ew")

        self.o_log.configure(yscrollcommand=cuon_doc.set, xscrollcommand=cuon_ngang.set, state="disabled")

        khung_log.rowconfigure(0, weight=1)
        khung_log.columnconfigure(0, weight=1)

    def _doi_trang_thai_nang_cao(self) -> None:
        """Ẩn/hiện phần tuỳ chọn nâng cao"""
        if self.hien_nang_cao.get():
            self.khung_nang_cao.grid()
        else:
            self.khung_nang_cao.grid_remove()

    def _ghi_log(self, msg: str) -> None:
        """Ghi một dòng vào log"""
        self.o_log.configure(state="normal")
        self.o_log.insert(tk.END, msg + "\n")
        self.o_log.see(tk.END)
        self.o_log.configure(state="disabled")

    def _xoa_log(self) -> None:
        """Xoá log """
        self.o_log.configure(state="normal")
        self.o_log.delete("1.0", tk.END)
        self.o_log.configure(state="disabled")

    def _in_ds_so(self, values, moi_dong: int = 6) -> None:
        """In danh sách số """
        parts = [f"{x:.6g}" for x in values]
        for i in range(0, len(parts), moi_dong):
            self._ghi_log("  " + "  ".join(parts[i:i + moi_dong]))

    def _kiem_tra_float64_file(self, path: str) -> int:
        """Kiểm tra file có đúng float64 và trả về số phần tử """
        if not os.path.exists(path):
            raise FileNotFoundError("File không tồn tại.")
        size = os.path.getsize(path)
        if size % 8 != 0:
            raise ValueError("File không đúng định dạng float64 (dung lượng không chia hết cho 8).")
        return size // 8

    def _chon_file_in(self) -> None:
        """Chọn file input """
        path = filedialog.askopenfilename(
            title="Chọn file input",
            filetypes=[("Binary file", "*.bin"), ("Tất cả", "*.*")]
        )
        if path:
            self.file_in.set(path)
            self._ghi_log(f"Đã chọn input: {path}")

    def _chon_file_out(self) -> None:
        """Chọn nơi lưu output """
        path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu output",
            defaultextension=".bin",
            filetypes=[("Binary file", "*.bin"), ("Tất cả", "*.*")]
        )
        if path:
            self.file_out.set(path)
            self._ghi_log(f"Output sẽ lưu tại: {path}")

    def _tao_file_mau(self) -> None:
        """Tạo file mẫu (ngẫu nhiên) để test """
        path = filedialog.asksaveasfilename(
            title="Lưu file mẫu",
            defaultextension=".bin",
            filetypes=[("Binary file", "*.bin"), ("Tất cả", "*.*")]
        )
        if not path:
            return

        so_pt = simpledialog.askinteger("Số phần tử", "Bạn muốn tạo bao nhiêu số?", initialvalue=60, minvalue=1, maxvalue=200000)
        if so_pt is None:
            return

        seed = simpledialog.askinteger("Seed", "Seed ngẫu nhiên:", initialvalue=1, minvalue=0, maxvalue=10**9)
        if seed is None:
            return

        try:
            extsort_core.tao_file_mau(path, so_phan_tu=int(so_pt), seed=int(seed))
            self.file_in.set(path)
            self._ghi_log(f"Đã tạo file mẫu: {path}")
            self._ghi_log(f"Số phần tử: {so_pt}")
            self._ghi_log("20 số đầu:")
            self._in_ds_so(extsort_core.doc_vai_so(path, 20))
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _xem_20_so_dau(self) -> None:
        """Xem 20 số đầu của file input """
        path = self.file_in.get().strip()
        if not path:
            messagebox.showwarning("Thiếu file", "Bạn chưa chọn file input.")
            return

        try:
            n = self._kiem_tra_float64_file(path)
            head = extsort_core.doc_vai_so(path, 20)
            self._ghi_log(f"File hiện tại có {n} phần tử.")
            self._ghi_log("20 số đầu:")
            self._in_ds_so(head)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _kiem_tra_file(self) -> None:
        """
        Kiểm tra file output (nếu có), nếu không thì kiểm tra file input.
        Mục đích: check file output tăng dần.
        """
        path = self.file_out.get().strip() or self.file_in.get().strip()
        if not path:
            messagebox.showwarning("Thiếu file", "Bạn chưa chọn file để kiểm tra.")
            return

        if not os.path.exists(path):
            messagebox.showerror("Lỗi", "File cần kiểm tra không tồn tại.")
            return

        try:
            n = self._kiem_tra_float64_file(path)
            ok = extsort_core.kiem_tra_tang_dan(path)
            self._ghi_log(f"Kiểm tra: {path}")
            self._ghi_log(f"  Số phần tử: {n}")
            self._ghi_log(f"  Tăng dần: {'ĐÚNG' if ok else 'SAI'}")
            messagebox.showinfo("Kết quả", f"Tăng dần: {'ĐÚNG' if ok else 'SAI'}")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _bam_sap_xep(self) -> None:
        """Chạy sắp xếp ngoại cho 1 file """
        fin = self.file_in.get().strip()
        fout = self.file_out.get().strip()

        if not fin or not fout:
            messagebox.showwarning("Thiếu thông tin", "Bạn cần chọn file input và file output.")
            return

        try:
            n = self._kiem_tra_float64_file(fin)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
            return

        self._ghi_log("Bắt đầu...")
        self._ghi_log(f"Input : {fin}")
        self._ghi_log(f"Output: {fout}")
        self._ghi_log(f"Số phần tử: {n}")
        self._ghi_log(f"Giới hạn minh hoạ: {int(self.gioi_han_minh_hoa.get())}")

        if self.hien_nang_cao.get():
            self._ghi_log(f"Giới hạn run: {int(self.gioi_han_run.get())}")
            self._ghi_log(f"Khối đọc/ghi: {int(self.so_phan_tu_moi_khoi.get())}")

        try:
            extsort_core.sap_xep_ngoai_1_file(
                fin,
                fout,
                gioi_han_run=int(self.gioi_han_run.get()),
                so_phan_tu_moi_khoi=int(self.so_phan_tu_moi_khoi.get()),
                gioi_han_minh_hoa=int(self.gioi_han_minh_hoa.get()),
                gui_log=self._ghi_log
            )
            self._ghi_log("Xong.")
            messagebox.showinfo("Hoàn tất", "Đã sắp xếp xong.")
        except Exception as e:
            self._ghi_log(f"[LỖI] {e}")
            messagebox.showerror("Lỗi", str(e))


if __name__ == "__main__":
    ExtSortApp().mainloop()