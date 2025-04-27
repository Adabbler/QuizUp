import tkinter as tk
from tkinter import ttk


class ModernUI:
    """现代UI组件集合"""

    # 定义主题色彩方案
    THEMES = {
        "light": {
            "bg": "#f5f7fa",  # 主背景色
            "card_bg": "#ffffff",  # 卡片背景
            "primary": "#3498db",  # 主色
            "primary_dark": "#2980b9",  # 主色深色 (悬停/激活)
            "secondary": "#9b59b6",  # 次要色
            "secondary_dark": "#8e44ad",  # 次要色深色
            "success": "#2ecc71",  # 成功色
            "success_dark": "#27ae60",  # 成功色深色
            "warning": "#f1c40f",  # 警告色
            "warning_dark": "#f39c12",  # 警告色深色
            "danger": "#e74c3c",  # 危险色
            "danger_dark": "#c0392b",  # 危险色深色
            "neutral": "#95a5a6",  # 中性色 (禁用/次要按钮)
            "neutral_dark": "#7f8c8d",  # 中性色深色
            "text": "#2c3e50",  # 文本色
            "text_secondary": "#7f8c8d",  # 次要文本色 (禁用/提示)
            "shadow": "0 2px 10px rgba(0,0,0,0.1)",  # 阴影效果 (暂未使用)
        },
        "dark": {
            "bg": "#2c3e50",  # 深色主背景
            "card_bg": "#34495e",  # 深色卡片背景
            "primary": "#3498db",  # 主色
            "primary_dark": "#2980b9",  # 主色深色
            "secondary": "#9b59b6",  # 次要色
            "secondary_dark": "#8e44ad",  # 次要色深色
            "success": "#2ecc71",  # 成功色
            "success_dark": "#27ae60",  # 成功色深色
            "warning": "#f1c40f",  # 警告色
            "warning_dark": "#f39c12",  # 警告色深色
            "danger": "#e74c3c",  # 危险色
            "danger_dark": "#c0392b",  # 危险色深色
            "neutral": "#95a5a6",  # 中性色
            "neutral_dark": "#7f8c8d",  # 中性色深色
            "text": "#ecf0f1",  # 深色文本色
            "text_secondary": "#bdc3c7",  # 深色次要文本色
            "shadow": "0 2px 10px rgba(0,0,0,0.3)",  # 深色阴影 (暂未使用)
        },
    }

    # 当前主题
    current_theme = "light"

    @staticmethod
    def get_theme_color(color_name):
        """获取当前主题的指定颜色"""
        return ModernUI.THEMES[ModernUI.current_theme].get(
            color_name, "#000000"
        )  # 默认返回黑色

    @staticmethod
    def switch_theme():
        """切换明暗主题"""
        ModernUI.current_theme = (
            "dark" if ModernUI.current_theme == "light" else "light"
        )
        return ModernUI.current_theme

    @staticmethod
    def apply_theme(root):
        """应用当前主题到根窗口及更新ttk样式"""
        theme = ModernUI.THEMES[ModernUI.current_theme]
        root.configure(bg=theme["bg"])

        # 更新ttk样式
        ModernUI.style_widgets(root)  # 调用样式更新函数

    @staticmethod
    def set_theme(root):
        """设置并应用初始主题"""
        style = ttk.Style()

        # 尝试使用系统主题以获得更好的原生观感
        try:
            style.theme_use("vista")  # Windows
        except tk.TclError:
            try:
                style.theme_use("clam")  # 通用跨平台主题
            except tk.TclError:
                pass  # 使用默认主题

        # 获取当前主题色
        theme = ModernUI.THEMES[ModernUI.current_theme]

        # 配置基础样式
        style.configure("TButton", font=("微软雅黑", 10))
        style.configure("TLabel", font=("微软雅黑", 10))
        style.configure("TFrame", background=theme["bg"])

        # 设置应用根窗口背景色
        root.configure(bg=theme["bg"])

        # 应用详细的控件样式
        ModernUI.style_widgets(root)

    @staticmethod
    def create_rounded_button(
        parent,
        text,
        command,
        width=120,
        height=35,
        corner_radius=10,
        bg=None,  # bg 和 hover_bg 仍然可以用于覆盖默认角色颜色
        fg="white",
        hover_bg=None,
        font=("微软雅黑", 10),
        image=None,
        compound=tk.LEFT,
        padding=5,
        color_role="primary",  # 新增 color_role 参数
    ):
        """创建圆角按钮 (使用自定义Canvas实现)"""
        # 如果未指定 bg/hover_bg，则根据 color_role 从主题获取
        role_bg = ModernUI.get_theme_color(color_role)
        # 尝试获取对应的深色，如果角色名没有 '_dark' 后缀，则添加
        dark_role = color_role if color_role.endswith("_dark") else f"{color_role}_dark"
        # 如果存在深色定义，则使用，否则悬停色与背景色相同
        role_hover_bg = (
            ModernUI.get_theme_color(dark_role)
            if dark_role in ModernUI.THEMES[ModernUI.current_theme]
            else role_bg
        )

        final_bg = bg if bg is not None else role_bg
        final_hover_bg = hover_bg if hover_bg is not None else role_hover_bg

        button = RoundedButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=corner_radius,
            bg=final_bg,
            hover_bg=final_hover_bg,
            fg=fg,
            image=image,
            compound=compound,
            padding=padding,
            color_role=color_role,  # 传递 color_role
        )
        button.itemconfig(button.text, font=font)  # 设置按钮文本字体

        # 添加悬停效果和动画绑定
        button.bind("<Enter>", lambda e: button.hover_animation(True))
        button.bind("<Leave>", lambda e: button.hover_animation(False))

        return button

    @staticmethod
    def toggle_theme(root):
        """切换主题并应用"""
        ModernUI.switch_theme()
        ModernUI.apply_theme(root)

        # 触发自定义事件，通知应用主题已更改 (例如更新非ttk控件)
        root.event_generate("<<ThemeChanged>>")

    @staticmethod
    def style_widgets(root):
        """配置ttk控件样式以匹配当前主题"""
        style = ttk.Style(root)
        # 确保使用一个支持自定义的主题，clam通常是好的选择
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass  # 如果clam不可用，则使用默认主题

        # 获取当前主题色
        theme = ModernUI.THEMES[ModernUI.current_theme]

        # --- 通用样式 ---
        style.configure(
            ".", font=("微软雅黑", 10), background=theme["bg"], foreground=theme["text"]
        )

        # --- Frame ---
        style.configure("TFrame", background=theme["bg"])
        style.configure(
            "Card.TFrame",  # 用于问题卡片、统计卡片等
            background=theme["card_bg"],
            relief="solid",  # 给卡片一个边框
            borderwidth=1,
        )
        style.configure(
            "Title.TFrame", background=theme["primary"]
        )  # 统计窗口标题栏背景
        style.configure("Summary.TFrame", background=theme["bg"])  # 统计窗口总结栏背景

        # --- Label ---
        style.configure("TLabel", background=theme["bg"], foreground=theme["text"])
        style.configure(
            "Header.TLabel",
            font=("微软雅黑", 16, "bold"),
            background=theme["bg"],
            foreground=theme["text"],
        )
        style.configure(
            "Chapter.TLabel",
            font=("微软雅黑", 14, "bold"),
            background=theme["bg"],
            foreground=theme["text"],
        )
        style.configure(
            "QuestionType.TLabel",
            font=("微软雅黑", 12, "bold"),
            background=theme["card_bg"],  # 背景应为卡片背景
            foreground=theme["primary"],
        )
        style.configure(
            "Option.TLabel",
            background=theme["card_bg"],
            foreground=theme["text"],
            anchor="w",
            justify="left",
        )
        # 统计窗口标签样式
        style.configure(
            "StatsHeader.TLabel",
            font=("微软雅黑", 11, "bold"),
            background=theme["card_bg"],  # 章节标题和统计表头背景应为卡片背景
            foreground=theme["text"],
        )
        style.configure(
            "StatsValue.TLabel",
            font=("微软雅黑", 10),
            background=theme["card_bg"],  # 统计数值背景应为卡片背景
            foreground=theme["text"],
        )
        style.configure(
            "StatsCorrect.TLabel",
            background=theme["card_bg"],  # 正确数背景
            foreground=theme["success"],
        )
        style.configure(
            "StatsWrong.TLabel",
            background=theme["card_bg"],  # 错误数背景
            foreground=theme["danger"],
        )
        style.configure(
            "StatsRate.TLabel",
            background=theme["card_bg"],  # 正确率背景
            foreground=theme["secondary"],
        )
        style.configure(
            "Title.TLabel",  # 统计窗口标题栏文字
            background=theme["primary"],
            foreground="white",
            font=("微软雅黑", 14, "bold"),
        )
        style.configure(
            "Summary.TLabel",  # 统计窗口总结栏文字
            background=theme["bg"],  # 总结栏背景应为窗口主背景
            foreground=theme["text"],
        )
        # 为总结栏的特殊颜色标签创建或修改样式
        style.configure(
            "SummaryCorrect.TLabel", background=theme["bg"], foreground=theme["success"]
        )
        style.configure(
            "SummaryWrong.TLabel", background=theme["bg"], foreground=theme["danger"]
        )
        style.configure(
            "SummaryRate.TLabel",
            background=theme["bg"],
            foreground=theme["secondary"],
            font=("微软雅黑", 10, "bold"),  # 保持字体加粗
        )

        # --- Button (主要使用RoundedButton, ttk.Button作为备用) ---
        style.configure(
            "TButton",
            padding=5,
            relief="flat",
            background=theme["primary"],
            foreground="white",
            font=("微软雅黑", 10),  # 确保字体一致
        )
        style.map(
            "TButton",
            background=[
                ("active", theme["primary_dark"]),
                ("disabled", theme["neutral"]),
            ],
            foreground=[("disabled", theme["text_secondary"])],
        )

        # --- Radiobutton & Checkbutton ---
        style.configure(
            "TRadiobutton",
            background=theme["card_bg"],  # 背景设为卡片背景
            foreground=theme["text"],  # 设置文字颜色
            padding=(10, 5),
            font=("微软雅黑", 11),  # 移除 self.option_font 引用，直接使用默认字体
        )
        style.configure(
            "TCheckbutton",
            background=theme["card_bg"],  # 背景设为卡片背景
            foreground=theme["text"],  # 设置文字颜色
            padding=(10, 5),
            font=("微软雅黑", 11),  # 移除 self.option_font 引用，直接使用默认字体
        )
        style.map(
            "TRadiobutton",
            background=[("active", theme["bg"])],  # 悬停时背景变为窗口背景
            foreground=[("active", theme["text"])],  # 悬停时文字颜色
            indicatorcolor=[  # 指示器颜色
                ("selected", theme["primary"]),
                ("!selected", theme["neutral"]),
            ],
        )
        style.map(
            "TCheckbutton",
            background=[("active", theme["bg"])],  # 悬停时背景变为窗口背景
            foreground=[("active", theme["text"])],  # 悬停时文字颜色
            indicatorcolor=[  # 指示器颜色
                ("selected", theme["primary"]),
                ("!selected", theme["neutral"]),
            ],
        )

        # --- Text ---
        style.configure(
            "TText",  # 虽然我们用的是tk.Text，这里配置一下以防万一
            background=theme["card_bg"],
            foreground=theme["text"],  # 添加文字颜色
            borderwidth=0,
            font=("微软雅黑", 13),
            padx=10,
            pady=10,
            relief="flat",
        )

        # --- Scrollbar ---
        style.configure(
            "Vertical.TScrollbar",
            background=theme["neutral"],
            troughcolor=theme["bg"],
            borderwidth=0,
            arrowsize=14,
        )
        style.map("Vertical.TScrollbar", background=[("active", theme["neutral_dark"])])

        # --- Progressbar ---
        style.configure(
            "TProgressbar",
            thickness=8,
            background=theme["primary"],  # 进度条颜色
            troughcolor=theme["bg"],  # 进度条背景槽颜色
            borderwidth=0,
        )


