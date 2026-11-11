#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量文件重命名工具 v2.1
Author: WorkBuddy
Description: Windows 桌面版批量文件重命名软件 - 增强版
支持多选功能组合、倒序排序、删除指定文字等
"""

import os
import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from uuid import uuid4


class RenameBatchError(Exception):
    """批量操作失败；remaining 记录未能恢复原名的文件当前位置。"""

    def __init__(self, error, remaining):
        super().__init__(str(error))
        self.remaining = remaining


class BatchRenameApp:
    """批量文件重命名主应用"""

    def __init__(self, root):
        self.root = root
        self.root.title("批量文件重命名工具 v2.1")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)

        # 设置主题颜色
        self.colors = {
            "bg": "#f5f5f5",
            "sidebar": "#2c3e50",
            "sidebar_text": "#ecf0f1",
            "accent": "#3498db",
            "accent_hover": "#2980b9",
            "success": "#27ae60",
            "danger": "#e74c3c",
            "warning": "#f39c12",
            "text": "#2c3e50",
            "text_light": "#7f8c8d",
            "white": "#ffffff",
            "border": "#dcdde1",
            "row_even": "#ffffff",
            "row_odd": "#f8f9fa",
            "preview_new": "#d4edda",
            "preview_unchanged": "#ffffff",
        }

        self.root.configure(bg=self.colors["bg"])

        # 数据存储
        self.current_dir = ""
        self.files = []
        self.rename_history = []
        self.selection_mode = "directory"

        # 功能开关变量
        self.enable_reverse = tk.BooleanVar(value=False)
        self.enable_delete_text = tk.BooleanVar(value=False)
        self.enable_replace = tk.BooleanVar(value=False)
        self.enable_prefix = tk.BooleanVar(value=False)
        self.enable_suffix = tk.BooleanVar(value=False)
        self.enable_sequence = tk.BooleanVar(value=False)
        self.enable_regex = tk.BooleanVar(value=False)
        self.enable_case = tk.BooleanVar(value=False)
        self.enable_ext = tk.BooleanVar(value=False)

        # 创建界面
        self._create_styles()
        self._create_widgets()

    def _create_styles(self):
        """创建自定义样式"""
        style = ttk.Style()
        style.theme_use("clam")

        # 按钮样式
        style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground=self.colors["white"],
            padding=(15, 8),
            font=("Microsoft YaHei UI", 10),
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.colors["accent_hover"])],
        )

        style.configure(
            "Success.TButton",
            background=self.colors["success"],
            foreground=self.colors["white"],
            padding=(15, 8),
            font=("Microsoft YaHei UI", 10),
        )
        style.map(
            "Success.TButton",
            background=[("active", "#219a52")],
        )

        style.configure(
            "Danger.TButton",
            background=self.colors["danger"],
            foreground=self.colors["white"],
            padding=(15, 8),
            font=("Microsoft YaHei UI", 10),
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#c0392b")],
        )

        # Treeview 样式
        style.configure(
            "FileTree.Treeview",
            background=self.colors["white"],
            foreground=self.colors["text"],
            rowheight=30,
            fieldbackground=self.colors["white"],
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "FileTree.Treeview.Heading",
            background=self.colors["sidebar"],
            foreground=self.colors["white"],
            font=("Microsoft YaHei UI", 10, "bold"),
            padding=(10, 8),
        )
        style.map(
            "FileTree.Treeview",
            background=[("selected", self.colors["accent"])],
            foreground=[("selected", self.colors["white"])],
        )

    def _create_widgets(self):
        """创建主界面组件"""
        # 顶部工具栏
        self._create_toolbar()

        # 主内容区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 左侧面板 - 重命名选项
        left_panel = ttk.LabelFrame(main_frame, text="重命名选项（可多选组合）", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

        # 右侧面板 - 文件列表和预览
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建左侧选项
        self._create_rename_options(left_panel)

        # 创建右侧文件列表
        self._create_file_list(right_panel)

        # 底部状态栏
        self._create_statusbar()

    def _create_toolbar(self):
        """创建顶部工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        # 选择文件夹按钮
        ttk.Button(
            toolbar,
            text="📁 选择文件夹",
            style="Accent.TButton",
            command=self._select_directory,
        ).pack(side=tk.LEFT, padx=(0, 5))

        # 选择文件按钮
        ttk.Button(
            toolbar,
            text="📄 选择文件",
            style="Accent.TButton",
            command=self._select_files,
        ).pack(side=tk.LEFT, padx=(0, 10))

        # 刷新按钮
        ttk.Button(
            toolbar,
            text="🔄 刷新",
            style="Accent.TButton",
            command=self._refresh_files,
        ).pack(side=tk.LEFT, padx=(0, 10))

        # 当前路径显示
        self.path_var = tk.StringVar(value="请选择文件夹或文件...")
        path_label = ttk.Label(
            toolbar,
            textvariable=self.path_var,
            font=("Microsoft YaHei UI", 10),
            foreground=self.colors["text_light"],
        )
        path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 撤销按钮
        ttk.Button(
            toolbar,
            text="↩ 撤销上次",
            style="Danger.TButton",
            command=self._undo_last_rename,
        ).pack(side=tk.RIGHT, padx=(10, 0))

    def _create_rename_options(self, parent):
        """创建重命名选项面板"""
        # 创建滚动区域
        canvas = tk.Canvas(parent, width=280, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        parent = scrollable_frame

        # ========== 倒序排序 ==========
        reverse_frame = ttk.LabelFrame(parent, text="排序选项", padding=5)
        reverse_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            reverse_frame,
            text="🔄 倒序排列文件",
            variable=self.enable_reverse,
        ).pack(anchor=tk.W, pady=2)

        # ========== 删除指定文字 ==========
        delete_frame = ttk.LabelFrame(parent, text="删除文字", padding=5)
        delete_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            delete_frame,
            text="🗑 删除指定文字",
            variable=self.enable_delete_text,
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(delete_frame, text="要删除的文字:").pack(anchor=tk.W)
        self.entry_delete_text = ttk.Entry(delete_frame, width=25)
        self.entry_delete_text.pack(fill=tk.X, pady=(2, 5))

        # ========== 查找替换 ==========
        replace_frame = ttk.LabelFrame(parent, text="查找替换", padding=5)
        replace_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            replace_frame,
            text="🔄 查找替换",
            variable=self.enable_replace,
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(replace_frame, text="查找:").pack(anchor=tk.W)
        self.entry_find = ttk.Entry(replace_frame, width=25)
        self.entry_find.pack(fill=tk.X, pady=(2, 5))

        ttk.Label(replace_frame, text="替换为:").pack(anchor=tk.W)
        self.entry_replace = ttk.Entry(replace_frame, width=25)
        self.entry_replace.pack(fill=tk.X, pady=(2, 5))

        self.replace_all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            replace_frame,
            text="替换所有匹配项",
            variable=self.replace_all_var,
        ).pack(anchor=tk.W)

        # ========== 添加前缀 ==========
        prefix_frame = ttk.LabelFrame(parent, text="添加前缀", padding=5)
        prefix_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            prefix_frame,
            text="➕ 添加前缀",
            variable=self.enable_prefix,
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(prefix_frame, text="前缀文本:").pack(anchor=tk.W)
        self.entry_prefix = ttk.Entry(prefix_frame, width=25)
        self.entry_prefix.pack(fill=tk.X, pady=(2, 5))

        # ========== 添加后缀 ==========
        suffix_frame = ttk.LabelFrame(parent, text="添加后缀", padding=5)
        suffix_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            suffix_frame,
            text="➕ 添加后缀",
            variable=self.enable_suffix,
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(suffix_frame, text="后缀文本:").pack(anchor=tk.W)
        self.entry_suffix = ttk.Entry(suffix_frame, width=25)
        self.entry_suffix.pack(fill=tk.X, pady=(2, 5))

        # ========== 序号重命名 ==========
        sequence_frame = ttk.LabelFrame(parent, text="序号重命名", padding=5)
        sequence_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            sequence_frame,
            text="🔢 序号重命名",
            variable=self.enable_sequence,
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(sequence_frame, text="基础名称 (可为空):").pack(anchor=tk.W)
        self.entry_base_name = ttk.Entry(sequence_frame, width=25)
        self.entry_base_name.insert(0, "")
        self.entry_base_name.pack(fill=tk.X, pady=(2, 5))

        ttk.Label(sequence_frame, text="起始序号:").pack(anchor=tk.W)
        self.entry_start_num = ttk.Entry(sequence_frame, width=25)
        self.entry_start_num.insert(0, "1")
        self.entry_start_num.pack(fill=tk.X, pady=(2, 5))

        ttk.Label(sequence_frame, text="序号位数 (补零):").pack(anchor=tk.W)
        self.entry_digits = ttk.Entry(sequence_frame, width=25)
        self.entry_digits.insert(0, "3")
        self.entry_digits.pack(fill=tk.X, pady=(2, 5))

        # ========== 正则替换 ==========
        regex_frame = ttk.LabelFrame(parent, text="正则替换", padding=5)
        regex_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            regex_frame,
            text="📝 正则替换",
            variable=self.enable_regex,
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(regex_frame, text="正则表达式:").pack(anchor=tk.W)
        self.entry_regex = ttk.Entry(regex_frame, width=25)
        self.entry_regex.pack(fill=tk.X, pady=(2, 5))

        ttk.Label(regex_frame, text="替换为:").pack(anchor=tk.W)
        self.entry_regex_replace = ttk.Entry(regex_frame, width=25)
        self.entry_regex_replace.pack(fill=tk.X, pady=(2, 5))

        # ========== 大小写转换 ==========
        case_frame = ttk.LabelFrame(parent, text="大小写转换", padding=5)
        case_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            case_frame,
            text="Aa 大小写转换",
            variable=self.enable_case,
        ).pack(anchor=tk.W, pady=2)

        self.case_mode = tk.StringVar(value="lower")
        cases = [
            ("全部小写", "lower"),
            ("全部大写", "upper"),
            ("首字母大写", "title"),
            ("驼峰命名", "camel"),
        ]
        for text, value in cases:
            ttk.Radiobutton(
                case_frame,
                text=text,
                value=value,
                variable=self.case_mode,
            ).pack(anchor=tk.W, pady=1)

        # ========== 扩展名修改 ==========
        ext_frame = ttk.LabelFrame(parent, text="扩展名修改", padding=5)
        ext_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            ext_frame,
            text="📎 修改扩展名",
            variable=self.enable_ext,
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(ext_frame, text="新扩展名 (如 .txt):").pack(anchor=tk.W)
        self.entry_new_ext = ttk.Entry(ext_frame, width=25)
        self.entry_new_ext.pack(fill=tk.X, pady=(2, 5))

        # ========== 过滤选项 ==========
        filter_frame = ttk.LabelFrame(parent, text="过滤选项", padding=5)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        self.filter_ext = tk.StringVar()
        ttk.Label(filter_frame, text="扩展名过滤 (如: .txt,.jpg):").pack(anchor=tk.W)
        ttk.Entry(filter_frame, textvariable=self.filter_ext, width=25).pack(
            fill=tk.X, pady=(2, 5)
        )

        self.filter_keyword = tk.StringVar()
        ttk.Label(filter_frame, text="关键字过滤:").pack(anchor=tk.W)
        ttk.Entry(filter_frame, textvariable=self.filter_keyword, width=25).pack(
            fill=tk.X, pady=(2, 5)
        )

        # ========== 预览和执行按钮 ==========
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            btn_frame,
            text="👁 预览效果",
            style="Accent.TButton",
            command=self._preview_rename,
        ).pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            btn_frame,
            text="✅ 执行重命名",
            style="Success.TButton",
            command=self._execute_rename,
        ).pack(fill=tk.X)

    def _create_file_list(self, parent):
        """创建文件列表"""
        list_frame = ttk.LabelFrame(parent, text="文件列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建 Treeview
        columns = ("序号", "原文件名", "新文件名", "大小", "修改时间")
        self.file_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            style="FileTree.Treeview",
            selectmode="extended",
        )

        # 设置列
        self.file_tree.heading("序号", text="#")
        self.file_tree.heading("原文件名", text="原文件名")
        self.file_tree.heading("新文件名", text="新文件名")
        self.file_tree.heading("大小", text="大小")
        self.file_tree.heading("修改时间", text="修改时间")

        self.file_tree.column("序号", width=40, anchor=tk.CENTER)
        self.file_tree.column("原文件名", width=200, anchor=tk.W)
        self.file_tree.column("新文件名", width=200, anchor=tk.W)
        self.file_tree.column("大小", width=80, anchor=tk.E)
        self.file_tree.column("修改时间", width=130, anchor=tk.CENTER)

        # 滚动条
        scrollbar_y = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.file_tree.yview
        )
        scrollbar_x = ttk.Scrollbar(
            list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview
        )
        self.file_tree.configure(
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set
        )

        # 布局
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_statusbar(self):
        """创建底部状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Microsoft YaHei UI", 9),
            foreground=self.colors["text_light"],
        ).pack(side=tk.LEFT)

        self.file_count_var = tk.StringVar(value="文件数: 0")
        ttk.Label(
            status_frame,
            textvariable=self.file_count_var,
            font=("Microsoft YaHei UI", 9),
            foreground=self.colors["text_light"],
        ).pack(side=tk.RIGHT)

    def _select_directory(self):
        """选择文件夹"""
        dir_path = filedialog.askdirectory(title="选择要重命名文件的文件夹")
        if dir_path:
            self.current_dir = dir_path
            self.selection_mode = "directory"
            self.path_var.set(f"文件夹: {dir_path}")
            self._load_files()

    def _select_files(self):
        """选择文件"""
        file_paths = filedialog.askopenfilenames(title="选择要重命名的文件")
        if file_paths:
            self.selection_mode = "files"
            self.current_dir = ""
            self.files = []
            for full_path in file_paths:
                try:
                    stat = os.stat(full_path)
                    self.files.append({
                        "name": os.path.basename(full_path),
                        "path": full_path,
                        "size": stat.st_size,
                        "mtime": datetime.fromtimestamp(stat.st_mtime),
                        "dir": os.path.dirname(full_path),
                    })
                except Exception as e:
                    print(f"读取文件信息失败: {full_path}, 错误: {e}")

            self.path_var.set(f"已选择 {len(self.files)} 个文件")
            self._update_file_tree()
            self.status_var.set(f"已加载 {len(self.files)} 个文件")
            self.file_count_var.set(f"文件数: {len(self.files)}")

    def _load_files(self):
        """加载文件列表"""
        if not self.current_dir:
            return False

        self.files = []
        try:
            for item in sorted(os.listdir(self.current_dir)):
                full_path = os.path.join(self.current_dir, item)
                if os.path.isfile(full_path):
                    stat = os.stat(full_path)
                    self.files.append(
                        {
                            "name": item,
                            "path": full_path,
                            "size": stat.st_size,
                            "mtime": datetime.fromtimestamp(stat.st_mtime),
                            "dir": self.current_dir,
                        }
                    )
        except OSError as e:
            self.files = []
            self._update_file_tree()
            self.status_var.set("加载文件夹失败")
            self.file_count_var.set("文件数: 0")
            messagebox.showerror("错误", f"无法读取文件夹，请检查路径和访问权限。\n{e}")
            return False

        self._update_file_tree()
        self.status_var.set(f"已加载 {len(self.files)} 个文件")
        self.file_count_var.set(f"文件数: {len(self.files)}")
        return True

    def _refresh_files(self):
        """刷新文件列表"""
        if self.selection_mode == "files":
            file_paths = [f["path"] for f in self.files]
            self.files = []
            for full_path in file_paths:
                if os.path.exists(full_path):
                    try:
                        stat = os.stat(full_path)
                        self.files.append({
                            "name": os.path.basename(full_path),
                            "path": full_path,
                            "size": stat.st_size,
                            "mtime": datetime.fromtimestamp(stat.st_mtime),
                            "dir": os.path.dirname(full_path),
                        })
                    except Exception:
                        pass
            self._update_file_tree()
            self.status_var.set(f"已刷新 {len(self.files)} 个文件")
            self.file_count_var.set(f"文件数: {len(self.files)}")
        elif self.current_dir:
            if self._load_files():
                self.status_var.set("已刷新")

    def _update_file_tree(self, new_names=None):
        """更新文件树显示"""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        filtered_files = self._get_ordered_files()

        for i, file_info in enumerate(filtered_files, 1):
            new_name = new_names[i - 1] if new_names and i - 1 < len(new_names) else ""

            size = file_info["size"]
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            time_str = file_info["mtime"].strftime("%Y-%m-%d %H:%M")

            item_id = self.file_tree.insert(
                "", tk.END, values=(i, file_info["name"], new_name, size_str, time_str)
            )

            if new_name and new_name != file_info["name"]:
                self.file_tree.item(item_id, tags=("changed",))

        self.file_tree.tag_configure("changed", background=self.colors["preview_new"])

    def _apply_filter(self, files):
        """应用过滤条件"""
        filtered = files

        ext_filter = self.filter_ext.get().strip()
        if ext_filter:
            exts = [
                "." + e.strip().lstrip(".").lower()
                for e in re.split(r"[,，]", ext_filter)
                if e.strip().lstrip(".")
            ]
            if exts:
                filtered = [
                    f for f in filtered
                    if any(f["name"].lower().endswith(ext) for ext in exts)
                ]

        keyword = self.filter_keyword.get().strip()
        if keyword:
            filtered = [
                f for f in filtered if keyword.lower() in f["name"].lower()
            ]

        return filtered

    def _get_ordered_files(self):
        """预览、序号生成和执行始终使用同一文件顺序。"""
        files = self._apply_filter(self.files)
        return files[::-1] if self.enable_reverse.get() else files

    @staticmethod
    def _validate_name(name):
        if not name or name in (".", ".."):
            raise ValueError("文件名不能为空，也不能是 . 或 ..")
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
            raise ValueError('文件名不能包含 < > : " / \\ | ? * 或控制字符')
        if name.endswith((".", " ")):
            raise ValueError("文件名不能以空格或句点结尾")
        device = name.split(".", 1)[0].rstrip(" ").upper()
        if re.fullmatch(
            r"CON|PRN|AUX|NUL|CLOCK\$|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³]",
            device,
        ):
            raise ValueError("文件名不能使用 Windows 保留名称，如 CON、NUL、COM1")
        if len(name.encode("utf-16-le", errors="surrogatepass")) // 2 > 255:
            raise ValueError("文件名过长，请缩短后重试")

    def _generate_new_names(self):
        """根据当前选中的功能组合生成新文件名"""
        filtered_files = self._get_ordered_files()
        if not filtered_files:
            messagebox.showinfo("提示", "没有符合过滤条件的文件")
            return None

        if self.enable_sequence.get():
            try:
                start_num = int(self.entry_start_num.get().strip() or "1")
                digits = int(self.entry_digits.get().strip() or "3")
            except ValueError:
                messagebox.showerror("错误", "起始序号和位数必须是整数！")
                return None
            if start_num < 0 or not 1 <= digits <= 255:
                messagebox.showerror("错误", "起始序号不能小于 0，序号位数必须在 1 到 255 之间")
                return None

        new_names = []

        for i, f in enumerate(filtered_files):
            name = f["name"]
            base, ext = os.path.splitext(name)

            # 1. 删除指定文字
            if self.enable_delete_text.get():
                delete_text = self.entry_delete_text.get()
                if delete_text:
                    base = base.replace(delete_text, "")

            # 2. 查找替换
            if self.enable_replace.get():
                find_text = self.entry_find.get()
                replace_text = self.entry_replace.get()
                if find_text:
                    if self.replace_all_var.get():
                        base = base.replace(find_text, replace_text)
                    else:
                        base = base.replace(find_text, replace_text, 1)

            # 3. 序号重命名（生成基础序号）
            if self.enable_sequence.get():
                base_name = self.entry_base_name.get().strip()
                num = str(start_num + i).zfill(digits)
                # 基础名称为空时，直接用序号；否则用基础名称+序号
                base = f"{base_name}{num}" if base_name else num

            # 4. 添加前缀（在序号基础上添加）
            if self.enable_prefix.get():
                prefix = self.entry_prefix.get()
                if prefix:
                    base = prefix + base

            # 5. 添加后缀（在序号基础上添加）
            if self.enable_suffix.get():
                suffix = self.entry_suffix.get()
                if suffix:
                    base = base + suffix

            # 6. 正则替换
            if self.enable_regex.get():
                pattern = self.entry_regex.get()
                replacement = self.entry_regex_replace.get()
                if pattern:
                    try:
                        base = re.sub(pattern, replacement, base)
                    except (re.error, IndexError) as e:
                        messagebox.showerror("错误", f"正则表达式错误: {str(e)}")
                        return None

            # 7. 大小写转换
            if self.enable_case.get():
                case_mode = self.case_mode.get()
                if case_mode == "lower":
                    base = base.lower()
                elif case_mode == "upper":
                    base = base.upper()
                elif case_mode == "title":
                    base = base.title()
                elif case_mode == "camel":
                    words = [word for word in re.split(r"[-_\s]+", base) if word]
                    base = (
                        words[0].lower() + "".join(w.capitalize() for w in words[1:])
                        if words else ""
                    )

            # 8. 修改扩展名
            if self.enable_ext.get():
                new_ext = self.entry_new_ext.get().strip()
                if new_ext:
                    if not new_ext.startswith("."):
                        new_ext = "." + new_ext
                    ext = new_ext

            new_name = base + ext
            try:
                self._validate_name(new_name)
            except ValueError as e:
                messagebox.showerror("无效文件名", f"{name!r} → {new_name!r}\n{e}")
                return None
            new_names.append(new_name)

        return new_names

    def _preview_rename(self):
        """预览重命名效果"""
        new_names = self._generate_new_names()
        if new_names is None:
            return

        self._update_file_tree(new_names)
        try:
            self._validate_rename_plan(self._make_rename_plan(new_names))
        except (OSError, ValueError) as e:
            self.status_var.set("预览发现冲突，请调整重命名选项")
            messagebox.showerror("重命名冲突", str(e))
            return
        self.status_var.set("预览模式 - 绿色背景表示将被修改的文件")

    @staticmethod
    def _path_key(path):
        return os.path.normcase(os.path.abspath(path))

    @staticmethod
    def _file_id(path):
        stat = os.lstat(path)
        return stat.st_dev, stat.st_ino

    @staticmethod
    def _rename_file(old_path, new_path):
        """保留重名保护，同时允许 Windows 上只修改文件名大小写。"""
        if os.path.lexists(new_path):
            same_path = os.path.normcase(os.path.abspath(old_path)) == os.path.normcase(
                os.path.abspath(new_path)
            )
            if not same_path or not os.path.samefile(old_path, new_path):
                raise FileExistsError("目标文件已存在")

        # Windows 的 os.rename 支持大小写修改，且不会覆盖其他已有文件。
        os.rename(old_path, new_path)

    def _make_rename_plan(self, new_names):
        return [
            {
                "old_path": file_info["path"],
                "new_path": os.path.join(os.path.dirname(file_info["path"]), new_name),
            }
            for file_info, new_name in zip(self._get_ordered_files(), new_names)
            if file_info["name"] != new_name
        ]

    def _validate_rename_plan(self, plan):
        sources = {}
        targets = set()
        for record in plan:
            old_path, new_path = record["old_path"], record["new_path"]
            source_key, target_key = self._path_key(old_path), self._path_key(new_path)
            if source_key in sources:
                raise ValueError(f"重复选择了同一文件: {old_path}")
            if target_key in targets:
                raise ValueError(f"多个文件将使用同一个名称: {new_path}")
            identity = self._file_id(old_path)
            if "file_id" in record and record["file_id"] != identity:
                raise OSError(f"文件已被其他文件替换，不能撤销: {old_path}")
            sources[source_key] = old_path
            targets.add(target_key)

        for record in plan:
            new_path = record["new_path"]
            if os.path.lexists(new_path):
                source = sources.get(self._path_key(new_path))
                if source is None or not os.path.samefile(source, new_path):
                    raise FileExistsError(f"目标文件已存在: {new_path}")

    @staticmethod
    def _temporary_path(path):
        while True:
            temporary = os.path.join(os.path.dirname(path), f"~br{uuid4().hex[:8]}.tmp")
            if not os.path.lexists(temporary):
                return temporary

    def _run_rename_plan(self, plan):
        """先暂存再改名，支持同批名称互换；失败时尽力恢复原名。"""
        self._validate_rename_plan(plan)
        states = [
            dict(
                record,
                current_path=record["old_path"],
                file_id=self._file_id(record["old_path"]),
            )
            for record in plan
        ]
        try:
            for state in states:
                temporary = self._temporary_path(state["old_path"])
                self._rename_file(state["current_path"], temporary)
                state["current_path"] = temporary
            for state in states:
                self._rename_file(state["current_path"], state["new_path"])
                state["current_path"] = state["new_path"]
        except OSError as error:
            # 已完成的目标名可能占用其他文件的原名，先统一腾空再恢复。
            for state in states:
                if state["current_path"] == state["new_path"]:
                    try:
                        temporary = self._temporary_path(state["current_path"])
                        self._rename_file(state["current_path"], temporary)
                        state["current_path"] = temporary
                    except OSError:
                        pass
            for state in states:
                if state["current_path"] != state["old_path"]:
                    try:
                        self._rename_file(state["current_path"], state["old_path"])
                        state["current_path"] = state["old_path"]
                    except OSError:
                        pass
            remaining = [
                {
                    "old_path": state["old_path"],
                    "new_path": state["current_path"],
                    "file_id": state["file_id"],
                }
                for state in states if state["current_path"] != state["old_path"]
            ]
            raise RenameBatchError(error, remaining) from error

        return [
            {
                "old_path": state["old_path"],
                "new_path": state["new_path"],
                "file_id": state["file_id"],
            }
            for state in states
        ]

    def _update_file_paths(self, records):
        # 一次性匹配原路径，避免名称互换时把同一项更新两次。
        paths = {self._path_key(record["old_path"]): record["new_path"] for record in records}
        for file_info in self.files:
            new_path = paths.get(self._path_key(file_info["path"]))
            if new_path is not None:
                file_info.update(
                    path=new_path,
                    name=os.path.basename(new_path),
                    dir=os.path.dirname(new_path),
                )

    @staticmethod
    def _batch_error_message(error):
        if error.remaining:
            paths = "\n".join(record["new_path"] for record in error.remaining)
            return f"{error}\n\n部分文件未能恢复原名，已保留撤销记录，可解除占用后重试。文件当前位置:\n{paths}"
        return f"{error}\n\n本次操作未完成，已恢复原文件名。"

    def _execute_rename(self):
        """执行重命名操作"""
        if not self.files:
            messagebox.showwarning("提示", "请先选择文件夹或文件")
            return

        # 检查是否启用了任何功能
        enabled_features = [
            self.enable_reverse.get(),
            self.enable_delete_text.get(),
            self.enable_replace.get(),
            self.enable_prefix.get(),
            self.enable_suffix.get(),
            self.enable_sequence.get(),
            self.enable_regex.get(),
            self.enable_case.get(),
            self.enable_ext.get(),
        ]
        if not any(enabled_features):
            messagebox.showwarning("提示", "请至少选择一个重命名功能")
            return

        new_names = self._generate_new_names()
        if new_names is None:
            return

        plan = self._make_rename_plan(new_names)
        if not plan:
            self._update_file_tree()
            messagebox.showinfo("提示", "没有需要重命名的文件")
            return

        try:
            self._validate_rename_plan(plan)
        except (OSError, ValueError) as e:
            messagebox.showerror("无法重命名", str(e))
            return
        if not messagebox.askyesno(
            "确认", f"确定要重命名 {len(plan)} 个文件吗？"
        ):
            return

        try:
            history = self._run_rename_plan(plan)
        except RenameBatchError as e:
            if e.remaining:
                self.rename_history.append(e.remaining)
                self._update_file_paths(e.remaining)
            messagebox.showerror("重命名失败", self._batch_error_message(e))
        except (OSError, ValueError) as e:
            messagebox.showerror("重命名失败", str(e))
        else:
            self.rename_history.append(history)
            self._update_file_paths(history)
            messagebox.showinfo("完成", f"成功重命名 {len(history)} 个文件")

        self._refresh_files()

    def _undo_last_rename(self):
        """撤销上次重命名操作"""
        if not self.rename_history:
            messagebox.showinfo("提示", "没有可撤销的操作")
            return

        history = self.rename_history[-1]
        plan = [
            dict(record, old_path=record["new_path"], new_path=record["old_path"])
            for record in history
        ]
        try:
            restored = self._run_rename_plan(plan)
        except RenameBatchError as e:
            self._update_file_paths(e.remaining)
            locations = {
                self._path_key(record["old_path"]): record["new_path"]
                for record in e.remaining
            }
            for record in history:
                record["new_path"] = locations.get(self._path_key(record["new_path"]), record["new_path"])
            pending = [record for record in history if record["old_path"] != record["new_path"]]
            if pending:
                self.rename_history[-1] = pending
            else:
                self.rename_history.pop()
            messagebox.showerror("撤销失败", self._batch_error_message(e))
        except (OSError, ValueError) as e:
            messagebox.showerror("撤销失败", f"{e}\n\n已保留撤销记录，处理后可重试。")
        else:
            self.rename_history.pop()
            self._update_file_paths(restored)
            messagebox.showinfo("撤销完成", f"已撤销 {len(restored)} 个文件的重命名")

        self._refresh_files()


def main():
    root = tk.Tk()

    # 设置 DPI 感知 (Windows)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = BatchRenameApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
