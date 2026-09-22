# สคริปต์เดโมภาษาไทย (Log Management Demo)

ใช้สำหรับอัด Demo Video / สัมภาษณ์ แนะนำความยาวรวม **15–25 นาที** (ยืดได้ถึง ~30 นาทีตามโจทย์)

**ลิงก์เดโม:** https://logmgr-saas.onrender.com  
**บัญชี:** `admin` / `password` · `viewer` / `password` · `viewer_b` / `password`

> ถ้า Render ตื่นช้า ให้เปิดหน้าเว็บไว้ก่อนเริ่มพูด 30–60 วินาที

---

## 1) เปิดเรื่อง (1–2 นาที)

> สวัสดีครับ/ค่ะ วันนี้จะเดโมระบบ **Log Management Demo** ที่พัฒนาสำหรับโจทย์คัดเลือก Full-Stack Developer Intern  
>  
> ปัญหาที่ระบบนี้แก้คือ องค์กรมี log จากหลายแหล่ง รูปแบบไม่เหมือนกัน ถ้าไม่มีจุดรวมศูนย์ จะค้นหาและสัมพันธ์เหตุการณ์ยาก  
>  
> ระบบนี้รับ log หลายแหล่ง → แปลงเป็น schema กลาง → เก็บค้นหาได้ → แสดง Dashboard → แจ้งเตือน และมี Auth แยกบทบาท Admin/Viewer พร้อมแยก tenant  
>  
> รันได้ 2 โหมด: **Appliance** ด้วย Docker Compose บนเครื่องเดียว และ **SaaS** ที่ deploy บน Render มี HTTPS สาธารณะ

**โชว์:** เปิด GitHub repo สั้นๆ + เปิด URL SaaS

---

## 2) สถาปัตยกรรม (2–3 นาที)

> Tech stack ที่เลือก:  
> - Backend: FastAPI  
> - Frontend: React  
> - Storage: PostgreSQL  
> - Ingest: HTTP JSON + Syslog UDP (บน Appliance) + อัปโหลดไฟล์  
> - Deploy: Docker Compose และ Render (image เดียวรวม UI+API)  
>  
> เหตุผลที่เลือก Postgres แทน OpenSearch คือน้ำหนักเบา เหมาะกับเดโมบนเครื่องเดียว/ฟรีเทียร์ แต่ยังค้นหาและทำ index ได้เพียงพอ

**โชว์ (ถ้ามี):** แผนภาพใน `docs/architecture.md` หรือโครงสร้างโฟลเดอร์ repo

---

## 3) Login + RBAC (3 นาที)

1. เข้าเว็บ → login `admin` / `password`  
2. ชี้ว่าเป็น Admin เห็นได้หลาย tenant  

> ตอนนี้ล็อกอินเป็น Admin สามารถดูข้อมูลทุก tenant และทำ ingest ได้

3. Logout → login `viewer` / `password`  

> Viewer ของ demoA จะเห็นเฉพาะ tenant ของตัวเอง — ไม่เห็นข้อมูล demoB

4. Logout → login `viewer_b` / `password`  

> Viewer ของ demoB เห็นเฉพาะ demoB — นี่คือ multi-tenant แบบ logical isolation

5. กลับมาเป็น `admin` สำหรับขั้นถัดไป

---

## 4) Dashboard (2–3 นาที)

> แท็บ Dashboard แสดงสรุปเหตุการณ์ในช่วงเวลา: จำนวนรวม Timeline Top IP Top User Top Event Type และแยกตาม source  
> สามารถกรองตาม tenant และ source ได้ทันที

**โชว์:** เปลี่ยน filter tenant `demoA` / `demoB` / All แล้วชี้ว่ากราฟเปลี่ยน

---

## 5) Ingest หลายแหล่ง (5–7 นาที)

### 5.1 HTTP JSON

> ต่อไปจะยิง log ผ่าน REST API ตามโจทย์ `POST /ingest`

**ทำ:** แท็บ Ingest → Send JSON (หรือใช้ `samples/post_logs.py`)  
**โชว์:** แท็บ Events มีแถวใหม่

### 5.2 ไฟล์ sample (AWS / M365 / AD / CrowdStrike)

