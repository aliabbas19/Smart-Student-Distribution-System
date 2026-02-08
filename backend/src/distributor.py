
"""
-----------------------------------------------------------
Smart Student Distribution System (S.S.D.S)
Copyright (C) 2026 Ali Abbas & Ali Alaa. All Rights Reserved.
Proprietary and confidential.
-----------------------------------------------------------
"""

import math
import pandas as pd
from src.rules import Rules

class Distributor:
    """
    كلاس التوزيع المركزي (Central Distributor Engine)
    
    هذا الكلاس يمثل "العقل" للنظام. هو المسؤول عن اتخاذ قرارات توزيع الطلبة على الأقسام
    بناءً على المعدل، الرغبات، والسعة الاستيعابية المتاحة لكل قناة (مركزي، موازي، شهداء).
    
    الخوارزمية المتبعة:
    1. حساب السعة (Capacity Planning).
    2. تهيئة العدادات (Usage Counters).
    3. ترتيب الطلبة تنازلياً (Priority Queueing based on Score).
    4. التوزيع الأساسي (Main Allocation Loop).
    5. معالجة الاستثناءات (Exception Handling - Faculty Children).
    """

    def __init__(self, processed_df, capacities=None, quotas=None):
        """
        تهيئة الموزع.
        
        Args:
            processed_df (DataFrame): بيانات الطلبة المعالجة.
            capacities (dict, optional): سعات الأقسام المحددة مسبقاً (للوضع اليدوي).
            quotas (dict, optional): نسب القبول لكل قناة (الافتراضي من Rules.QUOTAS).
        """
        self.df = processed_df
        self.capacities = capacities if capacities else {}
        self.quotas = quotas if quotas else Rules.QUOTAS
        
        # متتبعات الاستخدام (Usage Trackers)
        # لتتبع عدد المقاعد المحجوزة في كل قسم لكل قناة لحظياً.
        # {DeptName: {'مركزي': 50, 'موازي': 20, ...}}
        self.dept_channel_usage = {} 
        
        # متتبع أدنى معدل (Minimum Score Tracker)
        # نحتفظ بأقل معدل تم قبوله في القناة المركزية لكل قسم.
        # يستخدم لاحقاً لتطبيق استثناء أبناء الأساتذة (معدل الطالب >= الحد الأدنى - 5).
        self.dept_min_scores = {}

    def calculate_capacities(self, mode='EQUAL', input_value=None):
        """
        حساب السعة الاستيعابية (Capacity Calculation Logic)
        
        يقوم هذا التابع بتحديد عدد المقاعد الكلي لكل قسم بناءً على الوضع المختار:
        
        1. وضع متساوي (EQUAL):
           - يتم تقسيم العدد الكلي للمقاعد (input_value) بالتساوي على جميع الأقسام.
           - يتم توزيع الباقي (Remainder) بالتساوي على أول ن من الأقسام.
           
        2. وضع يدوي (MANUAL):
           - يتم استخدام السعات المدخلة يدوياً لكل قسم من قبل المستخدم.
        
        Args:
            mode (str): 'EQUAL' أو 'MANUAL'.
            input_value (int/dict): إجمالي المقاعد (للـ EQUAL) أو قاموس السعات (للـ MANUAL).
        """
        # 1. تحديد جميع الأقسام الفريدة المذكورة في رغبات الطلبة
        # نستخدم دمج الأعمدة الثلاثة للحصول على قائمة شاملة
        choices = pd.concat([self.df['choice_1'], self.df['choice_2'], self.df['choice_3']]).dropna().unique()
        unique_depts = sorted([d for d in choices if str(d).strip() != ''])
        
        self.capacities = {}
        num_depts = len(unique_depts)
        
        if num_depts == 0:
            return

        # استراتيجية التوزيع اليدوي
        if mode == 'MANUAL' and isinstance(input_value, dict):
            # نستخدم القيم المدخلة، والباقي صفر
            self.capacities = {dept: int(input_value.get(dept, 0)) for dept in unique_depts}
            
        # استراتيجية التوزيع المتساوي
        elif mode == 'EQUAL':
            # إذا لم يحدد المستخدم عدداً، نفترض سعة 100% (مقعد لكل طالب)
            total_capacity = int(input_value) if input_value is not None else len(self.df)
            
            base_cap = total_capacity // num_depts # القسمة الصحيحة
            remainder = total_capacity % num_depts # الباقي
            
            for i, dept in enumerate(unique_depts):
                # توزيع الباقي على أول الأقسام لضمان توزيع كامل العدد
                extra = 1 if i < remainder else 0
                self.capacities[dept] = base_cap + extra
        
        else:
            # الوضع الافتراضي (Fallback)
            # يضع قيمة آمنة (100) لتجنب الأقسام الصفرية
            self.capacities = {dept: 100 for dept in unique_depts}

        # تهئة العدادات بعد تحديد السعة
        # تصفير العدادات لكل قسم وقناة
        for dept in self.capacities:
            self.dept_channel_usage[dept] = {k: 0 for k in self.quotas.keys()}
            self.dept_min_scores[dept] = 100.0 # نبدأ بقيمة عالية للتناقص

    def _check_capacity(self, dept, channel_type):
        """
        التحقق من توفر مقعد شاغر (Slot Availability Check)
        
        تتحقق هذه الدالة مما إذا كان هناك مجال لقبول طالب جديد في قسم معين وقناة معينة.
        
        المنطق:
        - السعة القصوى للقناة = السعة الكلية للقسم * نسبة القناة.
        - القبول المركزي يحصل على "باقي" المقاعد لضمان عدم ضياع الكسور العشرية.
        
        Returns:
            bool: True إذا وجد مقعد شاغر، False إذا امتلأ.
        """
        if dept not in self.capacities: return False
        
        total_cap = self.capacities[dept]
        quota_percent = self.quotas.get(channel_type, 0)
        
        # حساب السعة النظرية لهذه القناة (Floor لتقريب الكسور للأسفل)
        max_seats = math.floor(total_cap * quota_percent)
        
        # التعامل مع الكسور (Remainder Handling)
        # القناة المركزية تأخذ كل ما تبقى من القنوات الأخرى
        # هذا يضمن أن مجموع المقاعد الفرعية = المقاعد الكلية دائماً
        if channel_type == 'مركزي':
            others = 0
            for q_name, q_val in self.quotas.items():
                if q_name != 'مركزي':
                    # جمع سعات القنوات الأخرى
                    others += math.floor(total_cap * q_val)
            # المركزي = الكلي - مجموع الباقين
            max_seats = total_cap - others

        current_usage = self.dept_channel_usage[dept][channel_type]
        
        return current_usage < max_seats

    def distribute(self):
        """
        تنفيذ عملية التوزيع (Execute Distribution Pipeline)
        
        هذه هي الدالة الرئيسية التي تدير العملية كاملة.
        
        Returns:
            dict: {id: AssignedDepartment}
        """
        # 1. الترتيب (Pre-sorting)
        # الفرز حسب المعدل تنازلياً هو جوهر العدالة في النظام.
        self.df = self.df.sort_values(by=['average'], ascending=False)
        
        # --- [Smart Quota Balancing] ---
        # التحقق من وجود طلبة في القنوات المختلفة.
        # إذا كانت قناة معينة خالية تماماً من الطلبة (مثل الموازي)، فلا داعي لحجز مقاعد لها.
        # يتم تحويل حصتها إلى القناة المركزية لتعظيم الاستفادة من المقاعد.
        
        # حساب عدد الطلبة لكل قناة في البيانات الحالية
        channel_counts = self.df['channel'].apply(Rules.get_normalized_channel).value_counts()
        
        total_students = len(self.df)
        if total_students > 0:
            # القنوات التي يجب التحقق منها (غير المركزي)
            for ch_name in ['الموازي', 'ذوي الشهداء']:
                count = channel_counts.get(ch_name, 0)
                
                # إذا لم يوجد أي طالب في هذه القناة، وكانت لها نسبة محجوزة
                if count == 0 and self.quotas.get(ch_name, 0) > 0:
                    transfer_amount = self.quotas[ch_name]
                    # تصفير حصة القناة الفارغة
                    self.quotas[ch_name] = 0.0
                    # إضافة الحصة إلى المركزي
                    self.quotas['مركزي'] = self.quotas.get('مركزي', 0) + transfer_amount
                    # print(f"Smart Balancing: Transferred {transfer_amount*100}% from {ch_name} to Central due to zero demand.")

        assigned_results = {} # النتائج: {رقم_الطالب: القسم}
        
        # 2. حلقة التوزيع الرئيسية (Main Pass)
        for index, row in self.df.iterrows():
            student_id = row['id']
            # تحديد قناة الطالب (توحيد الاسم)
            channel = Rules.get_normalized_channel(row['channel'])
            
            choices = [row['choice_1'], row['choice_2'], row['choice_3']]
            
            assigned_dept = None
            
            # محاولة تلبية الرغبات بالترتيب
            for choice in choices:
                if not choice or pd.isna(choice): continue
                
                # التحقق من توفر مقعد
                if self._check_capacity(choice, channel):
                    # حجز المقعد
                    self.dept_channel_usage[choice][channel] += 1
                    assigned_dept = choice
                    
                    # تسجيل أدنى معدل (للأغراض الإحصائية + استثناء أبناء الأساتذة)
                    # يتم تحديثه فقط للقناة المركزية لأن الاستثناء يعتمد عليها
                    if channel == 'مركزي':
                        if row['average'] < self.dept_min_scores[choice]:
                            self.dept_min_scores[choice] = row['average']
                    break # تم التوزيع، ننتقل للطالب التالي
            
            assigned_results[student_id] = assigned_dept

        # 3. دورة ملء الشواغر (Vacancies Fill Pass) - [New Logic]
        # في حال بقيت مقاعد شاغرة (لأن طلاب الموازي/الشهداء لم يملؤوا حصتهم)،
        # نقوم بتوزيع الطلاب غير المقبولين على هذه المقاعد المتبقية بغض النظر عن الحصة.
        # هذا يضمن عدم ضياع المقاعد (100% إشغال).
        
        for index, row in self.df.iterrows():
            student_id = row['id']
            # إذا تم قبوله مسبقاً، تجاوز
            if student_id in assigned_results and assigned_results[student_id] is not None:
                continue
                
            channel = Rules.get_normalized_channel(row['channel'])
            choices = [row['choice_1'], row['choice_2'], row['choice_3']]
            
            for choice in choices:
                if not choice or pd.isna(choice): continue
                if choice not in self.capacities: continue
                
                # التحقق من السعة الكلية فقط (Actual Physical Capacity)
                total_limit = self.capacities[choice]
                current_total_usage = sum(self.dept_channel_usage[choice].values())
                
                if current_total_usage < total_limit:
                    # يوجد مقعد شاغر! قم بتعيينه للطالب
                    self.dept_channel_usage[choice][channel] += 1
                    assigned_results[student_id] = choice
                    
                    # تحديث الحد الأدنى للمركزي إذا لزم الأمر
                    if channel == 'مركزي':
                        if row['average'] < self.dept_min_scores[choice]:
                            self.dept_min_scores[choice] = row['average']
                    break

        # 4. حلقة معالجة الاستثناءات (Exception Pass - Faculty Children)
        # نعيد المرور على الطلبة لتطبيق قاعدة "ابن التدريسي".
        # يتم التحقق مما إذا كان الطالب يستحق قسماً أفضل مما حصل عليه (أو إذا لم يقبل أصلاً).
        
        for index, row in self.df.iterrows():
            student_id = row['id']
            
            # التحقق فقط إذا لم يتم قبوله (أو يمكن تحسين منطقه - هنا نركز على غير المقبولين والمقبولين برغبة دنيا)
            # للتبسيط الحالي، الكود الأصلي يتحقق من غير المقبولين، 
            # لكن التحسين المنطقي هو التحقق من "الترقية" (Upgrade) أيضاً.
            # سنستخدم الدالة المساعدة في Rules.
            
            # هل يستحق الترقية؟
            # ملاحظة: هذا الاستثناء يتجاوز السعة (Overload Injection)
            if row['is_faculty_child']:
               better_choice = Rules.apply_faculty_child_exception(row, self.dept_min_scores)
               
               # إذا وجد خيار أفضل مما هو معين له حالياً (بافتراض أن assigned_dept هو None أو رغبة أدنى)
               # هنا، ببساطة إذا وجدنا استحقاقاً سنعتمده فوراً.
               if better_choice:
                   # هل هذا الخيار أفضل من الحالي؟ (تحتاج منطق مقارنة ترتيب الرغبات)
                   # الكود الحالي يفترض التعيين إذا لم يكن معيناً، لنلتزم بالمنطق الأساسي المعدل:
                   current = assigned_results.get(student_id)
                   
                   # إذا لم يكن مقبولاً أو كان مقبولاً في رغبة أدنى (يمكن إضافتها لاحقاً)
                   # حالياً: سنطبق الاستثناء بقوة التجاوز
                   assigned_results[student_id] = better_choice
                   # print(f"Faculty Child Exception Applied: {row['name']} -> {better_choice}")

        return assigned_results
