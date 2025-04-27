import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
import random
from datetime import datetime
from question_bank import QuestionBank
from modern_ui import ModernUI, RoundedButton
from custom_dialog import CustomDialog


class QuizApp:
    """主应用类"""

    def __init__(self, root):
        self.root = root
        self.root.title("QuizUp")  # 修改程序标题

        # 应用现代UI主题和样式
        ModernUI.set_theme(root)

        # 绑定主题切换事件，用于更新非ttk控件或特殊控件
        self.root.bind("<<ThemeChanged>>", self.on_theme_changed)

        # 尝试设置应用图标
        try:
            # 获取资源路径 (适配打包)
            base_dir = getattr(
                sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
            )
            icon_path = os.path.join(base_dir, "QuizUp_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # 打包时忽略图标加载错误

        # 设置窗口大小
        window_width = 900
        window_height = 650

        # 获取屏幕尺寸
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # 计算窗口居中的位置，y坐标向上偏移屏幕高度的5%
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2 - int(screen_height * 0.05)

        # 设置窗口大小和位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 设置默认背景色 (虽然set_theme会做，这里可以保留作为初始设置)
        self.root.configure(bg=ModernUI.get_theme_color("bg"))

        # 字体定义
        self.default_font = ("微软雅黑", 11)
        self.chapter_font = ("微软雅黑", 16, "bold")
        self.notice_font = ("微软雅黑", 13)
        self.question_font = ("微软雅黑", 13)
        self.option_font = ("微软雅黑", 11)  # 选项专用字体

        # 初始化变量
        self.answer_var = tk.StringVar()  # 用于单选题和判断题
        self.answer_vars = []  # 用于多选题 (存储BooleanVar)
        self.choice_option_labels = []  # 存储单选题选项标签的引用
        self.multi_option_labels = []  # 存储多选题选项标签的引用
        self.config = self.load_config()  # 加载配置 (如上次文件路径)

        # 添加动画效果的变量
        self.fade_animation = None  # 用于存储当前动画任务的ID
        self.animation_running = False  # 动画是否正在运行的标志
        self.last_question = None  # 上一题内容 (用于动画对比)
        self.rounded_buttons = []  # 用于存储所有 RoundedButton 实例
        self.answered_counts = {}  # 用于存储每章已答题目数 {chapter_index: count}

        # 初始化答题统计数据
        # 结构: { chapter_index: { "判断题": {"answered": n, "correct": m}, ... }, ... }
        self.stats = {}

        self.question_bank = None  # 当前加载的题库对象
        self.current_question = None  # 当前显示的问题数据
        self.current_chapter_index = 0  # 当前章节索引
        self.shown_questions = (
            set()
        )  # 记录已显示过的题目 (chapter_index, question_index)
        self.type_counts = {  # 记录每种题型在本章显示的次数 (用于可能的加权随机)
            "判断题": 0,
            "单选题": 0,
            "多选题": 0,
        }

        # 创建主框架 (使用ttk.Frame并应用样式)
        self.main_frame = ttk.Frame(self.root, padding="15 15 15 15", style="TFrame")
        self.main_frame.pack(expand=True, fill="both")
        self.main_frame.rowconfigure(0, weight=1)  # 让内容框架占据主要空间
        self.main_frame.columnconfigure(0, weight=1)

        # 创建内容框架 (用于放置开始界面或答题界面)
        self.content_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.content_frame.grid(row=0, column=0, sticky="nsew")  # 使用grid布局

        # 创建开发者标签
        self.author_label = ttk.Label(
            self.main_frame,
            text="开发者：Dabbler",
            font=("微软雅黑", 9),
            style="TLabel",  # 使用基础标签样式
        )
        # 将开发者标签放置在主框架右下角
        self.author_label.grid(row=1, column=0, sticky="se", padx=5, pady=5)
        # 初始化时设置颜色
        self.author_label.configure(
            foreground=ModernUI.get_theme_color("text_secondary")
        )

        # 创建开始界面
        self.create_start_screen()

    def on_theme_changed(self, event=None):
        """处理主题变更事件，更新需要手动调整颜色的控件"""
        # 更新根窗口背景 (apply_theme已做，但再次确认无妨)
        self.root.configure(bg=ModernUI.get_theme_color("bg"))

        # 更新ttk样式以反映新主题 (apply_theme已做)
        # ModernUI.style_widgets(self.root) # 无需重复调用

        # 更新作者标签颜色 (它是ttk.Label，但前景设为次要文本色)
        self.author_label.configure(
            foreground=ModernUI.get_theme_color("text_secondary")
        )

        # 更新所有RoundedButton按钮的颜色
        self.update_rounded_buttons()  # 现在会使用优化后的方法

        # 如果当前显示的是问题页面，更新问题卡片内的非ttk或特殊控件
        if hasattr(self, "question_text") and self.question_text.winfo_exists():
            # 更新题目文本区域 (tk.Text) 的背景和前景
            bg_color = ModernUI.get_theme_color("card_bg")
            fg_color = ModernUI.get_theme_color("text")
            self.question_text.configure(bg=bg_color, fg=fg_color)

            # 更新题型标签 (ttk.Label，但背景色需明确为卡片背景)
            if hasattr(self, "question_type_label"):
                self.question_type_label.configure(
                    background=bg_color, foreground=ModernUI.get_theme_color("primary")
                )

            # 更新选项区域 (ttk控件样式已在style_widgets中更新)
            # 需要手动更新选项 Label 的颜色
            if hasattr(self, "options_frame") and self.options_frame.winfo_exists():
                card_bg_color = ModernUI.get_theme_color("card_bg")
                text_color = ModernUI.get_theme_color("text")
                # 更新选项框架背景
                self.options_frame.configure(style="Card.TFrame")  # 确保背景是卡片色
                # 更新判断题、单选、多选框架背景
                for frame in [self.judge_frame, self.choice_frame, self.multi_frame]:
                    if frame.winfo_exists():
                        frame.configure(style="Card.TFrame")
                        # 遍历子控件更新 Label 颜色
                        for widget in frame.winfo_children():
                            if isinstance(widget, ttk.Frame):  # 选项行框架
                                widget.configure(style="Card.TFrame")
                                for child in widget.winfo_children():
                                    if isinstance(child, ttk.Label):
                                        # 更新选项 Label 颜色
                                        child.configure(
                                            background=card_bg_color,
                                            foreground=text_color,
                                        )
                                    elif isinstance(
                                        child, (ttk.Radiobutton, ttk.Checkbutton)
                                    ):
                                        # ttk 控件理论上会自动更新，但可以强制指定背景
                                        child.configure(
                                            style=child.winfo_class()
                                        )  # 重新应用样式
                            elif isinstance(
                                widget, (ttk.Radiobutton, ttk.Checkbutton)
                            ):  # 判断题的直接子控件
                                widget.configure(
                                    style=widget.winfo_class()
                                )  # 重新应用样式

            # 更新进度标签颜色 (ttk.Label，但前景设为次要文本色)
            if hasattr(self, "progress_label") and self.progress_label.winfo_exists():
                self.progress_label.configure(
                    foreground=ModernUI.get_theme_color("text_secondary")
                )

    def update_rounded_buttons(self):
        """更新应用中所有RoundedButton实例的颜色以匹配当前主题 (优化版)"""
        for button in self.rounded_buttons:
            # 检查按钮是否存在，因为屏幕切换时旧按钮可能已被销毁
            if not button.winfo_exists():
                continue

            # 获取按钮的角色
            role = button.color_role

            # 判断按钮是否禁用
            if button.is_disabled:
                # 禁用状态使用中性色
                button.bg = ModernUI.get_theme_color("neutral")
                button.fg = ModernUI.get_theme_color("text_secondary")
                button.hover_bg = button.bg  # 禁用时悬停色不变
                button.itemconfig(button.rect, fill=button.bg, outline=button.bg)
                button.itemconfig(button.text, fill=button.fg)
            else:
                # 根据按钮角色从当前主题获取颜色
                role_bg = ModernUI.get_theme_color(role)
                dark_role = role if role.endswith("_dark") else f"{role}_dark"
                role_hover_bg = (
                    ModernUI.get_theme_color(dark_role)
                    if dark_role in ModernUI.THEMES[ModernUI.current_theme]
                    else role_bg
                )

                button.bg = role_bg
                button.hover_bg = role_hover_bg
                # fg 通常是白色，除非特殊指定
                button.fg = getattr(button, "_original_fg", "white")

                # 根据当前状态（是否悬停/按下）更新显示颜色
                # 检查鼠标是否在按钮上 (仅在窗口有焦点时有效)
                is_hovering = (
                    button.winfo_containing(
                        button.winfo_pointerx(), button.winfo_pointery()
                    )
                    == button
                    and self.root.focus_get() is not None
                )
                current_bg = (
                    button.hover_bg if button.is_pressed or is_hovering else button.bg
                )
                button.itemconfig(button.rect, fill=current_bg, outline=current_bg)
                button.itemconfig(button.text, fill=button.fg)

            # 更新Canvas本身的背景色以匹配父容器
            try:
                # 尝试获取父容器的背景色，如果失败则使用全局背景色
                parent_bg = button.master.cget("background")
            except tk.TclError:
                parent_bg = ModernUI.get_theme_color("bg")
            button.configure(bg=parent_bg)

            # 更新阴影颜色
            if hasattr(button, "shadow"):
                # 阴影颜色应与按钮所在的Canvas背景一致
                button.itemconfig(button.shadow, fill=parent_bg)

    def load_config(self):
        """加载配置文件 (例如上次打开的文件路径)"""
        # 获取资源路径 (适配打包)
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "quiz_config.json")
        default_config = {"last_file": "", "recent_files": []}  # 默认配置

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # 简单验证配置格式
                    if (
                        isinstance(config, dict)
                        and "last_file" in config
                        and "recent_files" in config
                    ):
                        return config
                    else:
                        return default_config  # 格式不符，返回默认
            except (json.JSONDecodeError, IOError):
                return default_config  # 加载失败，返回默认
        return default_config  # 配置文件不存在，返回默认

    def save_config(self):
        """保存配置文件"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "quiz_config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                # ensure_ascii=False 保证中文能正确写入
                # indent=2 使json文件更易读
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except IOError:
            pass  # 忽略保存配置失败

    def create_start_screen(self):
        """创建开始界面"""
        # 清除内容框架中的所有组件
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.configure(style="TFrame")  # 确保是基础样式
        self.rounded_buttons.clear()  # 清空旧按钮列表

        # 创建容器框架 (用于居中内容)
        center_frame = ttk.Frame(self.content_frame, padding="20 40", style="TFrame")
        # 使用 place 将其放置在内容框架的中心偏上位置
        center_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        # 标题标签和图标框架
        title_frame = ttk.Frame(center_frame, style="TFrame")
        title_frame.pack(pady=(0, 25))

        # 图标标签
        try:
            # 获取脚本所在目录
            base_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_dir, "QuizUp_icon.png")
            if os.path.exists(icon_path):
                icon_image = tk.PhotoImage(file=icon_path)
                icon_label = ttk.Label(
                    title_frame,
                    image=icon_image,
                    style="TLabel",  # 使用基础标签样式
                )
                icon_label.image = icon_image  # 防止图像被垃圾回收
                icon_label.pack(side=tk.TOP)
        except Exception:
            pass  # 忽略图标加载错误

        # 标题标签
        title_label = ttk.Label(
            title_frame,
            text="QuizUp",  # 修改标题
            font=("微软雅黑", 26, "bold"),
            style="Header.TLabel",  # 使用标题样式
        )
        title_label.pack(side=tk.TOP)  # 标题靠左，右侧留出空间

        # 公告/说明标签
        notice_text = (
            "本程序为题库复习程序\n选择题库文件开始答题\n支持标准格式的 .txt 文件"
        )
        notice_label = ttk.Label(
            center_frame,
            text=notice_text,
            font=self.notice_font,
            justify=tk.CENTER,  # 文本居中对齐
            style="TLabel",  # 使用基础标签样式
        )
        notice_label.pack(pady=(0, 35))

        # 按钮框架
        button_frame = ttk.Frame(center_frame, style="TFrame")
        button_frame.pack(pady=15)

        # 选择题库按钮
        select_button = ModernUI.create_rounded_button(
            button_frame,
            text="选择题库文件",
            command=self.select_question_bank,
            width=200,
            height=50,
            corner_radius=25,
            # bg=ModernUI.get_theme_color("primary"), # 由 color_role 决定
            # hover_bg=ModernUI.get_theme_color("primary_dark"),
            color_role="primary",  # 指定角色
            fg="white",
            font=("微软雅黑", 14, "bold"),
        )
        select_button.pack(pady=12)
        self.rounded_buttons.append(select_button)  # 添加到列表

        # 继续上次学习按钮 (如果配置文件中有记录且文件存在)
        last_file = self.config.get("last_file")
        if last_file and os.path.exists(last_file):
            last_file_name = os.path.basename(last_file)
            # 限制显示的文件名长度，避免按钮过长
            display_name = (
                last_file_name
                if len(last_file_name) < 30
                else last_file_name[:27] + "..."  # 超长则截断并加省略号
            )
            continue_button = ModernUI.create_rounded_button(
                button_frame,
                text=f"继续: {display_name}",
                # 使用 lambda 传递参数，确保每次点击都用最新的 lf 值
                command=lambda lf=last_file: self.start_quiz(lf),
                width=250,  # 按钮稍宽以容纳文件名
                height=40,
                corner_radius=20,
                # bg=ModernUI.get_theme_color("success"), # 由 color_role 决定
                # hover_bg=ModernUI.get_theme_color("success_dark"),
                color_role="success",  # 指定角色
                fg="white",
                font=("微软雅黑", 11),
            )
            continue_button.pack(pady=12)
            self.rounded_buttons.append(continue_button)  # 添加到列表

    def select_question_bank(self):
        """打开文件对话框选择题库文件"""
        # 初始目录设为脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = filedialog.askopenfilename(
            initialdir=current_dir,
            title="选择题库文件",
            filetypes=(("文本文件", "*.txt"), ("所有文件", "*.*")),  # 文件类型过滤器
        )

        if file_path:  # 如果用户选择了文件
            # 更新最近使用的文件列表
            recent_files = self.config.get("recent_files", [])
            if file_path in recent_files:
                recent_files.remove(file_path)  # 如果已存在，先移除
            recent_files.insert(0, file_path)  # 添加到列表开头
            # 保留最近10个文件记录
            self.config["recent_files"] = recent_files[:10]

            # 更新最后使用的文件
            self.config["last_file"] = file_path
            self.save_config()  # 保存配置

            # 开始答题
            self.start_quiz(file_path)

    def start_quiz(self, file_path=None):
        """根据提供的文件路径开始答题"""
        if not file_path:
            messagebox.showerror("错误", "未指定题库文件路径。")
            self.create_start_screen()  # 返回开始界面
            return

        # 初始化题库对象
        self.question_bank = QuestionBank()
        # 加载题库文件，如果失败则显示错误并返回开始界面
        if not self.question_bank.load_question_bank(file_path):
            # 错误消息已在 load_question_bank 中显示
            self.create_start_screen()
            return

        # 重置答题状态
        self.current_chapter_index = 0
        self.shown_questions = set()
        self.type_counts = {"判断题": 0, "单选题": 0, "多选题": 0}
        self.stats = {}  # 重置统计数据
        self.answered_counts = {}  # 重置章节计数
        # 初始化第一章计数 (如果题库非空)
        if self.question_bank and self.question_bank.chapters:
            self.answered_counts[0] = 0

        # 更新窗口标题以包含题库名称
        self.root.title(f"题库复习 - {self.question_bank.title}")

        # 创建答题界面
        self.create_quiz_screen()

        # 显示第一题
        self.show_chapter_question()

    def create_quiz_screen(self):
        """创建答题主界面"""
        # 清除内容框架
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.configure(style="TFrame")
        self.rounded_buttons.clear()  # 清空旧按钮列表

        # --- 顶部面板 (章节标题和控制按钮) ---
        top_panel = ttk.Frame(self.content_frame, padding="0 10 0 10", style="TFrame")
        top_panel.pack(fill=tk.X)

        # 章节标签
        self.chapter_label = ttk.Label(
            top_panel,
            text="当前章节: ...",  # 初始文本
            font=self.chapter_font,
            style="Chapter.TLabel",  # 应用章节标题样式
        )
        self.chapter_label.pack(side=tk.LEFT, padx=(10, 0))

        # 右侧控制按钮框架
        control_frame = ttk.Frame(top_panel, style="TFrame")
        control_frame.pack(side=tk.RIGHT, padx=(0, 10))

        # 主题切换按钮
        theme_icon = "🌙" if ModernUI.current_theme == "light" else "🔆"
        theme_button = ModernUI.create_rounded_button(
            control_frame,
            text=theme_icon,  # 显示图标
            command=lambda: [  # 点击时执行两个动作
                ModernUI.toggle_theme(self.root),  # 切换主题
                self.update_theme_button_icon(),  # 更新按钮图标
            ],
            width=40,
            height=30,
            corner_radius=15,
            # bg=ModernUI.get_theme_color("neutral"), # 由 color_role 决定
            # hover_bg=ModernUI.get_theme_color("neutral_dark"),
            color_role="neutral",  # 指定角色
            fg="white",
            font=("微软雅黑", 12),  # 图标字体稍大
        )
        self.theme_button = theme_button  # 保存引用以便更新图标
        theme_button.pack(side=tk.RIGHT, padx=5)
        self.rounded_buttons.append(theme_button)  # 添加到列表

        # 答题统计按钮
        self.stats_button = ModernUI.create_rounded_button(
            control_frame,
            text="答题统计",
            command=self.show_stats,
            width=90,
            height=30,
            corner_radius=15,
            # bg=ModernUI.get_theme_color("warning"), # 由 color_role 决定
            # hover_bg=ModernUI.get_theme_color("warning_dark"),
            color_role="warning",  # 指定角色
            fg="white",
            font=("微软雅黑", 9),
        )
        self.stats_button.pack(side=tk.RIGHT, padx=5)
        self.rounded_buttons.append(self.stats_button)  # 添加到列表

        # 返回主菜单按钮
        home_button = ModernUI.create_rounded_button(
            control_frame,
            text="主菜单",
            command=self.create_start_screen,  # 返回开始界面
            width=90,
            height=30,
            corner_radius=15,
            # bg=ModernUI.get_theme_color("neutral"), # 由 color_role 决定
            # hover_bg=ModernUI.get_theme_color("neutral_dark"),
            color_role="neutral",  # 指定角色
            fg="white",
            font=("微软雅黑", 9),
        )
        home_button.pack(side=tk.RIGHT, padx=5)
        self.rounded_buttons.append(home_button)  # 添加到列表

        # --- 问题卡片面板 ---
        # 外层容器用于可能的阴影或边距效果
        card_container = ttk.Frame(self.content_frame, style="TFrame")
        card_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # 问题卡片主体 (使用Card样式)
        question_panel = ttk.Frame(card_container, style="Card.TFrame", padding="20 15")
        question_panel.pack(fill=tk.BOTH, expand=True)

        # 配置卡片内部行列权重
        question_panel.rowconfigure(0, weight=0)  # 题型标签 (固定高度)
        question_panel.rowconfigure(1, weight=3)  # 问题文本区域 (可扩展)
        question_panel.rowconfigure(2, weight=4)  # 选项框架 (可扩展，权重稍大)
        question_panel.rowconfigure(3, weight=0)  # 进度条框架 (固定高度)
        question_panel.rowconfigure(4, weight=0)  # 下一题按钮框架 (固定高度)
        question_panel.columnconfigure(0, weight=1)  # 列宽占满

        # 题目类型标签
        self.question_type_label = ttk.Label(
            question_panel,
            text="【题型】",
            style="QuestionType.TLabel",  # 应用题型样式
            # 背景色由样式自动处理
        )
        self.question_type_label.grid(row=0, column=0, sticky="nw", pady=(0, 5))

        # 题目显示区域 (使用tk.Text)
        # 外部套一层Frame是为了更好地控制边距和样式一致性
        text_frame = ttk.Frame(question_panel, style="Card.TFrame", borderwidth=0)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 5))
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        # 题目文本控件 (tk.Text)
        self.question_text = tk.Text(
            text_frame,
            wrap=tk.WORD,  # 自动换行
            font=self.question_font,
            bg=ModernUI.get_theme_color("card_bg"),  # 背景设为卡片背景
            fg=ModernUI.get_theme_color("text"),  # 前景设为文本颜色
            bd=0,  # 无边框
            height=2.5,  # 初始高度 (大致行数)
            relief=tk.FLAT,  # 扁平样式
            state="disabled",  # 初始不可编辑
            highlightthickness=0,  # 无焦点高亮边框
            cursor="arrow",  # 使用箭头光标
        )
        self.question_text.grid(row=0, column=0, sticky="nsew")

        # 选项框架 (用于容纳不同题型的选项)
        self.options_frame = ttk.Frame(
            question_panel, style="Card.TFrame", borderwidth=0
        )
        self.options_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 5))
        self.options_frame.columnconfigure(0, weight=1)  # 使选项内容水平扩展

        # 创建答案选项按钮/标签 (初始隐藏)
        self.create_answer_buttons()

        # 进度指示器框架
        self.progress_frame = ttk.Frame(question_panel, style="TFrame")
        self.progress_frame.grid(
            row=3, column=0, sticky="ew", pady=(0, 5)
        )  # 减少底部pady
        self.progress_frame.columnconfigure(0, weight=1)
        # 配置行权重
        self.progress_frame.rowconfigure(0, weight=0)  # 进度条
        self.progress_frame.rowconfigure(1, weight=0)  # 进度标签

        # 进度条
        self.progress = ttk.Progressbar(
            self.progress_frame,
            style="TProgressbar",
            orient="horizontal",
            length=200,
            mode="determinate",
        )
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 2))  # 增加底部pady

        # 进度标签
        self.progress_label = ttk.Label(
            self.progress_frame,
            text="已答: 0 / 总数: 0",  # 初始文本
            style="TLabel",  # 使用基础标签样式
            font=("微软雅黑", 8),  # 字体稍小
            foreground=ModernUI.get_theme_color("text_secondary"),  # 次要文本色
        )
        self.progress_label.grid(
            row=1, column=0, sticky="w", padx=5
        )  # 放置在进度条下方靠左

        # 下一题按钮框架
        next_button_frame = ttk.Frame(
            question_panel, style="Card.TFrame", borderwidth=0
        )
        next_button_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        next_button_frame.columnconfigure(0, weight=1)  # 用于居中按钮

        # 下一题按钮
        self.next_button = ModernUI.create_rounded_button(
            next_button_frame,
            text="下一题",
            command=self.next_question,
            width=160,
            height=40,
            corner_radius=20,
            # bg=ModernUI.get_theme_color("secondary"), # 由 color_role 决定
            # hover_bg=ModernUI.get_theme_color("secondary_dark"),
            color_role="secondary",  # 指定角色
            fg="white",
            font=("微软雅黑", 12, "bold"),
        )
        self.next_button.grid(row=0, column=0, pady=5)  # 放置在框架中央
        self.rounded_buttons.append(self.next_button)  # 添加到列表

        # --- 底部章节切换 ---
        bottom_frame = ttk.Frame(self.content_frame, padding="10 10", style="TFrame")
        bottom_frame.pack(fill=tk.X)
        # 配置列权重使按钮分布在两侧
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)

        # 上一章按钮
        self.prev_chapter_button = ModernUI.create_rounded_button(
            bottom_frame,
            text="← 上一章",
            command=self.prev_chapter,
            width=110,
            height=35,
            corner_radius=17,
            # bg=ModernUI.get_theme_color("primary"), # 由 color_role 决定
            # hover_bg=ModernUI.get_theme_color("primary_dark"),
            color_role="primary",  # 指定角色
            fg="white",
            font=("微软雅黑", 10),
        )
        self.prev_chapter_button.grid(row=0, column=0, sticky="e", padx=10)  # 靠右对齐
        self.rounded_buttons.append(self.prev_chapter_button)  # 添加到列表

        # 下一章按钮
        self.next_chapter_button = ModernUI.create_rounded_button(
            bottom_frame,
            text="下一章 →",
            command=self.next_chapter,
            width=110,
            height=35,
            corner_radius=17,
            # bg=ModernUI.get_theme_color("primary"), # 由 color_role 决定
            # hover_bg=ModernUI.get_theme_color("primary_dark"),
            color_role="primary",  # 指定角色
            fg="white",
            font=("微软雅黑", 10),
        )
        self.next_chapter_button.grid(row=0, column=1, sticky="w", padx=10)  # 靠左对齐
        self.rounded_buttons.append(self.next_chapter_button)  # 添加到列表

    def create_answer_buttons(self):
        """创建用于显示答案选项的ttk控件 (初始隐藏)"""
        # 清除旧的选项标签引用
        self.choice_option_labels = []
        self.multi_option_labels = []

        # 共享的样式参数
        style_args = {"style": "TRadiobutton"}  # 单选按钮样式
        check_style_args = {"style": "TCheckbutton"}  # 复选框样式
        label_style_args = {
            "style": "Option.TLabel",
            "font": self.option_font,
        }  # 选项标签样式

        # --- 判断题选项 (A/B) ---
        self.judge_frame = ttk.Frame(self.options_frame, style="Card.TFrame")
        # 使用pack布局，稍后根据题目类型决定是否显示
        self.judge_frame.pack(fill=tk.X, pady=5)

        rb_true = ttk.Radiobutton(
            self.judge_frame,
            text="对 (A)",
            variable=self.answer_var,  # 绑定到单选变量
            value="A",  # 选中时的值
            **style_args,
        )
        rb_true.pack(side=tk.LEFT, padx=30, pady=5, expand=True)  # 水平排列，扩展填充
        # 绑定点击事件确保单击即选中 (有时ttk默认行为可能不符合预期)
        rb_true.bind("<Button-1>", lambda e: self.answer_var.set("A"))

        rb_false = ttk.Radiobutton(
            self.judge_frame,
            text="错 (B)",
            variable=self.answer_var,
            value="B",
            **style_args,
        )
        rb_false.pack(side=tk.LEFT, padx=30, pady=5, expand=True)
        rb_false.bind("<Button-1>", lambda e: self.answer_var.set("B"))

        # --- 单选题选项 (A/B/C/D) ---
        self.choice_frame = ttk.Frame(self.options_frame, style="Card.TFrame")
        self.choice_frame.pack(fill=tk.X)  # 使用pack布局

        for i, opt in enumerate(["A", "B", "C", "D"]):
            # 每行一个选项，包含Radiobutton和Label
            option_row = ttk.Frame(self.choice_frame, style="Card.TFrame")
            option_row.pack(fill=tk.X, pady=1, padx=10)  # 垂直排列，左右留边距

            rb = ttk.Radiobutton(
                option_row,
                text=f"{opt}.",  # 显示 "A." "B." 等
                variable=self.answer_var,  # 绑定到单选变量
                value=opt,  # 选中时的值
                **style_args,
            )
            rb.grid(
                row=0, column=0, sticky="w", padx=(15, 5), pady=5
            )  # 左对齐，增加左内边距
            # 绑定点击事件
            rb.bind("<Button-1>", lambda e, v=opt: self.answer_var.set(v))

            option_label = ttk.Label(
                option_row,
                text=f"选项 {opt}",  # 初始文本
                wraplength=700,  # 自动换行宽度
                **label_style_args,
            )
            option_label.grid(
                row=0, column=1, sticky="w", pady=5
            )  # 紧随Radiobutton之后，左对齐
            # 点击标签也能选中对应的Radiobutton
            option_label.bind("<Button-1>", lambda e, v=opt: self.answer_var.set(v))

            self.choice_option_labels.append(
                option_label
            )  # 保存标签引用，以便后续更新文本
            option_row.columnconfigure(1, weight=1)  # 让标签列可以扩展宽度

        # --- 多选题选项 (A/B/C/D) ---
        self.multi_frame = ttk.Frame(self.options_frame, style="Card.TFrame")
        self.multi_frame.pack(fill=tk.X)  # 使用pack布局
        self.answer_vars = []  # 重置多选题的变量列表

        for i, opt in enumerate(["A", "B", "C", "D"]):
            var = tk.BooleanVar(value=False)  # 每个选项一个布尔变量
            self.answer_vars.append(var)

            # 每行一个选项，包含Checkbutton和Label
            option_row = ttk.Frame(self.multi_frame, style="Card.TFrame")
            option_row.pack(fill=tk.X, pady=1, padx=10)

            cb = ttk.Checkbutton(
                option_row,
                text=f"{opt}.",  # 显示 "A." "B." 等
                variable=var,  # 绑定到对应的布尔变量
                **check_style_args,
            )
            cb.grid(
                row=0, column=0, sticky="w", padx=(15, 5), pady=5
            )  # 左对齐，增加左内边距

            option_label = ttk.Label(
                option_row,
                text=f"选项 {opt}",  # 初始文本
                wraplength=700,  # 自动换行宽度
                **label_style_args,
            )
            option_label.grid(
                row=0, column=1, sticky="w", pady=5
            )  # 紧随Checkbutton之后，左对齐
            # 点击标签也能切换对应的Checkbutton状态
            option_label.bind(
                "<Button-1>", lambda e, c=cb: c.invoke()
            )  # invoke()模拟点击

            self.multi_option_labels.append(option_label)  # 保存标签引用
            option_row.columnconfigure(1, weight=1)  # 让标签列可以扩展宽度

        # 初始状态下隐藏所有选项框架
        self.judge_frame.pack_forget()
        self.choice_frame.pack_forget()
        self.multi_frame.pack_forget()

    def show_chapter_question(self):
        """根据当前章节索引，选择并显示一个题目"""
        if not self.question_bank or not self.question_bank.chapters:
            messagebox.showerror("错误", "题库未加载或为空！")
            self.create_start_screen()
            return

        # 检查是否已完成所有章节
        if self.current_chapter_index >= len(self.question_bank.chapters):
            # 使用自定义对话框提示
            dialog = CustomDialog(
                self.root,
                title="完成",
                message="已完成所有章节！是否重新开始？",
                yes_text="重新开始",
                no_text="返回主菜单",
            )
            if dialog.result:  # 如果用户选择“重新开始”
                self.current_chapter_index = 0
                self.shown_questions.clear()
                self.type_counts = {"判断题": 0, "单选题": 0, "多选题": 0}
                self.stats = {}  # 清空统计
                self.show_chapter_question()  # 显示第一章第一题
            else:  # 用户选择“返回主菜单”
                self.create_start_screen()
            return

        # 获取当前章节的所有问题
        current_chapter_questions = self.question_bank.chapters[
            self.current_chapter_index
        ]
        # 处理空章节的情况
        if not current_chapter_questions:
            messagebox.showinfo(
                "提示", f"第 {self.current_chapter_index + 1} 章没有题目，跳至下一章。"
            )
            self.next_chapter()  # 自动跳到下一章
            return

        # --- 问题选择逻辑 ---
        # 找出本章尚未显示过的问题索引
        available_indices = [
            i
            for i, q in enumerate(current_chapter_questions)
            if (self.current_chapter_index, i) not in self.shown_questions
        ]

        # 如果本章所有问题都已显示过
        if not available_indices:
            # --- 在显示对话框前，更新进度条到100% ---
            total_questions_in_chapter = len(current_chapter_questions)
            if total_questions_in_chapter > 0:
                # 确保 answered_counts 反映的是已完成所有题目
                # 注意：此时 answered_counts 应该是 total_questions_in_chapter
                # 如果不是，可能需要检查 next_question 中的计数逻辑
                answered_in_chapter = self.answered_counts.get(
                    self.current_chapter_index, 0
                )
                # 强制设置为总数，以防万一计数有误
                answered_in_chapter = total_questions_in_chapter

                self.progress.configure(value=100)
                self.progress_label.config(
                    text=f"已答: {answered_in_chapter} / 总数: {total_questions_in_chapter}"
                )
                self.root.update_idletasks()  # 强制更新UI显示进度条变化
            # --- 更新结束 ---

            is_last_chapter = (
                self.current_chapter_index >= len(self.question_bank.chapters) - 1
            )
            dialog_title = "完成" if is_last_chapter else "章节完成"
            dialog_message = (
                f"您已完成所有题目！\n是否重新开始答题？"
                if is_last_chapter
                else f"第 {self.current_chapter_index + 1} 章题目已完成！\n是否进入下一章？"
            )
            dialog_yes_text = "重新开始" if is_last_chapter else "下一章"

            # 弹出对话框询问操作
            dialog = CustomDialog(
                self.root,
                title=dialog_title,
                message=dialog_message,
                yes_text=dialog_yes_text,
                no_text="返回主菜单",
            )
            if dialog.result:  # 用户选择“下一章”或“重新开始”
                if is_last_chapter:
                    # 重新开始答题
                    self.current_chapter_index = 0
                    self.shown_questions.clear()
                    self.type_counts = {"判断题": 0, "单选题": 0, "多选题": 0}
                    self.stats = {}  # 清空统计
                    self.show_chapter_question()
                else:
                    # 进入下一章
                    self.next_chapter()
            else:  # 用户选择“返回主菜单”
                self.create_start_screen()
            return

        # --- 从可用问题中随机选择一个 ---
        # 可以加入基于 type_counts 的加权随机逻辑，优先显示做得少的题型
        # 目前使用简单随机选择
        selected_index = random.choice(available_indices)
        question_data = current_chapter_questions[selected_index]
        self.current_question = question_data  # 存储当前问题数据

        # 将选中的问题加入已显示集合
        question_identifier = (self.current_chapter_index, selected_index)
        self.shown_questions.add(question_identifier)  # 仅添加记录

        # 更新本章该题型的显示次数
        self.type_counts[question_data["type"]] += 1

        # --- 更新UI元素 ---
        # 更新章节标题标签
        chapter_title = question_data.get(
            "chapter",
            f"第{self.current_chapter_index + 1}章",  # 从问题数据获取章节名，否则使用默认
        )
        self.chapter_label.config(text=f"{chapter_title}")

        # 更新章节切换按钮的状态
        prev_state = tk.NORMAL if self.current_chapter_index > 0 else tk.DISABLED
        self.prev_chapter_button.set_state(prev_state)

        is_last_chapter = (
            self.current_chapter_index >= len(self.question_bank.chapters) - 1
        )
        next_state = tk.DISABLED if is_last_chapter else tk.NORMAL
        self.next_chapter_button.set_state(next_state)

        # 强制更新界面以确保按钮状态立即生效
        self.root.update_idletasks()

        # --- 显示选中的问题 ---
        self.display_question(question_data)

    def get_multi_answer(self):
        """获取多选题用户选择的答案 (返回排序后的字母字符串, 如 "ACD")"""
        answer = ""
        for i, var in enumerate(self.answer_vars):
            if var.get():  # 如果该选项被选中
                answer += chr(65 + i)  # 将索引转换为大写字母 (0->A, 1->B, ...)
        return "".join(sorted(answer))  # 返回排序后的答案字符串

    def next_question(self):
        """处理“下一题”按钮点击：检查当前答案（如果已选），然后显示新题目"""
        if not self.current_question:
            # 一般不会发生，但作为安全检查
            self.show_chapter_question()
            return

        # 检查用户是否已作答
        answered = False
        user_answer = ""
        q_type = self.current_question["type"]

        if q_type in ["判断题", "单选题"]:
            user_answer = self.answer_var.get()  # 获取单选变量的值
            answered = bool(user_answer)  # 如果有值则认为已作答
        elif q_type == "多选题":
            user_answer = self.get_multi_answer()  # 获取多选答案
            answered = bool(user_answer)  # 如果选择了至少一个选项则认为已作答

        # 记录当前章节索引，因为 show_chapter_question 可能会改变它
        completed_chapter_index = self.current_chapter_index

        # 如果已作答，则检查答案并显示结果
        if answered:
            correct_answer = self.current_question.get("answer", "")  # 获取正确答案
            # 多选题答案需要排序后比较
            if q_type == "多选题":
                correct_answer = "".join(sorted(correct_answer.upper()))
            is_correct = user_answer == correct_answer

            # 更新统计数据
            self.update_stats(is_correct)

            # 显示结果反馈 (使用自定义对话框)
            result_title = "回答正确！" if is_correct else "回答错误！"
            # 格式化答案显示
            display_user_answer = user_answer
            display_correct_answer = correct_answer
            if q_type == "判断题":
                display_user_answer = "对 (A)" if user_answer == "A" else "错 (B)"
                display_correct_answer = "对 (A)" if correct_answer == "A" else "错 (B)"

            result_message = (
                f"你的答案: {display_user_answer}\n正确答案: {display_correct_answer}"
            )

            if is_correct:
                # 正确时显示简单提示
                dialog = CustomDialog(
                    self.root,
                    title=result_title,
                    message="太棒了，回答正确！",
                    yes_text="下一题",
                    show_no=False,  # 只显示一个按钮
                )
            else:
                # 错误时显示正确答案
                dialog = CustomDialog(
                    self.root,
                    title=result_title,
                    message=result_message,
                    yes_text="下一题",
                    show_no=False,  # 只显示一个按钮
                )

            # 对话框关闭后，准备加载下一题
            # 在加载下一题之前，增加上一题所在章节的计数
            self.answered_counts[completed_chapter_index] = (
                self.answered_counts.get(completed_chapter_index, 0) + 1
            )
            self.show_chapter_question()

        else:
            # 如果未作答，直接显示下一题 (允许跳过)
            # 跳过题目也算完成，增加计数
            self.answered_counts[completed_chapter_index] = (
                self.answered_counts.get(completed_chapter_index, 0) + 1
            )
            self.show_chapter_question()

    def next_chapter(self):
        """切换到下一章"""
        if self.current_chapter_index < len(self.question_bank.chapters) - 1:
            self.current_chapter_index += 1
            # 重置章节内状态
            self.type_counts = {"判断题": 0, "单选题": 0, "多选题": 0}
            # 重置新章节的已答计数 (优化点)
            self.answered_counts[self.current_chapter_index] = 0
            self.show_chapter_question()  # 显示新章节的第一题

    def prev_chapter(self):
        """切换到上一章"""
        if self.current_chapter_index > 0:
            self.current_chapter_index -= 1
            # 重置章节内状态
            self.type_counts = {"判断题": 0, "单选题": 0, "多选题": 0}
            # 重置新章节的已答计数
            self.answered_counts[self.current_chapter_index] = 0
            # 清除返回到的这一章的已显示题目记录，以便重新开始
            self.shown_questions = {
                (chap_idx, q_idx)
                for chap_idx, q_idx in self.shown_questions
                if chap_idx != self.current_chapter_index
            }
            self.show_chapter_question()  # 显示新章节的第一题

    def display_question(self, question):
        """在UI上显示给定的问题数据 (包含淡入淡出动画)"""
        # 保存当前问题以便动画对比或回退 (暂未使用回退)
        self.last_question = self.current_question

        # 如果动画正在运行，先取消它，避免冲突
        if self.animation_running and self.fade_animation:
            self.root.after_cancel(self.fade_animation)
            self.animation_running = False

        # 执行淡出动画，完成后在回调中更新内容并淡入
        self.fade_out_content(question)

    def fade_out_content(self, new_question, current_alpha=1.0):
        """淡出当前问题内容 (递归调用)"""
        self.animation_running = True
        step = 0.1  # 每次透明度减少量
        delay = 20  # 动画帧之间的延迟 (毫秒)

        if current_alpha > step:
            try:
                new_alpha = current_alpha - step
                # 计算基于透明度的颜色 (与背景色混合)
                new_fg_color = self.get_alpha_color(
                    ModernUI.get_theme_color("text"), new_alpha
                )
                new_option_color = self.get_alpha_color(
                    ModernUI.get_theme_color("text"), new_alpha  # 选项也用基础文本色
                )
                bg_color = ModernUI.get_theme_color("card_bg")  # 卡片背景色

                # 更新问题文本颜色
                self.question_text.configure(fg=new_fg_color)

                # 更新选项标签颜色
                for label in self.choice_option_labels + self.multi_option_labels:
                    label.configure(foreground=new_option_color)
                # 判断题的 Radiobutton 文本颜色 (需要通过样式修改，这里暂不处理)

                # 计划下一次淡出步骤
                self.fade_animation = self.root.after(
                    delay, lambda: self.fade_out_content(new_question, new_alpha)
                )
            except Exception:
                # 如果控件已销毁或发生其他错误，停止动画并直接更新
                self.update_question_content(new_question)
                self.animation_running = False
        else:
            # 淡出完成，更新内容并开始淡入
            self.update_question_content(new_question)
            self.fade_in_content()

    def fade_in_content(self, current_alpha=0.0):
        """淡入新问题内容 (递归调用)"""
        step = 0.1  # 每次透明度增加量
        delay = 20  # 动画帧之间的延迟 (毫秒)

        if current_alpha < 1.0:
            try:
                new_alpha = min(current_alpha + step, 1.0)  # 确保不超过1.0
                # 计算基于透明度的颜色
                new_fg_color = self.get_alpha_color(
                    ModernUI.get_theme_color("text"), new_alpha
                )
                new_option_color = self.get_alpha_color(
                    ModernUI.get_theme_color("text"), new_alpha
                )
                bg_color = ModernUI.get_theme_color("card_bg")

                # 更新问题文本颜色
                self.question_text.configure(fg=new_fg_color)

                # 更新选项标签颜色
                for label in self.choice_option_labels + self.multi_option_labels:
                    label.configure(foreground=new_option_color)
                # 判断题的 Radiobutton 文本颜色 (需要通过样式修改，这里暂不处理)

                # 计划下一次淡入步骤
                self.fade_animation = self.root.after(
                    delay, lambda: self.fade_in_content(new_alpha)
                )
            except Exception:
                # 如果控件已销毁或发生其他错误，停止动画并直接显示最终状态
                self.question_text.configure(fg=ModernUI.get_theme_color("text"))
                for label in self.choice_option_labels + self.multi_option_labels:
                    label.configure(foreground=ModernUI.get_theme_color("text"))
                self.animation_running = False
        else:
            # 淡入完成
            self.animation_running = False
            # 确保最终颜色正确
            self.question_text.configure(fg=ModernUI.get_theme_color("text"))
            for label in self.choice_option_labels + self.multi_option_labels:
                label.configure(foreground=ModernUI.get_theme_color("text"))

    def get_alpha_color(self, fg_color_hex, alpha):
        """计算前景在背景上的透明度混合颜色"""
        try:
            bg_color_hex = ModernUI.get_theme_color("card_bg")

            # 解析十六进制颜色 "#RRGGBB"
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip("#")
                return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

            fg_r, fg_g, fg_b = hex_to_rgb(fg_color_hex)
            bg_r, bg_g, bg_b = hex_to_rgb(bg_color_hex)

            # alpha blending: new_color = fg_color * alpha + bg_color * (1 - alpha)
            r = int(fg_r * alpha + bg_r * (1 - alpha))
            g = int(fg_g * alpha + bg_g * (1 - alpha))
            b = int(fg_b * alpha + bg_b * (1 - alpha))

            # 确保颜色值在 0-255 范围内
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

            # 格式化回十六进制 "#RRGGBB"
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            # 发生错误时返回原始前景色
            return fg_color_hex

    def update_question_content(self, new_question):
        """更新UI以显示新问题的内容 (无动画，供动画函数调用)"""
        q_type = new_question["type"]
        q_text = new_question["question"]
        options = new_question.get("options", [])  # 获取选项，可能为空

        # --- 重置UI状态 ---
        # 启用文本控件以便修改
        self.question_text.config(state="normal")
        self.question_text.delete(1.0, tk.END)  # 清空旧内容

        # 重置答案变量
        self.answer_var.set("")  # 清空单选/判断题变量
        for var in self.answer_vars:  # 清空多选题变量
            var.set(False)

        # --- 根据题目类型配置UI ---
        self.question_type_label.config(text=f"【{q_type}】")  # 更新题型标签
        self.question_text.insert(tk.END, q_text)  # 插入新题干

        # 隐藏所有选项框架
        self.judge_frame.pack_forget()
        self.choice_frame.pack_forget()
        self.multi_frame.pack_forget()

        # 根据题型显示对应的选项框架并更新内容
        if q_type == "判断题":
            self.judge_frame.pack(fill=tk.X, pady=5, padx=10)  # 显示判断题框架
        elif q_type == "单选题":
            self.choice_frame.pack(fill=tk.X, pady=5)  # 显示单选题框架
            # 更新选项标签文本
            for i, label in enumerate(self.choice_option_labels):
                if i < len(options):
                    label.config(text=options[i])
                else:
                    label.config(text="")  # 清空多余的标签 (虽然一般是4个)
        elif q_type == "多选题":
            self.multi_frame.pack(fill=tk.X, pady=5)  # 显示多选题框架
            # 更新选项标签文本
            for i, label in enumerate(self.multi_option_labels):
                if i < len(options):
                    label.config(text=options[i])
                else:
                    label.config(text="")  # 清空多余的标签

        # 禁用文本控件，使其不可编辑
        self.question_text.config(state="disabled")
        # 将文本滚动到顶部
        self.question_text.yview_moveto(0)

        # 更新进度条
        if self.current_chapter_index < len(self.question_bank.chapters):
            current_chapter_questions = self.question_bank.chapters[
                self.current_chapter_index
            ]
            total_questions_in_chapter = len(current_chapter_questions)
            # 使用优化后的计数器获取本章已回答的问题数量 (优化点)
            answered_in_chapter = self.answered_counts.get(
                self.current_chapter_index, 0
            )

            if total_questions_in_chapter > 0:
                # 确保 answered_in_chapter 不超过 total_questions_in_chapter
                # (理论上不会，但作为安全检查)
                answered_in_chapter = min(
                    answered_in_chapter, total_questions_in_chapter
                )
                progress_value = (
                    answered_in_chapter * 100
                ) / total_questions_in_chapter
                self.progress.configure(value=progress_value)
                # 更新进度标签文本
                self.progress_label.config(
                    text=f"已答: {answered_in_chapter} / 总数: {total_questions_in_chapter}"
                )
            else:
                self.progress.configure(value=0)  # 空章节进度为0
                # 更新进度标签文本
                self.progress_label.config(text="已答: 0 / 总数: 0")

    def show_stats(self):
        """显示答题统计信息窗口"""
        # 创建统计信息窗口 (Toplevel)
        stats_window = tk.Toplevel(self.root)
        stats_window.title("答题情况统计")
        stats_window.geometry("700x550")  # 初始大小
        # 使用主题背景色
        stats_window.configure(bg=ModernUI.get_theme_color("bg"))
        stats_window.minsize(600, 400)  # 最小尺寸

        # --- 标题栏 ---
        # 应用 Title.TFrame 样式
        title_bar = ttk.Frame(stats_window, style="Title.TFrame", padding="0 5")
        title_bar.pack(fill=tk.X)

        # 应用 Title.TLabel 样式
        ttk.Label(
            title_bar,
            text="答题统计情况",
            style="Title.TLabel",
            padding=8,
        ).pack()

        # --- 主框架 (包含滚动条和内容) ---
        # 使用基础 TFrame 样式
        main_scroll_frame = ttk.Frame(stats_window, style="TFrame")
        main_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建 Canvas 用于滚动
        # Canvas 背景设为窗口背景色
        canvas = tk.Canvas(
            main_scroll_frame,
            bg=ModernUI.get_theme_color("bg"),
            bd=0,
            highlightthickness=0,
        )
        # 创建垂直滚动条
        scrollbar = ttk.Scrollbar(
            main_scroll_frame,
            orient="vertical",
            command=canvas.yview,
            style="Vertical.TScrollbar",  # 应用滚动条样式
        )
        # 创建真正的内容框架，放置在 Canvas 中
        # 内容框架背景也设为窗口背景色
        content_frame = ttk.Frame(canvas, style="TFrame", padding="15 15")

        # 关联 Canvas 和滚动条
        canvas.configure(yscrollcommand=scrollbar.set)
        # 将内容框架放入 Canvas
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")

        # --- 滚动逻辑 ---
        # 当内容框架大小改变时，更新 Canvas 的滚动区域
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 确保内容框架宽度不超过 Canvas 宽度，避免水平滚动条
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        # 当 Canvas 大小改变时，更新内容框架的宽度
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        content_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮绑定 (跨平台)
        def on_mousewheel(event):
            delta = 0
            if event.num == 4:
                delta = -1  # Linux 上滚
            elif event.num == 5:
                delta = 1  # Linux 下滚
            elif event.delta > 0:
                delta = -1  # Windows/macOS 上滚
            elif event.delta < 0:
                delta = 1  # Windows/macOS 下滚
            if delta != 0:
                canvas.yview_scroll(delta, "units")

        # 将滚轮事件绑定到 Canvas, 内容框架, 和窗口本身，确保滚动有效
        for widget in (canvas, content_frame, stats_window):
            widget.bind("<MouseWheel>", on_mousewheel)  # Windows/macOS
            widget.bind("<Button-4>", on_mousewheel)  # Linux 上滚
            widget.bind("<Button-5>", on_mousewheel)  # Linux 下滚

        # --- 统计内容填充 ---
        total_answered = 0
        total_correct = 0
        total_wrong = 0
        total_time = datetime.now().strftime("%Y-%m-%d %H:%M")  # 当前时间

        # 题库信息和统计时间
        # 使用基础 TFrame 背景
        ttk.Label(
            content_frame,
            text=f"题库: {self.question_bank.title if self.question_bank else 'N/A'}",
            style="TLabel",  # 使用基础标签样式
            font=("微软雅黑", 11, "bold"),  # 字体加粗
        ).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(
            content_frame,
            text=f"统计时间: {total_time}",
            style="TLabel",  # 使用基础标签样式
            font=("微软雅黑", 9),
            foreground=ModernUI.get_theme_color("text_secondary"),  # 次要文本色
        ).pack(anchor=tk.W, pady=(0, 15))

        # --- 分章节统计 ---
        num_chapters = len(self.question_bank.chapters) if self.question_bank else 0
        if num_chapters == 0:
            ttk.Label(
                content_frame,
                text="没有可统计的数据。",
                style="TLabel",
                font=("微软雅黑", 11),
            ).pack(pady=20)

        for chapter_index in range(num_chapters):
            chapter_stats = self.stats.get(
                chapter_index, {}
            )  # 获取本章统计，默认为空字典
            chapter_data = self.question_bank.chapters[chapter_index]
            # 获取章节标题
            chapter_title = (
                chapter_data[0].get("chapter", f"第{chapter_index + 1}章")
                if chapter_data  # 如果章节非空，从第一个问题获取标题
                else f"第{chapter_index + 1}章"  # 空章节使用默认标题
            )

            # --- 每章一个卡片面板 ---
            # 应用 Card.TFrame 样式 (自带背景色和边框)
            chapter_panel = ttk.Frame(
                content_frame, style="Card.TFrame", padding="15 10"
            )
            chapter_panel.pack(fill=tk.X, pady=8)

            # 章节标题标签
            # 应用 StatsHeader 样式，背景色由 Card.TFrame 继承
            ttk.Label(
                chapter_panel,
                text=chapter_title,
                style="StatsHeader.TLabel",
                # background 不再需要硬编码为 "white"
            ).pack(anchor=tk.W, pady=(0, 10))

            # --- 统计表格 (Grid布局) ---
            # 表格框架也使用 Card.TFrame 样式继承背景色
            stats_grid = ttk.Frame(
                chapter_panel,
                style="Card.TFrame",
                padding=(3, 3, 3, 3),
            )
            stats_grid.pack(fill=tk.X)
            # 配置列权重，使列宽分布合理
            stats_grid.columnconfigure(0, weight=3, uniform="stats_col")  # 题型 (较宽)
            stats_grid.columnconfigure(1, weight=1, uniform="stats_col")  # 已答
            stats_grid.columnconfigure(2, weight=1, uniform="stats_col")  # 正确
            stats_grid.columnconfigure(3, weight=1, uniform="stats_col")  # 错误
            stats_grid.columnconfigure(
                4, weight=2, uniform="stats_col"
            )  # 正确率 (稍宽)

            # 表头行
            headers = ["题型", "已答", "正确", "错误", "正确率"]
            for col, header in enumerate(headers):
                hdr_label = ttk.Label(
                    stats_grid,
                    text=header,
                    font=("微软雅黑", 9, "bold"),
                    style="StatsHeader.TLabel",  # 使用表头样式
                    # background 不再需要硬编码
                    anchor=("w" if col == 0 else "center"),  # 题型左对齐，其他居中
                    padding=(5 if col == 0 else 0, 2),  # 第一列左内边距
                )
                hdr_label.grid(row=0, column=col, sticky="ew", pady=(0, 5))

            # 数据行
            row_num = 1
            has_data_in_chapter = False  # 标记本章是否有数据
            for q_type in ["判断题", "单选题", "多选题"]:
                type_stats = chapter_stats.get(q_type, {"answered": 0, "correct": 0})
                answered = type_stats["answered"]
                correct = type_stats["correct"]

                if answered > 0:  # 只显示有答题记录的行
                    has_data_in_chapter = True
                    wrong = answered - correct
                    rate = f"{correct / answered * 100:.1f}%"  # 计算正确率

                    # 题型列 (左对齐)
                    ttk.Label(
                        stats_grid,
                        text=q_type,
                        style="StatsValue.TLabel",  # 使用数值样式
                        # background 不再需要硬编码
                        anchor="w",
                        padding=(5, 1),
                    ).grid(row=row_num, column=0, sticky="ew")

                    # 已答列 (居中)
                    ttk.Label(
                        stats_grid,
                        text=str(answered),
                        style="StatsValue.TLabel",
                        # background 不再需要硬编码
                        anchor="center",
                    ).grid(row=row_num, column=1, sticky="ew")
                    # 正确列 (居中，使用正确颜色样式)
                    ttk.Label(
                        stats_grid,
                        text=str(correct),
                        style="StatsCorrect.TLabel",  # 应用正确数样式
                        # background 不再需要硬编码
                        anchor="center",
                    ).grid(row=row_num, column=2, sticky="ew")
                    # 错误列 (居中，使用错误颜色样式)
                    ttk.Label(
                        stats_grid,
                        text=str(wrong),
                        style="StatsWrong.TLabel",  # 应用错误数样式
                        # background 不再需要硬编码
                        anchor="center",
                    ).grid(row=row_num, column=3, sticky="ew")
                    # 正确率列 (居中，使用正确率颜色样式)
                    ttk.Label(
                        stats_grid,
                        text=rate,
                        style="StatsRate.TLabel",  # 应用正确率样式
                        # background 不再需要硬编码
                        anchor="center",
                    ).grid(row=row_num, column=4, sticky="ew")
                    row_num += 1

                    # 累加总计 (仅当该行显示时)
                    total_answered += answered
                    total_correct += correct
                    total_wrong += wrong

            # 如果本章没有任何答题记录
            if not has_data_in_chapter:
                ttk.Label(
                    stats_grid,
                    text="本章无答题记录",
                    font=("微软雅黑", 9),
                    style="StatsValue.TLabel",  # 使用基础数值样式
                    # background 不再需要硬编码
                    foreground=ModernUI.get_theme_color("text_secondary"),  # 灰色提示
                ).grid(
                    row=1, column=0, columnspan=5, pady=5
                )  # 跨越所有列

        # --- 总结部分 ---
        # 使用 Summary.TFrame 样式 (背景为窗口主背景)
        summary_panel = ttk.Frame(
            content_frame, style="Summary.TFrame", padding="15 15"
        )
        summary_panel.pack(fill=tk.X, pady=(15, 5))

        # 总结标题
        # 使用 Summary.TLabel 样式继承背景和前景
        ttk.Label(
            summary_panel,
            text="总计",
            style="StatsHeader.TLabel",  # 仍然用表头样式，但背景会不同
            font=("微软雅黑", 11, "bold"),  # 确保字体
            background=ModernUI.get_theme_color("bg"),  # 明确指定背景为窗口背景
        ).pack(anchor=tk.W, pady=(0, 10))

        # 总结数据网格
        # 使用 Summary.TFrame 样式继承背景
        summary_grid = ttk.Frame(summary_panel, style="Summary.TFrame")
        summary_grid.pack(fill=tk.X)
        # 配置列权重
        summary_grid.columnconfigure(0, weight=1, uniform="sum_col")
        summary_grid.columnconfigure(1, weight=1, uniform="sum_col")
        summary_grid.columnconfigure(2, weight=1, uniform="sum_col")
        summary_grid.columnconfigure(3, weight=2, uniform="sum_col")  # 正确率稍宽

        # 计算总正确率
        total_rate = (
            f"{total_correct / total_answered * 100:.1f}%"
            if total_answered > 0
            else "N/A"  # 避免除零错误
        )

        # 显示总计数据
        ttk.Label(
            summary_grid, text=f"总答题: {total_answered}", style="Summary.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=2)
        ttk.Label(
            summary_grid,
            text=f"总正确: {total_correct}",
            style="SummaryCorrect.TLabel",  # 使用总结栏的正确样式
            # background 由样式处理
        ).grid(row=0, column=1, sticky="w", padx=2)
        ttk.Label(
            summary_grid,
            text=f"总错误: {total_wrong}",
            style="SummaryWrong.TLabel",  # 使用总结栏的错误样式
            # background 由样式处理
        ).grid(row=0, column=2, sticky="w", padx=2)
        ttk.Label(
            summary_grid,
            text=f"总正确率: {total_rate}",
            style="SummaryRate.TLabel",  # 使用总结栏的正确率样式
            # background 由样式处理
        ).grid(row=0, column=3, sticky="w", padx=2)

        # --- 底部关闭按钮 ---
        # 使用基础 TFrame 样式
        button_frame = ttk.Frame(stats_window, style="TFrame", padding="0 10 10 10")
        button_frame.pack(fill=tk.X)
        button_frame.columnconfigure(0, weight=1)  # 居中按钮

        ok_button = ModernUI.create_rounded_button(
            button_frame,
            text="关闭",
            command=stats_window.destroy,  # 点击关闭窗口
            width=100,
            height=35,
            corner_radius=17,
            # bg=ModernUI.get_theme_color("neutral"), # 由 color_role 决定
            # hover_bg=ModernUI.get_theme_color("neutral_dark"),
            color_role="neutral",  # 指定角色
            fg="white",
        )
        ok_button.grid(row=0, column=0, pady=5)
        # 注意：统计窗口是临时的，其按钮不需要添加到主窗口的 self.rounded_buttons 列表

        # --- 窗口最终设置 ---
        stats_window.update_idletasks()  # 确保所有控件尺寸已计算

        # 将窗口居中于父窗口
        parent = self.root
        win_width = stats_window.winfo_width()
        win_height = stats_window.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - win_width) // 2
        y = parent_y + (parent_height - win_height) // 2
        y = max(y, 0)  # 防止窗口顶部超出屏幕
        stats_window.geometry(f"+{x}+{y}")

        # 设置为模态窗口
        stats_window.transient(self.root)  # 依附于主窗口
        stats_window.grab_set()  # 捕获事件
        stats_window.focus_set()  # 设置焦点
        # 绑定 Escape 键关闭窗口
        stats_window.bind("<Escape>", lambda e: stats_window.destroy())
        # 等待窗口关闭 (如果需要阻塞主程序)
        # stats_window.wait_window() # 一般不需要，除非后续代码依赖统计结果

    def update_stats(self, is_correct):
        """更新内部存储的答题统计数据"""
        if not self.current_question:
            return  # 防御性编程

        chapter_idx = self.current_chapter_index
        q_type = self.current_question["type"]

        # 确保章节字典存在
        if chapter_idx not in self.stats:
            self.stats[chapter_idx] = {}

        # 确保题型字典存在
        if q_type not in self.stats[chapter_idx]:
            self.stats[chapter_idx][q_type] = {"answered": 0, "correct": 0}

        # 更新计数
        self.stats[chapter_idx][q_type]["answered"] += 1
        if is_correct:
            self.stats[chapter_idx][q_type]["correct"] += 1

    def update_theme_button_icon(self):
        """更新主题切换按钮的图标"""
        if hasattr(self, "theme_button"):
            # 亮色主题显示月亮🌙，暗色主题显示太阳🔆
            theme_icon = "🌙" if ModernUI.current_theme == "light" else "🔆"
            # 使用 set_text 方法更新 RoundedButton 的文本
            self.theme_button.set_text(theme_icon)


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
