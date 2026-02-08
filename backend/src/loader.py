
"""
-----------------------------------------------------------
Smart Student Distribution System (S.S.D.S)
Copyright (C) 2026 Ali Abbas & Ali Alaa. All Rights Reserved.
Proprietary and confidential.
-----------------------------------------------------------
"""

import pandas as pd
import os

class DataLoader:
    """
    كلاس تحميل ومعالجة البيانات (Data Loader Class)
    
    هذا الكلاس مسؤول عن قراءة ملفات الإكسل، تنظيف البيانات، وتجهيزها للمعالجة بواسطة الموزع.
    يقوم بتحويل الأسماء العربية للأعمدة إلى مفاتيح إنجليزية داخلية لسهولة التعامل برمجياً.
    """
    
    # ---------------------------------------------------------
    # خريطة الأعمدة (Column Mapping)
    # ---------------------------------------------------------
    # تستخدم لترجمة عناوين الأعمدة في ملف الإكسل (عربي) إلى متغيرات برمجية (إنجليزي).
    COLUMN_MAP = {
        'ت': 'id',
        'اسم الطالب': 'name',
        'المعدل': 'average',
        'قناة القبول': 'channel',
        'الاختيار الأول': 'choice_1',
        'الاختيار الثاني': 'choice_2',
        'الاختيار الثالث': 'choice_3',
        'ملاحظات': 'notes'
    }

    def __init__(self, file_path):
        """
        تهيئة الكلاس.
        Args:
            file_path (str): المسار الكامل لملف الإكسل المراد معالجته.
        """
        self.file_path = file_path
        self.original_df = None  # نسخة أصلية للحفاظ على البيانات عند التصدير
        self.processed_df = None # نسخة للمعالجة داخل النظام

    def load(self):
        """
        دالة التحميل الرئيسية (Main Load Function)
        
        تقوم بالخطوات التالية:
        1. قراءة ملف الإكسل.
        2. تنظيف أسماء الأعمدة (إزالة المسافات الزائدة).
        3. إنشاء نسخة معالجة (Processed DataFrame).
        4. إعادة تسمية الأعمدة وفقاً للخريطة (COLUMN_MAP).
        5. تنظيف ومعالجة البيانات (تحويل المعدل لأرقام، اكتشاف أبناء الأساتذة).
        
        Returns:
            original_df: البيانات الخام (لاستخدامها لاحقاً في التصدير بنفس التنسيق).
            processed_df: البيانات الجاهزة للتوزيع.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Input file not found: {self.file_path}")

        # 1. قراءة البيانات
        df = pd.read_excel(self.file_path)
        
        # 2. تنظيف ترويسة الأعمدة (Sanitize Headers)
        df.columns = df.columns.str.strip()
        
        # حفظ النسخة الأصلية
        self.original_df = df.copy()

        # 3. إعادة التسمية (Renaming)
        # يتم تغيير الأسماء العربية إلى إنجليزية الداخلية فقط للأعمدة المعروفة
        df = df.rename(columns=self.COLUMN_MAP)

        # 4. المعالجة المسبقة (Preprocessing)
        
        # أ) التأكد من أن حقل المعدل رقمي (Numeric Validation)
        # يتم تحويل القيم غير الرقمية إلى 0 لتجنب الأخطاء الحسابية لاحقاً
        df['average'] = pd.to_numeric(df['average'], errors='coerce').fillna(0)
        
        # ب) تنظيف حقل قناة القبول
        if 'channel' in df.columns:
            df['channel'] = df['channel'].astype(str).str.strip()

        # ج) اكتشاف صفة "ابن تدريسي" (Feature Extraction)
        # المنطق: البحث عن عبارة "أبناء الأساتذة" داخل حقل الملاحظات
        if 'notes' in df.columns:
            df['is_faculty_child'] = df['notes'].astype(str).str.contains("أبناء الأساتذة", na=False)
        else:
            df['is_faculty_child'] = False

        self.processed_df = df
        return self.original_df, self.processed_df

    def get_settings(self):
        """
        استخراج الإعدادات اليدوية (Settings Exploitation)
        
        تحاول هذه الدالة قراءة ورقة عمل باسم 'Settings' من نفس ملف الإكسل (إن وجدت).
        تستخدم عادةً لتحديد السعات (Capacities) لكل قسم يدوياً.
        
        Returns:
            dict: {اسم_القسم: السعة} أو None في حال عدم وجود الورقة.
        """
        try:
            settings_df = pd.read_excel(self.file_path, sheet_name='Settings')
            if 'Dept_Name' in settings_df.columns and 'Capacity' in settings_df.columns:
                 # تحويل الجدول إلى قاموس {Dept: Cap}
                 return dict(zip(settings_df['Dept_Name'], settings_df['Capacity']))
        except:
            return None
        return None
