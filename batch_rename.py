#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量文件重命名工具 v2.0
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


class BatchRenameApp:
    """批量文件重命名主应用"""

    def __init__(self, root):
        self.root = root
        self.root.title("批量文件重命名工具 v2.0")
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
            return

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
        except PermissionError:
            messagebox.showerror("错误", "没有权限访问该文件夹")
            return

        self._update_file_tree()
        self.status_var.set(f"已加载 {len(self.files)} 个文件")
        self.file_count_var.set(f"文件数: {len(self.files)}")

    def _refresh_files(self):
        """刷新文件列表"""
        if self.selection_mode == "files" and self.files:
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
            self._load_files()
            self.status_var.set("已刷新")

    def _update_file_tree(self, new_names=None):
        """更新文件树显示"""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        filtered_files = self._apply_filter(self.files)

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
            exts = [e.strip().lower() for e in ext_filter.split(",")]
            filtered = [
                f
                for f in filtered
                if any(f["name"].lower().endswith(ext) for ext in exts)
            ]

        keyword = self.filter_keyword.get().strip()
        if keyword:
            filtered = [
                f for f in filtered if keyword.lower() in f["name"].lower()
            ]

        return filtered

    def _generate_new_names(self):
        """根据当前选中的功能组合生成新文件名"""
        filtered_files = self._apply_filter(self.files)
        if not filtered_files:
            return None

        # 如果启用倒序，先反转列表
        if self.enable_reverse.get():
            filtered_files = filtered_files[::-1]

        new_names = []

        for f in filtered_files:
            name = f["name"]
            base, ext = os.path.splitext(name)

            # 1. 删除指定文字
            if self.enable_delete_text.get():
                delete_text = self.entry_delete_text.get().strip()
                if delete_text:
                    base = base.replace(delete_text, "")
                    ext = ext  # 扩展名不变

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
                try:
                    start_num = int(self.entry_start_num.get() or 1)
                    digits = int(self.entry_digits.get() or 3)
                except ValueError:
                    messagebox.showerror("错误", "起始序号和位数必须是数字！")
                    return None
                idx = filtered_files.index(f)
                num = str(start_num + idx).zfill(digits)
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
                    except re.error as e:
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
                    words = re.split(r"[-_\s]+", base)
                    base = words[0].lower() + "".join(w.capitalize() for w in words[1:])

            # 8. 修改扩展名
            if self.enable_ext.get():
                new_ext = self.entry_new_ext.get().strip()
                if new_ext:
                    if not new_ext.startswith("."):
                        new_ext = "." + new_ext
                    ext = new_ext

            new_names.append(base + ext)

        return new_names

    def _preview_rename(self):
        """预览重命名效果"""
        new_names = self._generate_new_names()
        if new_names is None:
            return

        self._update_file_tree(new_names)
        self.status_var.set("预览模式 - 绿色背景表示将被修改的文件")

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

        filtered_files = self._apply_filter(self.files)

        # 如果启用倒序，需要对应调整
        if self.enable_reverse.get():
            filtered_files = filtered_files[::-1]

        # 检查是否有变更
        has_changes = any(
            new != old["name"] for new, old in zip(new_names, filtered_files)
        )
        if not has_changes:
            messagebox.showinfo("提示", "没有需要重命名的文件")
            return

        # 确认操作
        change_count = sum(
            1
            for new, old in zip(new_names, filtered_files)
            if new != old["name"]
        )
        if not messagebox.askyesno(
            "确认", f"确定要重命名 {change_count} 个文件吗？"
        ):
            return

        # 执行重命名
        success_count = 0
        errors = []
        history = []

        for new_name, file_info in zip(new_names, filtered_files):
            old_name = file_info["name"]
            if new_name == old_name:
                continue

            old_path = file_info["path"]
            if self.selection_mode == "files":
                file_dir = file_info.get("dir", os.path.dirname(old_path))
                new_path = os.path.join(file_dir, new_name)
            else:
                new_path = os.path.join(self.current_dir, new_name)

            if os.path.exists(new_path) and old_path != new_path:
                errors.append(f"跳过 {old_name}: 目标文件已存在")
                continue

            try:
                history.append({"old_path": old_path, "new_path": new_path})
                os.rename(old_path, new_path)
                success_count += 1
            except Exception as e:
                errors.append(f"重命名 {old_name} 失败: {str(e)}")

        if history:
            self.rename_history.append(history)

        result_msg = f"成功重命名 {success_count} 个文件"
        if errors:
            result_msg += f"\n\n失败 {len(errors)} 个:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                result_msg += f"\n... 还有 {len(errors) - 10} 个错误"

        if success_count > 0:
            messagebox.showinfo("完成", result_msg)
        else:
            messagebox.showerror("失败", result_msg)

        self._refresh_files()

    def _undo_last_rename(self):
        """撤销上次重命名操作"""
        if not self.rename_history:
            messagebox.showinfo("提示", "没有可撤销的操作")
            return

        history = self.rename_history.pop()
        success_count = 0
        errors = []

        for record in history:
            try:
                if os.path.exists(record["new_path"]):
                    os.rename(record["new_path"], record["old_path"])
                    success_count += 1
            except Exception as e:
                errors.append(f"撤销失败: {str(e)}")

        if success_count > 0:
            messagebox.showinfo("撤销完成", f"已撤销 {success_count} 个文件的重命名")
        if errors:
            messagebox.showerror("错误", "\n".join(errors))

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
