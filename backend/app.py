from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
import io
import json

# استيراد الوحدات الأساسية للنظام
from src.loader import DataLoader
from src.distributor import Distributor
from src.exporter import Exporter
from src.config_manager import ConfigManager # تم إضافة مدير الإعدادات

"""
-----------------------------------------------------------
Main Application Module (app.py)

هذا الملف هو نقطة الدخول (Entry Point) للخادم الخلفي (Backend Server).
يقوم بتهيئة تطبيق Flask وتعريف الـ Routes الخاصة بالواجهة البرمجية (API).
-----------------------------------------------------------
"""

app = Flask(__name__)
# تفعيل CORS للسماح للواجهة الأمامية بالوصول إلى الـ API من نطاق مختلف
CORS(app)

# تحديد مسارات الملفات الافتراضية للتشغيل والتطوير
DATA_PATH = os.path.join(os.getcwd(), 'data', 'input data.xlsx')
CONFIG_PATH = os.path.join(os.getcwd(), 'data', 'config.json')

# تهيئة مدير الإعدادات
config_manager = ConfigManager(CONFIG_PATH)

@app.route('/scan', methods=['POST'])
def scan_file():
    """
    نقطة فحص الملف (/scan)
    
    الهدف: استقبال ملف الإكسل المرفوع من المستخدم، قراءته، واستخراج المعلومات الأساسية منه
    لعرضها في الواجهة الأمامية قبل بدء التوزيع (مثل عدد الطلاب، قائمة الأقسام المتاحة).
    
    Returns:
        JSON: {status, student_count, departments}
    """
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400

        # حفظ الملف مؤقتاً للمعالجة
        temp_path = os.path.join("data", "temp_scan.xlsx")
        # التأكد من وجود المجلد
        os.makedirs("data", exist_ok=True)
        file.save(temp_path)

        # استخدام Loader لقراءة البيانات
        loader = DataLoader(temp_path)
        _, processed_df = loader.load()
        
        # استخراج الأقسام الفريدة من جميع أعمدة الرغبات
        choices = pd.concat([processed_df['choice_1'], processed_df['choice_2'], processed_df['choice_3']]).dropna().unique()
        unique_depts = sorted([d for d in choices if str(d).strip() != ''])
        
        return jsonify({
            "status": "success",
            "student_count": len(processed_df),
            "departments": unique_depts
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/distribute', methods=['POST'])
def distribute():
    """
    نقطة أجراء التوزيع (/distribute)
    
    الهدف: تنفيذ عملية التوزيع الكاملة.
    تستقبل: الملق، وضع التوزيع (EQUAL/MANUAL)، والسعات المحددة.
    تعيد: ملف إكسل يحتوي على النتائج النهائية.
    """
    try:
        # 1. استلام الملف (File Handing)
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400

        # 2. استلام الإعدادات (Request Parameters)
        # الوضع: 'EQUAL' (توزيع متساوي) أو 'MANUAL' (يدوي)
        mode = request.form.get('mode', 'EQUAL')
        
        # المدخلات الإضافية بناءً على الوضع
        total_capacity = request.form.get('total_capacity') # للوضع المتساوي
        
        # في الوضع اليدوي، نفضل استخدام القيم المحفوظة في ConfigManager إذا لم يرسلها المستخدم صراحة
        # ولكن للتكامل، سنفترض أن التوزيع يستخدم الإعدادات المحفوظة إذا كان الوضع MANUAL
        
        capacities_str = request.form.get('capacities')     # للوضع اليدوي (JSON string - اختياري اذا اردنا تجاوز المحفوظ)
        quotas_str = request.form.get('quotas')             # نسب القبول (اختياري)
        
        userInputCapacities = json.loads(capacities_str) if capacities_str else None
        userInputQuotas = json.loads(quotas_str) if quotas_str else None

        # استخدام النسب المحفوظة إذا لم يرسل المستخدم قيماً جديدة
        active_quotas = userInputQuotas if userInputQuotas else config_manager.get_quotas()

        # Normalize Quotas if provided (or strictly check saved ones)
        if active_quotas:
            normalized_quotas = {}
            for k, v in active_quotas.items():
                val = float(v)
                if val > 1.0: val = val / 100.0
                normalized_quotas[k] = val
            active_quotas = normalized_quotas
        
        # تجهيز مدخلات الموزع
        distributor_input = None
        if mode == 'MANUAL':
            # الأولوية: 1. المدخلات المباشرة 2. القيم المحفوظة في الإعدادات
            distributor_input = userInputCapacities if userInputCapacities else config_manager.get_manual_capacities_dict()
        elif mode == 'EQUAL':
            distributor_input = int(total_capacity) if total_capacity else 0

        # 3. تحميل البيانات (Data Loading)
        temp_path = os.path.join("data", "temp_upload.xlsx")
        os.makedirs("data", exist_ok=True)
        file.save(temp_path)

        loader = DataLoader(temp_path)
        original_df, processed_df = loader.load()
        
        # 4. تنفيذ التوزيع (Core Logic Execution)
        # نقوم بإنشاء كائن الموزع وتمرير البيانات ونسب القبول النشطة
        distributor = Distributor(processed_df, {}, active_quotas)
        
        # أولاً: حساب السعات
        distributor.calculate_capacities(mode, distributor_input)
        
        # ثانياً: إجراء التوزيع
        results = distributor.distribute()

        # معالجة تنسيق الأرقام (تقريب المعدل)
        # نحاول تقريب العمود في البيانات الأصلية قبل التصدير
        cols_to_round = [c for c in original_df.columns if 'معدل' in str(c) or 'Average' in str(c)]
        for col in cols_to_round:
            original_df[col] = pd.to_numeric(original_df[col], errors='coerce').fillna(0)
            original_df[col] = original_df[col].apply(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)
        
        # 5. توليد ملف النتائج (Excel Generation)
        # استخدام الكلاس المطور Exporter لإنشاء ملف إكسل منسق احترافياً
        output = Exporter.export_to_buffer(original_df, results)
        
        # تحويل الملف إلى Base64 لإرساله مع الـ JSON
        import base64
        file_b64 = base64.b64encode(output.getvalue()).decode('utf-8')

        # 6. تحضير البيانات للإرجاع (JSON Response)
        # دمج النتائج مع البيانات الأصلية للعرض
        output_df = original_df.copy()
        output_df['القسم المقبول'] = output_df['ت'].map(results)
        output_df['القسم المقبول'] = output_df['القسم المقبول'].fillna('غير مقبول')
        
        # تحويل البيانات إلى قائمة من القواميس
        final_data = output_df.fillna('').to_dict(orient='records')
        
        # 7. إحصائيات سريعة
        assigned_count = len([v for v in results.values() if v])
        total_count = len(processed_df)
        unassigned_count = total_count - assigned_count
        
        return jsonify({
            "status": "success",
            "data": final_data,
            "file_b64": file_b64,
            "file_name": "distribution_result.xlsx",
            "stats": {
                "assigned": assigned_count,
                "unassigned": unassigned_count,
                "total": total_count
            }
        })

    except Exception as e:
        # في حال حدوث أي خطأ غير متوقع، نعيد رسالة خطأ واضحة
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------------------------------------
# نقاط اتصال الإعدادات (Configuration Endpoints)
# ---------------------------------------------------------

@app.route('/config', methods=['GET'])
def get_config():
    """
    استرجاع الإعدادات الحالية.
    """
    try:
        # نقوم بإعادة تحميل أحدث نسخة من الملف للتأكد
        config = config_manager._load_config() 
        return jsonify({"status": "success", "data": config})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/config', methods=['POST'])
def update_config():
    """
    تحديث الإعدادات وحفظها.
    يستقبل JSON: { "quotas": {...}, "departments": [...] }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        if 'quotas' in data:
            config_manager.set_quotas(data['quotas'])
            
        if 'departments' in data:
            config_manager.update_departments(data['departments'])

        if 'total_capacity' in data:
            config_manager.set_total_capacity(data['total_capacity'])

        if 'manual_mode' in data:
            config_manager.set_manual_mode(data['manual_mode'])
            
        return jsonify({"status": "success", "message": "Configuration saved"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # تشغيل الخادم في وضع التطوير
    app.run(debug=True, port=5000)
