
"""
-----------------------------------------------------------
Smart Student Distribution System (S.S.D.S)
Copyright (C) 2026 Ali Abbas & Ali Alaa. All Rights Reserved.
Proprietary and confidential.
-----------------------------------------------------------
"""

import pandas as pd

class Rules:
    """
    كلاس القواعد (Rules Class)
    
    هذا الكلاس مسؤول عن تعريف الثوابت والقواعد الأساسية التي تحكم عملية التوزيع.
    يحتوي على:
    1. نسب القبول لكل قناة (QUOTAS).
    2. دوال مساعدة لتوحيد أسماء القنوات (Normalization).
    3. منطق استثناء أبناء التدريسيين (Faculty Child Exception).
    """

    # ---------------------------------------------------------
    # نسب القبول (Quota Percentages)
    # ---------------------------------------------------------
    # تحدد هذه القاموس نسبة المقاعد المخصصة لكل فئة.
    # مركزي: القبول العام (60%)
    # ذوي الشهداء: حصة مؤسسة الشهداء (10%)
    # الموازي: التعليم الموازي الخاص (30%)
    QUOTAS = {
        'مركزي': 0.60,       # Central / General Channel
        'ذوي الشهداء': 0.10, # Martyrs Channel
        'الموازي': 0.30      # Parallel / Private Education Channel
    }

    @staticmethod
    def get_normalized_channel(channel_name):
        """
        دالة توحيد أسماء القنوات (Channel Normalization)
        
        الهدف: التأكد من أن أسماء القنوات المدخلة من ملف الإكسل تتطابق مع المفاتيح المعتمدة في النظام.
        
        المدخلات:
            channel_name (str): اسم القناة كما ورد في الملف (مثلاً: "القبول العام", "قناة الشهداء").
            
        المخرجات:
            str: الاسم القياسي للقناة ('مركزي', 'ذوي الشهداء', 'الموازي').
        """
        channel_name = str(channel_name).strip()
        
        # البحث عن كلمات مفتاحية لتحديد القناة
        if 'شهداء' in channel_name:
            return 'ذوي الشهداء'
        elif 'موازي' in channel_name:
            return 'الموازي'
        else:
            # القيمة الافتراضية هي القبول المركزي
            return 'مركزي'

    @staticmethod
    def apply_faculty_child_exception(student, dept_min_scores):
        """
        تطبيق استثناء أبناء التدريسيين (Faculty Child Exception Logic)
        
        القاعدة:
        يحق لابن التدريسي الانتقال إلى قسم أعلى رغبة إذا كان معدله لا يقل عن (الحد الأدنى للقبول المركزي لذلك القسم - 5 درجات).
        هذا الاستثناء يتجاوز شرط السعة الاستيعابية للقسم (Overload).
        
        المدخلات:
            student (Series/Dict): بيانات الطالب (المعدل، الرغبات، هل هو ابن تدريسي).
            dept_min_scores (Dict): قاموس يحتوي على أقل معدل تم قبوله مركزياً في كل قسم {اسم_القسم: أقل_معدل}.
            
        المخرجات:
            str: اسم القسم الجديد الذي يستحق الانتقال إليه، أو None إذا لم ينطبق الشرط.
        """
        # 1. التحقق من صفة الطالب أولاً
        if not student.get('is_faculty_child', False):
            return None

        # 2. جلب رغبات الطالب بالترتيب
        choices = [student.get('choice_1'), student.get('choice_2'), student.get('choice_3')]
        
        # 3. المرور على الرغبات للتحقق من إمكانية الترقية
        for choice in choices:
            # تجاهل الرغبات الفارغة
            if not choice or pd.isna(choice): continue
            
            # جلب أقل معدل تم قبوله في هذا القسم (قناة المركزي)
            min_score = dept_min_scores.get(choice)
            
            if min_score is not None:
                # التحقق من الشرط الرياضي: معدل الطالب >= (أقل معدل - 5)
                if student['average'] >= (min_score - 5):
                    return choice
                    
        return None
