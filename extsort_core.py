"""
Nơi chứa phần xử lý file và thuật toán sắp xếp ngoại (External Sort)
Định dạng file dữ liệu:
- File nhị phân, lưu các số thực 8 bytes (float64)
- Các số nằm liên tiếp nhau, không có header
"""

import os
import struct
import random
from typing import List
import tempfile
import shutil
from typing import Callable, Optional


def dem_phan_tu(file_path: str) -> int:
    """
    Đếm số phần tử (float64) trong file.
    - Trả về: Số lượng phần tử = dung lượng file / 8.
    - Báo lỗi: ValueError nếu file không chia hết cho 8.
    """
    size = os.path.getsize(file_path)
    if size % 8 != 0:
        raise ValueError("File không đúng định dạng float64 (dung lượng không chia hết cho 8).")
    return size // 8


def doc_khoi(f, so_phan_tu: int) -> List[float]:
    """
    Đọc tối đa 'so_phan_tu' số float64 từ file đang mở

    Đọc kiểu streaming: đọc một khối rồi xử lý
    """
    if so_phan_tu <= 0:
        raise ValueError("so_phan_tu phải > 0")

    data = f.read(so_phan_tu * 8)
    if not data:
        return []

    if len(data) % 8 != 0:
        raise ValueError("File bị lỗi: số byte không chia hết cho 8.")

    out = []
    for (x,) in struct.iter_unpack("<d", data):
        out.append(x)
    return out


def ghi_khoi(f, values: List[float]) -> None:
    """
    Ghi một danh sách số float64 ra file đang mở

    values: Danh sách số cần ghi (sẽ được ép về float)
    """
    if not values:
        return

    buf = bytearray(8 * len(values))
    for i, v in enumerate(values):
        struct.pack_into("<d", buf, i * 8, float(v))
    f.write(buf)


def doc_vai_so(file_path: str, n: int = 20) -> List[float]:
    """
    Đọc n số đầu tiên trong file để xem nhanh (debug / minh hoạ file nhỏ)
    """
    if n <= 0:
        return []
    with open(file_path, "rb") as f:
        return doc_khoi(f, n)


def tao_file_mau(file_path: str, so_phan_tu: int = 50, seed: int = 1) -> None:
    """
    Tạo một file .bin mẫu chứa float64 ngẫu nhiên.

    Mục đích:
        - Có dữ liệu nhỏ để test app
        - Dùng cho minh hoạ 

    so_phan_tu: Số lượng phần tử muốn tạo (em nghĩ 20-200 cho dễ quan sát)
    """
    if so_phan_tu <= 0:
        raise ValueError("so_phan_tu phải > 0")

    rnd = random.Random(seed)
    values = [rnd.uniform(-100.0, 100.0) for _ in range(so_phan_tu)]

    with open(file_path, "wb") as f:
        ghi_khoi(f, values)


def kiem_tra_tang_dan(file_path: str, so_phan_tu_moi_khoi: int = 2048) -> bool:
    """
    Kiểm tra file có đang tăng dần không (không cần đọc hết vào RAM)

    Trả về: True nếu tăng dần (không giảm), False nếu có chỗ bị giảm
    """
    prev = None
    with open(file_path, "rb") as f:
        while True:
            block = doc_khoi(f, so_phan_tu_moi_khoi)
            if not block:
                break
            for x in block:
                if prev is not None and x < prev:
                    return False
                prev = x
    return True


def tron_hai_file_da_sap_xep(file_a: str, file_b: str, file_out: str, so_phan_tu_moi_khoi: int = 1024) -> None:
    """
    Trộn 2 file float64 đã sắp xếp tăng dần thành 1 file tăng dần.
    - Mỗi file có 1 buffer đọc theo khối
    - Output có 1 buffer ghi
    - So sánh phần tử hiện tại của A và B rồi ghi ra output
    - Đủ khối thì flush xuống disk

    """
    if so_phan_tu_moi_khoi <= 0:
        raise ValueError("so_phan_tu_moi_khoi phải > 0")

    dem_phan_tu(file_a)
    dem_phan_tu(file_b)

    with open(file_a, "rb") as fa, open(file_b, "rb") as fb, open(file_out, "wb") as fo:
        buf_a = doc_khoi(fa, so_phan_tu_moi_khoi)
        buf_b = doc_khoi(fb, so_phan_tu_moi_khoi)
        ia = 0
        ib = 0
        out_buf = []

        def lay_a():
            nonlocal buf_a, ia
            while True:
                if not buf_a:
                    return None
                if ia < len(buf_a):
                    v = buf_a[ia]
                    ia += 1
                    return v
                buf_a = doc_khoi(fa, so_phan_tu_moi_khoi)
                ia = 0

        def lay_b():
            nonlocal buf_b, ib
            while True:
                if not buf_b:
                    return None
                if ib < len(buf_b):
                    v = buf_b[ib]
                    ib += 1
                    return v
                buf_b = doc_khoi(fb, so_phan_tu_moi_khoi)
                ib = 0

        def flush():
            if out_buf:
                ghi_khoi(fo, out_buf)
                out_buf.clear()

        a = lay_a()
        b = lay_b()

        while a is not None and b is not None:
            if a <= b:
                out_buf.append(a)
                a = lay_a()
            else:
                out_buf.append(b)
                b = lay_b()

            if len(out_buf) >= so_phan_tu_moi_khoi:
                flush()

        while a is not None:
            out_buf.append(a)
            if len(out_buf) >= so_phan_tu_moi_khoi:
                flush()
            a = lay_a()

        while b is not None:
            out_buf.append(b)
            if len(out_buf) >= so_phan_tu_moi_khoi:
                flush()
            b = lay_b()

        flush()