class RoundedButton(tk.Canvas):
    """自定义圆角按钮类"""

    def __init__(
        self,
        parent,
        text,
        command,
        width=100,
        height=30,
        corner_radius=10,
        bg=None,
        fg="white",
        hover_bg=None,
        image=None,
        compound=tk.LEFT,
        padding=5,
        color_role="primary",  # 接收 color_role
        **kwargs,
    ):
        # 使用主题色
        if bg is None:
            bg = ModernUI.get_theme_color("primary")
        if hover_bg is None:
            hover_bg = ModernUI.get_theme_color("primary_dark")

        theme_bg = ModernUI.get_theme_color("bg")  # 获取父容器背景色
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,  # 无边框高亮
            bg=theme_bg,  # Canvas背景设为父容器背景色，避免穿帮
            **kwargs,
        )
        self.command = command
        self.bg = bg  # 正常背景色
        self.hover_bg = hover_bg  # 悬停背景色
        self.fg = fg  # 文字颜色
        self.color_role = color_role  # 存储 color_role
        self.scale_factor = 1.0  # 缩放比例，用于点击动画
        self.is_moved = False  # 跟踪按钮是否因点击动画被移动
        self.original_font = ("微软雅黑", 10)  # 默认字体，将在创建文本时更新
        self.is_pressed = False  # 跟踪按钮是否处于按下状态
        self.is_disabled = False  # 按钮是否禁用

        # 创建阴影效果 (可选，简单的灰色偏移矩形)
        # 注意：这个阴影效果比较简单，可能在不同主题下效果不佳
        self.shadow = self.create_rounded_rect(
            3,  # x偏移
            3,  # y偏移
            width + 1,  # 阴影宽度
            height + 1,  # 阴影高度
            corner_radius,
            fill=ModernUI.get_theme_color("bg"),  # 阴影颜色设为背景色，用stipple模拟
            outline="",
            stipple="gray50",  # 使用灰色点画填充模拟半透明阴影
        )

        # 创建圆角矩形主体
        self.rect = self.create_rounded_rect(
            1,
            1,
            width - 1,
            height - 1,
            corner_radius,
            fill=bg,
            outline=bg,  # outline设为bg避免边框
        )

        # 处理图像
        self.image_obj = None
        if image:
            self.image_obj = image
            # 根据compound参数决定图片位置
            img_x = padding + image.width() / 2 if compound == tk.LEFT else width / 2
            img_y = height / 2
            self.image = self.create_image(img_x, img_y, image=image)

        # 创建文本
        # 根据是否有图片和compound参数决定文本位置
        text_x_offset = 0
        if image and compound == tk.LEFT:
            text_x_offset = (padding + image.width()) / 2
        text_x = (width + text_x_offset) / 2
        self.text = self.create_text(
            text_x, height / 2, text=text, fill=fg, font=("微软雅黑", 10)
        )
        # 保存原始字体设置
        self.original_font = self.itemcget(self.text, "font")

        # 绑定事件
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

        # 初始状态设置
        self.lift(self.rect)  # 确保矩形在阴影之上
        if image:
            self.lift(self.image)  # 确保图片在矩形之上
        self.lift(self.text)  # 确保文本在最上层

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """使用create_polygon绘制圆角矩形"""
        points = [
            x1 + radius,
            y1,  # top left
            x2 - radius,
            y1,  # top right
            x2,
            y1,
            x2,
            y1 + radius,  # top right corner
            x2,
            y2 - radius,
            x2,
            y2,  # bottom right corner
            x2 - radius,
            y2,  # bottom right
            x1 + radius,
            y2,  # bottom left
            x1,
            y2,
            x1,
            y2 - radius,  # bottom left corner
            x1,
            y1 + radius,
            x1,
            y1,  # top left corner
        ]
        # smooth=True 使多边形顶点连接更平滑，模拟圆角
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, e):
        """鼠标进入按钮区域"""
        if not self.is_disabled:
            self.itemconfig(self.rect, fill=self.hover_bg, outline=self.hover_bg)

    def on_leave(self, e):
        """鼠标离开按钮区域"""
        if not self.is_disabled:
            self.itemconfig(self.rect, fill=self.bg, outline=self.bg)
            # 如果之前有点击动画，恢复
            if self.is_moved:
                self.scale_button(1.0)  # 恢复大小和位置

    def on_click(self, e):
        """鼠标左键按下"""
        if not self.is_disabled:
            self.is_pressed = True  # 标记为按下状态
            # 缩小按钮动画
            self.scale_button(0.95)
            # 按下时也使用悬停颜色
            self.itemconfig(self.rect, fill=self.hover_bg, outline=self.hover_bg)

    def on_release(self, e):
        """鼠标左键释放"""
        if not self.is_disabled:
            self.is_pressed = False  # 标记为释放状态

            # 恢复缩放和位置
            self.scale_button(1.0)

            # 检查鼠标释放时是否仍在按钮内
            if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
                # 仍在按钮内，保持悬停颜色
                self.itemconfig(self.rect, fill=self.hover_bg, outline=self.hover_bg)
                # 执行命令
                if self.command:
                    self.command()
            else:
                # 已移出按钮，恢复正常颜色
                self.itemconfig(self.rect, fill=self.bg, outline=self.bg)

    def scale_button(self, scale_factor):
        """缩放按钮大小并模拟按下效果"""
        # 获取当前按钮尺寸
        width = self.winfo_width()
        height = self.winfo_height()

        # 防止尺寸为0导致的缩放问题
        if width <= 1 or height <= 1:
            return

        # 简单的按下效果：向下向右移动1像素
        if scale_factor < 1.0 and not self.is_moved:  # 按下效果，且未移动过
            # 移动所有元素
            self.move(self.rect, 1, 1)
            self.move(self.text, 1, 1)
            if hasattr(self, "image") and self.image:  # 如果有图像元素也移动它
                self.move(self.image, 1, 1)
            self.is_moved = True  # 标记为已移动
        elif scale_factor >= 1.0 and self.is_moved:  # 恢复效果，且已移动过
            # 移回原位
            self.move(self.rect, -1, -1)
            self.move(self.text, -1, -1)
            if hasattr(self, "image") and self.image:  # 如果有图像元素也移动它
                self.move(self.image, -1, -1)
            self.is_moved = False  # 重置移动标记

    def hover_animation(self, enter=True):
        """悬停动画效果 (实际由on_enter/on_leave处理)"""
        if self.is_disabled:
            return
        if enter and not self.is_pressed:  # 鼠标进入且按钮未被按下
            self.itemconfig(self.rect, fill=self.hover_bg, outline=self.hover_bg)
        elif not enter and not self.is_pressed:  # 鼠标离开且按钮未被按下
            self.itemconfig(self.rect, fill=self.bg, outline=self.bg)
            # 确保离开时位置和缩放完全重置
            if self.is_moved:
                self.scale_button(1.0)

    def set_state(self, state):
        """设置按钮状态 (normal 或 disabled)"""
        # 存储原始命令，以便恢复
        if not hasattr(self, "_original_command"):
            self._original_command = self.command

        if state == tk.DISABLED:
            if not self.is_disabled:  # 仅在从未禁用或之前是启用状态时存储原始颜色
                self._original_bg = self.bg
                self._original_fg = self.fg
            self.is_disabled = True
            # 使用主题中的中性色
            disabled_color = ModernUI.get_theme_color("neutral")
            disabled_text = ModernUI.get_theme_color("text_secondary")
            # 存储原始颜色（如果尚未存储）
            if not hasattr(self, "_original_bg"):
                self._original_bg = self.bg
            if not hasattr(self, "_original_fg"):
                self._original_fg = self.fg

            self.itemconfig(self.rect, fill=disabled_color, outline=disabled_color)
            self.itemconfig(self.text, fill=disabled_text)
            # 解绑事件
            self.unbind("<Enter>")
            self.unbind("<Leave>")
            self.unbind("<Button-1>")
            self.unbind("<ButtonRelease-1>")
            self.command = None  # 禁用命令回调
        elif state == tk.NORMAL:
            self.is_disabled = False
            # 恢复颜色时，使用 color_role 从当前主题获取
            role_bg = ModernUI.get_theme_color(self.color_role)
            dark_role = (
                self.color_role
                if self.color_role.endswith("_dark")
                else f"{self.color_role}_dark"
            )
            role_hover_bg = (
                ModernUI.get_theme_color(dark_role)
                if dark_role in ModernUI.THEMES[ModernUI.current_theme]
                else role_bg
            )

            # 如果之前存储了 _original_bg，优先使用它对应的角色颜色？不，应该直接用 color_role
            self.bg = role_bg
            self.hover_bg = role_hover_bg
            # fg 通常是白色，除非特殊指定，这里恢复为原始存储的 fg 或默认白色
            self.fg = getattr(self, "_original_fg", "white")

            self.itemconfig(self.rect, fill=self.bg, outline=self.bg)
            self.itemconfig(self.text, fill=self.fg)
            # 重新绑定事件
            self.bind("<Enter>", self.on_enter)
            self.bind("<Leave>", self.on_leave)
            self.bind("<Button-1>", self.on_click)
            self.bind("<ButtonRelease-1>", self.on_release)
            self.command = self._original_command  # 恢复命令回调

    def set_text(self, text):
        """更新按钮文本"""
        self.itemconfig(self.text, text=text)
