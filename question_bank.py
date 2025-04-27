import os
import re
from tkinter import messagebox


class QuestionBank:
    def __init__(self, file_path=None):
        self.current_chapter = 0
        self.chapters = []
        self.file_path = file_path
        self.title = "题库复习程序"  # 默认标题

        if file_path:
            self.load_question_bank(file_path)

    def load_question_bank(self, file_path):
        """加载指定题库文件"""
        self.file_path = file_path
        self.chapters = []

        if not os.path.exists(file_path):
            messagebox.showerror(
                "错误", f"题库加载失败！请确保'{os.path.basename(file_path)}'文件存在。"
            )
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 获取题库标题（如果文件第一行是标题）
            first_line = content.strip().split("\n")[0]
            if not first_line.startswith(
                "第"
            ):  # 如果第一行不是以"第"开头，则认为是标题
                self.title = first_line
                content = "\n".join(content.strip().split("\n")[1:])  # 移除标题行
            else:
                # 使用文件名作为标题 (去除扩展名)
                self.title = os.path.splitext(os.path.basename(file_path))[0]

            # 分割章节 (使用正则表达式)
            chapter_pattern = r"第[一二三四五六七八九十]+章.*?(?=\n\n第[一二三四五六七八九十]+章|$)"  # 匹配章节标题直到下一个章节标题或文件末尾
            chapters = re.findall(chapter_pattern, content, re.DOTALL)

            for chapter_content in chapters:
                chapter_content = chapter_content.strip()
                if not chapter_content:
                    continue

                chapter_questions = self.parse_chapter(chapter_content)
                if chapter_questions:
                    self.chapters.append(chapter_questions)

            return bool(self.chapters)  # 如果成功加载了章节则返回True

        except Exception as e:
            messagebox.showerror("错误", f"加载题库时出错：{str(e)}")
            return False

        return True  # 理论上不会执行到这里，但保持函数完整性

    def parse_chapter(self, chapter_content):
        """解析章节内容，提取题目"""
        questions = []
        chapter_title = "未知章节"  # 默认章节标题

        try:
            # 获取章节标题 (更健壮的方式)
            title_match = re.match(
                r"^(第[一二三四五六七八九十]+章.*?)\n",
                chapter_content,  # 匹配以"第X章"开头的行
            )
            if title_match:
                chapter_title = title_match.group(1).strip()
            else:
                # 如果没有匹配到标准章节标题，尝试使用第一行作为标题
                first_line = chapter_content.split("\n", 1)[0].strip()
                if first_line:
                    chapter_title = first_line

            # 按题型分段
            # 使用更精确的模式匹配题型标题，允许题型标题后紧跟题目编号
            # 匹配如 "\n一、判断题\n" 或 "\n二、单项选择题\n" 等格式
            sections = re.split(
                r"(\n[一二三四五]、(?:判断题|单项选择题|多项选择题|单选题|多选题)\s*?\n)",
                chapter_content,
            )

            current_type = None
            current_section_content = ""

            # re.split的结果中，第一个元素可能是章节标题和第一个题型之前的内容，需要跳过
            if sections and not re.match(r"\n[一二三四五]、", sections[0]):
                pass  # 跳过章节标题部分

            idx = (
                1  # 从第二个元素开始，因为split结果是 [内容, 分隔符, 内容, 分隔符, ...]
            )
            while idx < len(sections):
                type_header = sections[idx].strip()  # 题型标题 (分隔符)
                section_content = (
                    sections[idx + 1].strip()
                    if idx + 1 < len(sections)
                    else ""  # 题型内容
                )
                idx += 2  # 每次处理一对(分隔符, 内容)

                if not type_header:
                    continue

                # 识别题型
                if "判断题" in type_header:
                    current_type = "判断题"
                elif (
                    "单项选择题" in type_header or "单选题" in type_header
                ):  # 修复：使用 or 和 in
                    current_type = "单选题"
                elif (
                    "多项选择题" in type_header or "多选题" in type_header
                ):  # 修复：使用 or 和 in
                    current_type = "多选题"
                else:
                    current_type = None  # 未知题型，跳过

                if not current_type or not section_content:
                    continue

                # --- 解析判断题 ---
                if current_type == "判断题":
                    # 匹配 "1. 题干 (A)" 或 "1、题干（B）" 等格式
                    judge_pattern = r"(\d+)[．.、]\s*(.*?)\s*[（\(]\s*([AB])\s*[）\)]"  # 匹配 编号.题干(答案)
                    judge_questions = re.findall(judge_pattern, section_content)
                    for _, q, a in judge_questions:
                        q_cleaned = re.sub(
                            r"\s+", " ", q.strip()
                        ).strip()  # 清理题干多余空格
                        if q_cleaned:
                            questions.append(
                                {
                                    "type": "判断题",
                                    "question": q_cleaned,
                                    "answer": a.strip(),
                                    "chapter": chapter_title,  # 添加章节信息
                                }
                            )

                # --- 解析选择题 ---
                elif current_type in ["单选题", "多选题"]:
                    # 按题目编号分割 (更健壮的分割方式)
                    # 匹配 "1." "1、" "1．" 开头的行作为题目开始
                    # 在内容前加换行符是为了确保第一个题目也能被正确分割
                    question_parts = re.split(
                        r"\n(?=\d+[．.、])", "\n" + section_content
                    )

                    for part in question_parts:
                        part = part.strip()
                        if not part:
                            continue

                        # 提取题干 (允许题干跨行)
                        # 匹配 "1. 题干... A. 选项A" 之间的内容
                        # 使用非贪婪匹配(.*?)，直到遇到换行符加A选项标识
                        q_match = re.match(
                            r"(\d+)[．.、]\s*(.*?)(?=\n\s*A[．.、])", part, re.DOTALL
                        )
                        if not q_match:
                            continue  # 如果连题干和A选项都匹配不到，则跳过这个部分

                        question_text_raw = q_match.group(2).strip()

                        # 提取答案并清理题干
                        answer = None
                        # 匹配题干末尾括号内的答案，允许多选答案有逗号或空格
                        answer_match = re.search(
                            r"[（\(]([A-D,，\s]+)[）\)]", question_text_raw
                        )
                        if answer_match:
                            answer_str = answer_match.group(1).strip()
                            # 清理答案字符串中的非字母字符并排序（适用于多选）
                            answer = "".join(
                                sorted(filter(str.isalpha, answer_str.upper()))
                            )
                            # 从题干中移除答案标记，替换为空括号
                            question_text = re.sub(
                                r"[（\(][A-D,，\s]+[）\)]", "（ ）", question_text_raw
                            ).strip()
                        else:
                            question_text = (
                                question_text_raw  # 没有找到答案标记，题干保持原样
                            )

                        # 清理题干中的多余空格和换行符
                        question_text = re.sub(r"\s+", " ", question_text).strip()
                        # 移除题干中空括号内的空格，防止意外换行
                        question_text = question_text.replace("（ ）", "（）")

                        # 提取选项 (允许选项跨行)
                        options = [""] * 4  # 初始化为4个空字符串，代表A,B,C,D
                        # 匹配 "A. 选项内容 \n B. 选项内容" 等格式
                        # 匹配 A/B/C/D 选项标识，选项内容直到下一个选项标识或字符串末尾
                        option_pattern = (
                            r"\n\s*([A-D])[．.、]\s*(.*?)(?=\n\s*[A-D][．.、]|\s*$)"
                        )
                        option_matches = re.findall(option_pattern, part, re.DOTALL)

                        found_options = 0
                        for opt_char, opt_text in option_matches:
                            opt_index = ord(opt_char.upper()) - ord(
                                "A"
                            )  # 计算选项索引 (A=0, B=1, ...)
                            if 0 <= opt_index < 4:
                                # 清理选项文本中的多余空格和换行符
                                cleaned_opt_text = re.sub(
                                    r"\s+", " ", opt_text.strip()
                                ).strip()
                                options[opt_index] = cleaned_opt_text
                                found_options += 1

                        # 只有当题干存在、找到4个选项且答案存在时才添加 (确保题目完整性)
                        # 修正：答案可能不存在于题干中，需要从其他地方获取或允许为空
                        if (
                            question_text and found_options == 4 and all(options)
                        ):  # 确保四个选项都被解析出来
                            # 确保多选题答案已排序
                            if current_type == "多选题" and answer:
                                answer = "".join(sorted(answer))

                            question_data = {
                                "type": current_type,
                                "question": question_text,
                                "options": options,
                                "answer": answer,  # 答案可能为None，如果未在题干中找到
                                "chapter": chapter_title,  # 添加章节信息
                            }
                            questions.append(question_data)

            return questions

        except Exception as e:
            messagebox.showerror("错误", f"解析章节 '{chapter_title}' 时出错：{str(e)}")
            return []  # 返回空列表表示解析失败