def sap_xep_ngoai_1_file(
    file_in: str,
    file_out: str,
    gioi_han_run: int = 4096,
    so_phan_tu_moi_khoi: int = 1024,
    gioi_han_minh_hoa: int = 0,
    gui_log: Optional[Callable[[str], None]] = None
) -> None:
    """
    Sắp xếp tăng dần 1 file nhị phân (float64) bằng External Merge Sort

    Nếu gioi_han_minh_hoa > 0 và file có số phần tử <= gioi_han_minh_hoa
    thì chương trình sẽ ghi log minh hoạ

    Tham số thêm:
        gioi_han_minh_hoa: ngưỡng để bật minh hoạ (0 là tắt).
        gui_log: hàm ghi log (hàm ghi vào ô log của GUI).
    """
    if gioi_han_run <= 0:
        raise ValueError("gioi_han_run phải > 0")
    if so_phan_tu_moi_khoi <= 0:
        raise ValueError("so_phan_tu_moi_khoi phải > 0")

    n = dem_phan_tu(file_in)
    if n == 0:
        with open(file_out, "wb") as f:
            pass
        return

    bat_minh_hoa = (gioi_han_minh_hoa > 0 and n <= gioi_han_minh_hoa)

    def log(msg: str) -> None:
        if gui_log is not None:
            gui_log(msg)

    def tom_tat_file(path: str, max_so: int = 12) -> str:
        """Lấy vài số đầu để minh hoạ """
        head = doc_vai_so(path, max_so)
        return " ".join(f"{x:.6g}" for x in head)

    thu_muc_tam = tempfile.mkdtemp(prefix="extsort_")

    def path_run(ten: str) -> str:
        return os.path.join(thu_muc_tam, ten)

    runs = []

    try:
        # 1: tạo initial runs
        if bat_minh_hoa:
            log(f"[Minh hoạ] File có {n} phần tử, bắt đầu tạo run...")

        with open(file_in, "rb") as fi:
            idx = 0
            while True:
                block = doc_khoi(fi, gioi_han_run)
                if not block:
                    break
                block.sort()
                p = path_run(f"run_{idx:04d}.bin")
                with open(p, "wb") as fr:
                    ghi_khoi(fr, block)
                runs.append(p)

                if bat_minh_hoa:
                    log(f"  Run {idx+1}: {len(block)} số | đầu run: {tom_tat_file(p)}")

                idx += 1

        if len(runs) == 1:
            if os.path.exists(file_out):
                os.remove(file_out)
            shutil.copyfile(runs[0], file_out)
            if bat_minh_hoa:
                log("[Minh hoạ] Chỉ có 1 run, không cần merge.")
            return

        # 2: merge theo pass
        pass_no = 1
        while len(runs) > 1:
            if bat_minh_hoa:
                log(f"[Minh hoạ] Pass {pass_no}: merge {len(runs)} run...")

            run_moi = []
            i = 0
            pair_no = 1

            while i < len(runs):
                if i + 1 >= len(runs):
                    run_moi.append(runs[i])
                    if bat_minh_hoa:
                        log(f"  Còn lẻ 1 run, giữ lại cho pass sau: {os.path.basename(runs[i])}")
                    i += 1
                    continue

                a = runs[i]
                b = runs[i + 1]
                outp = path_run(f"pass{pass_no:02d}_{len(run_moi):04d}.bin")

                if bat_minh_hoa:
                    log(f"  Merge {pair_no}: {os.path.basename(a)} + {os.path.basename(b)}")
                    log(f"    A head: {tom_tat_file(a)}")
                    log(f"    B head: {tom_tat_file(b)}")

                tron_hai_file_da_sap_xep(a, b, outp, so_phan_tu_moi_khoi=so_phan_tu_moi_khoi)
                run_moi.append(outp)

                if bat_minh_hoa:
                    log(f"    -> Out head: {tom_tat_file(outp)}")

                i += 2
                pair_no += 1

            runs = run_moi
            pass_no += 1

        ket_qua = runs[0]
        if os.path.exists(file_out):
            os.remove(file_out)
        shutil.copyfile(ket_qua, file_out)

        if bat_minh_hoa:
            log("[Minh hoạ] Hoàn tất. File output đã tạo xong.")

    finally:
        shutil.rmtree(thu_muc_tam, ignore_errors=True)