# จุดประสงค์ของเว็บไซต์ / Product purpose

## ภาษาไทย

### เว็บนี้มีไว้เพื่ออะไร?

**Log Management Demo** เป็นระบบรวมศูนย์สำหรับรับ–จัดเก็บ–ค้นหา–แสดงผล–แจ้งเตือน **บันทึกเหตุการณ์ด้านความปลอดภัย (security logs)** จากหลายแหล่ง

ในองค์กรจริง ข้อมูลมักกระจัดกระจาย เช่น

- Firewall / Network (Syslog)
- แอปพลิเคชัน (HTTP API)
- Endpoint (เช่น CrowdStrike)
- Cloud (AWS CloudTrail)
- Microsoft 365 / Active Directory

ระบบนี้จำลองการทำงานของ **แผงควบคุมฝ่ายปฏิบัติการ (SOC / IT operations console)** ที่ช่วยให้:

1. ยิง log เข้ามาได้หลายรูปแบบ  
2. แปลงให้อยู่ใน **schema กลาง** เดียวกัน  
3. ค้นหาและกรองตามเวลา / tenant / แหล่งที่มา  
4. ดูสรุปบน Dashboard  
5. ได้การแจ้งเตือนเมื่อมีพฤติกรรมผิดปกติเบื้องต้น (เช่น login ล้มเหลวซ้ำจาก IP เดิม)  
6. แยกสิทธิ์ผู้ใช้ (Admin / Viewer) และแยกข้อมูลตาม tenant  

ใช้สำหรับ **เดโมคัดเลือกฝึกงาน Full-Stack** เพื่อแสดงความสามารถครอบคลุม Backend, Frontend, Data pipeline, Security และ Deployment — **ไม่ใช่ SIEM ระดับ production**

---

## English

### Why does this website exist?

This is a **demo Log Management console** for security / IT operations. It ingests heterogeneous logs, normalizes them into one schema, stores them for search, shows a dashboard, and fires a simple alert rule — with multi-tenant RBAC — in both Appliance and SaaS modes.

It exists to demonstrate end-to-end full-stack engineering for an internship selection assignment.
