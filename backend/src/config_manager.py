
"""
-----------------------------------------------------------
Smart Student Distribution System (S.S.D.S)
Copyright (C) 2026 Ali Abbas & Ali Alaa. All Rights Reserved.
Proprietary and confidential.
-----------------------------------------------------------
"""

import json
import os
from src.rules import Rules

class ConfigManager:
    """
    مدير الإعدادات (Configuration Manager)
    
    مسؤول عن حفظ واسترجاع إعدادات النظام من ملف JSON.
    الإعدادات تشمل:
    - نسب القبول (Quotas).
    - سعات الأقسام (Department Capacities).
    - حالة تفعيل الأقسام (Active/Inactive).
    """
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """
        تحميل الإعدادات من الملف.
        في حال عدم وجود الملف، يتم إنشاء إعدادات افتراضية.
        """
        if not os.path.exists(self.config_path):
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self):
        """
        الإعدادات الافتراضية للنظام.
        """
        return {
            "quotas": Rules.QUOTAS, # استخدام النسب الموجودة في Rules كافتراضي
            "departments": []       # {name: str, capacity: int, is_active: bool}
        }

    def save_config(self):
        """
        حفظ الإعدادات الحالية إلى الملف.
        """
        try:
            # التأكد من وجود المجلد
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    # ---------------------------------------------------------
    # واجهات التعامل مع البيانات (Getters & Setters)
    # ---------------------------------------------------------

    def get_quotas(self):
        return self.config.get('quotas', Rules.QUOTAS)

    def set_quotas(self, quotas):
        """
        تحديث نسب القبول.
        Ex: {'مركزي': 0.60, ...}
        """
        self.config['quotas'] = quotas
        self.save_config()

    def get_departments(self):
        return self.config.get('departments', [])

    def update_departments(self, departments_list):
        """
        تحديث قائمة الأقسام وسعاتها.
        departments_list: List of dicts [{'name': 'SE', 'capacity': 100, 'is_active': True}, ...]
        """
        self.config['departments'] = departments_list
        self.save_config()

    def get_manual_capacities_dict(self):
        """
        استخراج قاموس السعات فقط للأقسام المفعلة لاستخدامه في التوزيع.
        Returns: {DeptName: Capacity}
        """
        depts = self.get_departments()
        cap_dict = {}
        for d in depts:
            # إذا كان القسم مفعلاً، نأخذ سعته
            if d.get('is_active', True):
                cap_dict[d['name']] = int(d.get('capacity', 0))
        return cap_dict

    def get_total_capacity(self):
        return self.config.get('total_capacity', 0)

    def set_total_capacity(self, capacity):
        self.config['total_capacity'] = int(capacity)
        self.save_config()

    def get_manual_mode(self):
        return self.config.get('manual_mode', False)

    def set_manual_mode(self, is_manual):
        self.config['manual_mode'] = bool(is_manual)
        self.save_config()
