import tkinter as tk
from tkinter import ttk
from modern_ui import ModernUI


class CustomDialog:
    """自定义模态对话框"""

    def __init__(
        self,
        parent,
        title="QuizUp",  # 修改默认标题
        message="操作已完成",
        yes_text="确定",
        no_text="取消",
        show_no=True,
    ):
        self.result = None  # 用于存储对话框结果 (True/False)

        # 创建对话框窗口 (Toplevel)
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        # 使用主题背景色
        self.dialog.configure(bg=ModernUI.get_theme_color("bg"))
        self.dialog.minsize(320, 160)  # 最小尺寸

        # 设置窗口位置居中于父窗口
        self.dialog.update_idletasks()  # 更新几何信息以获得准确尺寸
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # 设置模态：阻止与父窗口交互，并保持在父窗口之上
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # --- 内容区域 ---
        # 使用ttk.Frame并应用主题样式
        content_frame = ttk.Frame(self.dialog, padding="20 20 20 10", style="TFrame")
        content_frame.pack(expand=True, fill=tk.BOTH)
        content_frame.columnconfigure(0, weight=1)  # 使内容水平居中
        content_frame.rowconfigure(0, weight=1)  # 使内容垂直居中

        # 消息标签
        message_label = ttk.Label(
            content_frame,
            text=message,
            font=("微软雅黑", 11),
            wraplength=280,  # 自动换行宽度
            anchor=tk.CENTER,
            justify=tk.CENTER,
            style="TLabel",  # 应用ttk标签样式 (会自动继承主题颜色)
        )
        message_label.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        # --- 按钮区域 ---
        # 使用ttk.Frame并应用主题样式
        button_frame = ttk.Frame(self.dialog, padding="0 10 10 30", style="TFrame")
        button_frame.pack(fill=tk.X)
        # 配置列权重使内部框架居中
        button_frame.columnconfigure(0, weight=1)

        # 创建一个内部框架来容纳按钮，这个内部框架将被居中
        inner_button_frame = ttk.Frame(button_frame, style="TFrame")
        inner_button_frame.grid(row=0, column=0, pady=0)  # 放置在外部框架的中央

        # 创建按钮并添加到 inner_button_frame 中
        yes_button = ModernUI.create_rounded_button(
            inner_button_frame,  # 父容器是内部框架
            text=yes_text,
            command=self.yes_clicked,
            width=100,
            height=35,
            corner_radius=17,
            bg=ModernUI.get_theme_color("primary"),  # 使用主题主色
            hover_bg=ModernUI.get_theme_color("primary_dark"),
            fg="white",
            font=("微软雅黑", 10),
        )
        # 使用 pack 将按钮并排放置在内部框架中
        yes_button.pack(side=tk.LEFT, padx=5)

        if show_no:  # 如果需要显示“否”按钮
            no_button = ModernUI.create_rounded_button(
                inner_button_frame,  # 父容器是内部框架
                text=no_text,
                command=self.no_clicked,
                width=100,
                height=35,
                corner_radius=17,
                bg=ModernUI.get_theme_color("danger"),  # 使用主题危险色
                hover_bg=ModernUI.get_theme_color("danger_dark"),
                fg="white",
                font=("微软雅黑", 10),
            )
            no_button.pack(side=tk.LEFT, padx=5)

        # 设置默认焦点到“是”按钮
        yes_button.focus_set()

        # 绑定回车键到“是”操作，ESC键到“否”操作（如果显示）
        self.dialog.bind("<Return>", lambda e: self.yes_clicked())
        if show_no:
            self.dialog.bind("<Escape>", lambda e: self.no_clicked())

        # 禁止调整窗口大小
        self.dialog.resizable(False, False)

        # 等待窗口关闭 (阻塞父窗口直到此对话框关闭)
        self.dialog.wait_window()

    def yes_clicked(self):
        """“是”按钮点击事件"""
        self.result = True
        self.dialog.destroy()  # 关闭对话框

    def no_clicked(self):
        """“否”按钮点击事件"""
        self.result = False
        self.dialog.destroy()  # 关闭对话框
