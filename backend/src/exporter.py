
"""
-----------------------------------------------------------
Smart Student Distribution System (S.S.D.S)
Copyright (C) 2026 Ali Abbas & Ali Alaa. All Rights Reserved.
Proprietary and confidential.
-----------------------------------------------------------
"""

import pandas as pd
import io

class Exporter:
    """
    كلاس التصدير (Exporter Class)
    
    مسؤول عن إنشاء ملف الإكسل النهائي بتنسيق احترافي.
    المميزات:
    - دعم الكتابة من اليمين لليسار (RTL).
    - تنسيق الترويسة (Header Styling).
    - ضبط عرض الأعمدة تلقائياً (Auto-fit Columns).
    - تمييز الطلاب غير المقبولين باللون الأحمر (Conditional Formatting).
    """

    @staticmethod
    def export_to_buffer(original_df, results_map):
        """
        تصدير البيانات إلى ذاكرة (Buffer) بتنسيق إكسل متقدم.
        
        Args:
            original_df (DataFrame): البيانات الأصلية.
            results_map (dict): نتائج التوزيع {id: assigned_dept}.
            
        Returns:
            BytesIO: ملف الإكسل كـ Binary Stream.
        """
        # 1. دمج النتائج مع البيانات الأصلية
        output_df = original_df.copy()
        output_df['القسم المقبول'] = output_df['ت'].map(results_map)
        output_df['القسم المقبول'] = output_df['القسم المقبول'].fillna('غير مقبول')

        # 2. إعداد ملف الإكسل في الذاكرة
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # تحويل الـ DataFrame إلى Sheet
        sheet_name = 'توزيع الطلبة'
        output_df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        # 3. الحصول على كائنات (Workbook & Worksheet) للتنسيق
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # 4. إعداد التنسيقات (Formats)
        
        # تنسيق عام: اتجاه النص من اليمين لليسار
        worksheet.right_to_left() 
        
        # تنسيق الترويسة (Header Format)
        header_fmt = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#4F81BD', # أزرق احترافي
            'font_color': '#FFFFFF', # نص أبيض
            'border': 1
        })
        
        # تنسيق الخلايا العادية (Center Alignment)
        cell_fmt = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1
        })
        
        # تنسيق التحذير (للطلاب غير المقبولين)
        warning_fmt = workbook.add_format({
            'bg_color': '#FFC7CE', # أحمر فاتح
            'font_color': '#9C0006' # نص أحمر غامق
        })

        # 5. تطبيق التنسيقات على الأعمدة
        
        # تعيين الترويسة
        for col_num, value in enumerate(output_df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            
        # ضبط عرض الأعمدة (Estimating Width)
        for i, col in enumerate(output_df.columns):
            # حساب أقصى طول للنص في العمود
            column_len = output_df[col].astype(str).str.len().max()
            column_len = max(column_len, len(col)) + 2 # هوامش
            worksheet.set_column(i, i, column_len, cell_fmt)

        # 6. تنسيق شرطي (Conditional Formatting) لتمييز غير المقبولين
        # نفترض أن عمود "القسم المقبول" هو الأخير
        result_col_idx = len(output_df.columns) - 1
        # الحروف المقابلة للعمود (مثلاً A, B, ... Z, AA) - xlsxwriter يتعامل بالـ index
        
        worksheet.conditional_format(1, result_col_idx, len(output_df), result_col_idx, {
            'type': 'text',
            'criteria': 'containing',
            'value': 'غير مقبول',
            'format': warning_fmt
        })

        # 7. إغلاق وحفظ الملف
        writer.close()
        output.seek(0)
        
        return output