> ไม่บังคับต่อของจริงทุกแหล่ง — โจทย์อนุญาตใช้ sample ได้ ขอแค่มีอย่างน้อย 4 ทางที่ยิงเข้าได้ และ normalize รวมศูนย์

**ทำ:** อัปโหลด `samples/aws_cloudtrail.json`, `m365_audit.json`, `ad_4625.json`, `crowdstrike.json`  
**โชว์:** ใน Events คอลัมน์ source ต่างกัน แต่ฟิลด์สำคัญถูก map เข้า schema กลาง

### 5.3 Syslog (ถ้าเดโม Appliance / มี Docker local)

> บนโหมด Appliance รองรับ Syslog UDP พอร์ต 514

**ทำ:** `.\samples\send_syslog.ps1`  
**โชว์:** เห็น source `firewall` / `network` ใน UI ภายในประมาณ 1 นาที

> บน Render SaaS ไม่เปิดพอร์ต Syslog สาธารณะ — ใช้ HTTP + ไฟล์แทน ซึ่งยังครบเกณฑ์หลายโปรโตคอลเมื่อรวมกับ Appliance

---

## 6) Search / Events (2 นาที)

> แท็บ Events รองรับค้นหาและกรอง เช่น source, tenant, คำค้น user/IP/event type

**โชว์:** พิมพ์ค้นหา IP หรือชื่อ user แล้ว refresh

---

## 7) Alert (3–4 นาที)

> มีกฎอย่างน้อยหนึ่งข้อ: **Failed Login Burst** — ถ้า IP เดิมล็อกอินล้มเหลวเกิน threshold ภายใน 5 นาที จะสร้าง alert

**ทำ:**

```bash
python samples/post_logs.py --base https://logmgr-saas.onrender.com --burst
```

รอสักครู่ หรือเรียก evaluate แล้วเปิดแท็บ **Alerts**

> เห็นหัวข้อประมาณ Failed login burst from 203.0.113.7 — แสดงว่า detection pipeline ทำงานหลัง ingest

---

## 8) Security & Retention (1–2 นาที)

> ความปลอดภัยขั้นต่ำที่ทำแล้ว:  
> - Auth ด้วย JWT  
> - แยกบทบาท Admin/Viewer  
> - แยกข้อมูลตาม tenant  
> - SaaS ใช้ HTTPS  
>  
> Retention: ระบบลบข้อมูลที่เก่ากว่า 7 วันตามที่โจทย์กำหนด

---

## 9) Deployment (2 นาที)

> Appliance: คำสั่งเดียว `docker compose up --build -d` ตามเอกสารใน `docs/deploy/appliance.md`  
> SaaS: deploy ด้วย Render Blueprint จาก `render.yaml` ได้ URL ถาวร แม้ปิดโน้ตบุ๊ก

**โชว์:** เปิด https://logmgr-saas.onrender.com ย้ำว่าเป็น HTTPS สาธารณะ

---

## 10) ปิดท้าย (1 นาที)

> สรุปสิ่งที่ส่งมอบ:  
> 1) ระบบครบ ingest → normalize → search → dashboard → alert  
> 2) เอกสารสถาปัตยกรรมและวิธีติดตั้ง  
> 3) samples / tests / Postman  
> 4) GitHub + URL SaaS  
>  
> ข้อจำกัดที่รู้ตัว: multi-tenant ยังเป็นแบบแถวในตาราง ไม่ได้แยก index จริง และแผนฟรีของ Render อาจ sleep หลังไม่ใช้งาน  
>  
> พร้อมรับคำถามครับ/ค่ะ

---

## Checklist ก่อนอัด

- [ ] เปิด SaaS ไว้ให้ตื่นแล้ว  
- [ ] Login admin ผ่าน  
- [ ] มี events ในระบบพอให้ Dashboard ไม่ว่าง  
- [ ] ซ้อมคำสั่ง `--burst` ให้ Alert ขึ้นได้  
- [ ] เตรียม GitHub เปิดค้างไว้โชว์โครงสร้างโฟลเดอร์  
- [ ] อ่าน `docs/PURPOSE.md` และ `docs/TESTING.md` ทบทวน 5 นาที
